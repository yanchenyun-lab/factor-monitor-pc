# -*- coding: utf-8 -*-
"""
================================================================================
动态风险预算模型（Dynamic Risk Budget）全量化回测与绩效评估引擎
================================================================================

【模块定位】
针对 dynamic_risk_budget.py 进行历史时序推演、绩效评估与多维度可视化，
支撑前端图表看板展示与后端 API 接口服务。

【核心功能与金融逻辑】
1. 数据库批量预加载与秒级回测：
   - 预先从 MySQL (stock_returns / stock_historical_stage)
     批量提取全量宏观周期状态与资产收益率时序数据，避免按日单步网络往返，实现长周期秒级回测。
2. 动态调仓机制与无未来函数约束（No Look-ahead Bias）：
   - 支持三种调仓模式：
     * "M": 每月最后一个交易日调仓（定期再平衡，换手率低，防漂移）；
     * "stage_change": 仅当宏观周期发生实质性切换时调仓（事件驱动，契合宏观逻辑）；
     * "M_or_stage_change": 月末或宏观周期切换时触发调仓（兼顾宏观响应灵敏度与防长期自然漂移，推荐模式）。
   - 协方差估计仅使用截至调仓日历史窗口内的数据，严格杜绝使用未来数据。
3. 动态模拟资产权重自然漂移与换手摩擦成本扣除：
   - 真实模拟基金账户运行逻辑：未调仓日各资产权重随当日涨跌幅自然漂移；
   - 发生调仓时，精确计算双边换手率 (Turnover) 并扣除交易手续费/滑点成本。
4. 综合计算金融机构级量化绩效指标：
   - 收益维度：累计收益率 (Total Return)、年化复合增长率 (CAGR)、日度胜率 (Win Rate)；
   - 风险维度：年化波动率 (Volatility)、水下动态回撤 (Underwater Drawdown)、最大回撤 (MDD)、下行波动率；
   - 风险调整收益：夏普比率 (Sharpe Ratio)、卡玛比率 (Calmar Ratio)、索提诺比率 (Sortino Ratio)；
   - 相对基准指标：跟踪误差 (Tracking Error)、信息比率 (Information Ratio)、超额年化收益；
   - 交易运营维度：年均双边换手率 (Annual Turnover)、盈亏比 (Profit/Loss Ratio)。
5. 自动输出 4 合 1 高清策略全景图表：
   - 子图1：累计净值走势（策略 vs 等权基准 vs 单资产持有，叠加宏观六周期背景色带）；
   - 子图2：水下动态回撤曲线（Underwater Curve，直观观察风险暴露与恢复周期）；
   - 子图3：历史大类资产动态仓位配置堆叠图（0~100% 仓位演进与资产轮动轨迹）；
   - 子图4：分自然年度收益率对比柱状图（历年盈亏与超额分布）。
"""

import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import requests
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter
from pathlib import Path

# 确保控制台中文输出不乱码
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Matplotlib 中文字体支持，优先使用微软雅黑、黑体等常用中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 将工程根目录添加到 sys.path
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# 导入基础配置与动态风险预算核心算法
try:
    from api.dynamic_risk_budget import (
        CYCLE_MAP,
        DynamicRiskBudgetModel
    )
except ImportError:
    from dynamic_risk_budget import (
        CYCLE_MAP,
        DynamicRiskBudgetModel
    )


class RiskBudgetBacktestEngine:
    """
    动态风险预算策略回测引擎

    【核心职责】
    负责完成数据批量提取、历史调仓日信号生成、滚动协方差矩阵估计、
    SLSQP 非线性约束风险预算求解、资产权重自然漂移推演、
    交易摩擦扣除、多维量化绩效评估以及全景图表绘制。
    """
    def __init__(self,
                 asset_pool: dict,
                 cycle_rb_rules: dict,
                 data_table: str = "stock_returns",
                 start_date: str = "2007-01-01",
                 end_date: str = "2026-08-31",
                 rebalance_freq: str = "M_or_stage_change",
                 custom_bounds: dict = None,
                 history_window: int = 720,
                 transaction_cost: float = 0.0003,
                 rf: float = 0.02,
                 api_base_url: str = None):
        """

        初始化回测引擎并设置核心运行参数

        :param asset_pool: 资产池定义字典。
               格式: {"param1": {"code": "h00852_sh", "name": "中证1000全收益"}, ...}
               - key: 逻辑参数键（param1, param2...），用于内部矩阵对齐；
               - code: 对应数据库表中的行情列名字段（如 h00852_sh）；
               - name: 资产可读中文名称（如 中证1000全收益）。
        :param cycle_rb_rules: 宏观6周期对应的目标风险预算配额（TRC 配比）字典。
               格式: {
                   "阶段1-信用扩张": {"param1": 0.40, "param2": 0.10, ...},
                   "阶段2-经济复苏": {...},
                   ...
               }
        :param data_table: 数据库中存储资产日度收益率的表名 (统一使用纵表 "stock_returns")。
        :param start_date: 回测起始日期，格式 "YYYY-MM-DD"（默认 "2007-01-01"）。
        :param end_date: 回测截止日期，格式 "YYYY-MM-DD"（默认 "2026-08-31"）。
        :param rebalance_freq: 调仓触发模式:
               - "M": 每月最后一个交易日调仓（定期再平衡，换手率最低）；
               - "stage_change": 仅当宏观周期发生实质性切换时调仓（事件驱动）；
               - "M_or_stage_change": 月末或宏观周期切换时均触发调仓（推荐模式，兼顾敏捷响应与控制漂移）。
        :param custom_bounds: 资产权重边界硬约束字典，防止单个资产仓位过重引发非系统性风险。
               格式: {"param1": (0.0, 0.20), "param2": (0.0, 1.0)}
               若未指定则默认在优化时允许 0.0 ~ 1.0 (即 0% ~ 100%)。
        :param history_window: 协方差回溯交易日窗口（默认 720 天，约合 3 个自然年）。
               用于估计资产间的日收益率波动率与相关系数矩阵。
        :param transaction_cost: 单边调仓交易摩擦成本率（默认 0.0003，即万分之三）。
               每次调仓时按: 双边换手率 * transaction_cost 扣除摩擦损耗。
        :param rf: 年化无风险利率（默认 0.02，即 2.0%）。
               用于计算超额收益指标（夏普比率 Sharpe、索提诺比率 Sortino）。
        :param api_base_url: smartIR Java 后端 HTTP 基础地址，默认读取环境变量 SMARTIR_API_BASE 或 http://127.0.0.1:8080。
        """
        # 1. 资产池配置与资产键列表
        self.asset_pool = asset_pool
        self.asset_keys = list(asset_pool.keys())  # 如 ['param1', 'param2', 'param3', 'param4']
        
        # 2. 宏观周期目标风险预算规则
        self.cycle_rb_rules = cycle_rb_rules
        
        # 3. 数据表与回测时间区间
        self.data_table = data_table
        self.start_date = start_date
        self.end_date = end_date
        
        # 4. 调仓规则、约束与回测参数
        self.rebalance_freq = rebalance_freq
        self.custom_bounds = custom_bounds or {}
        self.history_window = history_window
        self.transaction_cost = transaction_cost
        self.rf = rf
        self.api_base_url = api_base_url or os.environ.get("SMARTIR_API_BASE", "http://127.0.0.1:8080")

        # 5. 回测输出结果容器（执行后填充）
        self.full_returns_df = None       # 全量资产收益率 DataFrame (清洗后为真实收益率 r，非 1+r)
        self.full_stage_df = None         # 历史宏观周期 DataFrame (trade_date, stage, cycle_name)
        self.merged_df = None             # 合并后的收益率与周期数据 DataFrame
        self.backtest_results_df = None   # 逐日回测全景结果 DataFrame (包含净值、权重、回撤等)
        self.rebalance_records = []       # 调仓操作历史记录列表 (记录每次调仓日期、周期、换手率、目标权重)
        self.metrics_summary = {}         # 最终量化指标汇总字典 (包含 CAGR、Sharpe、MDD 等格式化指标)

    def load_data_from_api(self):
        """
        通过 smartIR Java 后端提供的 HTTP 接口批量拉取全量行情与宏观阶段数据
        适用于云桌面内网隔离环境中无法直连 MySQL 数据库的场景
        """
        raw_codes = [str(info['code']).strip('`') for info in self.asset_pool.values()]
        url = f"{self.api_base_url.rstrip('/')}/api/returns/risk-data"
        payload = {
            "assetCodes": raw_codes,
            "startDate": self.start_date,
            "endDate": self.end_date
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到 smartIR Java 后端服务 ({url})，请确认 Java 项目 (端口 8080) 已启动或配置 SMARTIR_API_BASE")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求 smartIR Java 后端服务超时 (超过 60s): {url}")
        except Exception as e:
            raise RuntimeError(f"请求 smartIR Java 接口失败: {url}, 错误: {e}")

        data_bundle = res_json.get('data') if isinstance(res_json, dict) and 'data' in res_json else res_json
        if not data_bundle or not isinstance(data_bundle, dict):
            raise ValueError(f"从 Java 接口 {url} 获取数据为空或格式不正确: {res_json}")


        # 1. 解析宏观周期数据
        stages_data = data_bundle.get('stages') or []
        if not stages_data:
            raise ValueError("从 Java 接口未获取到宏观周期 stage 数据")
        df_stage = pd.DataFrame(stages_data)
        trade_date_col = 'tradeDate' if 'tradeDate' in df_stage.columns else 'trade_date'
        df_stage['trade_date'] = df_stage[trade_date_col].astype(str)
        df_stage.set_index('trade_date', inplace=True)
        stage_col = 'stage'
        df_stage['cycle_name'] = df_stage[stage_col].map(lambda s: CYCLE_MAP.get(s, "阶段1-信用扩张"))

        # 2. 解析资产收益率数据
        returns_data = data_bundle.get('returns') or []
        if not returns_data:
            raise ValueError("从 Java 接口未获取到资产收益率 returns 数据")
        df_raw = pd.DataFrame(returns_data)
        ret_date_col = 'tradeDate' if 'tradeDate' in df_raw.columns else 'trade_date'
        ret_code_col = 'assetCode' if 'assetCode' in df_raw.columns else 'asset_code'
        ret_rate_col = 'returnRate' if 'returnRate' in df_raw.columns else 'return_rate'

        df_raw['trade_date'] = df_raw[ret_date_col].astype(str)
        df_returns = df_raw.pivot(index='trade_date', columns=ret_code_col, values=ret_rate_col)

        # 3. 列名标准化重命名 (大小写不敏感映射)
        lower_rename_map = {str(info['code']).lower().strip('`'): key for key, info in self.asset_pool.items()}
        new_columns = []
        for col in df_returns.columns:
            col_clean = str(col).lower().strip('`')
            col_key = lower_rename_map.get(col_clean, col)
            new_columns.append(col_key)
        df_returns.columns = new_columns

        # 4. 数值清洗与真实收益率换算 (减 1.0)
        for col in self.asset_keys:
            if col in df_returns.columns:
                df_returns[col] = pd.to_numeric(df_returns[col], errors='coerce').astype(float) - 1.0

        df_returns.dropna(inplace=True)

        # 5. 合并收益率与宏观周期 (左连接并平滑延展宏观周期)
        merged = df_returns.join(df_stage[['stage', 'cycle_name']], how='left')
        merged['stage'] = merged['stage'].ffill().bfill().astype(int)
        merged['cycle_name'] = merged['stage'].map(lambda s: CYCLE_MAP.get(s, "阶段1-信用扩张"))
        merged.sort_index(inplace=True)

        self.full_returns_df = df_returns
        self.full_stage_df = df_stage
        self.merged_df = merged

        print(f"[数据加载完成 (via Java API)] 总有效交易日: {len(merged)} 天, 时间范围: {merged.index[0]} ~ {merged.index[-1]}")

    def load_data(self):
        """批量预载全量行情与宏观阶段数据 (纯通过 smartIR Java 后端 HTTP 接口，无数据库直连)"""
        self.load_data_from_api()

    def get_rebalance_flags(self, dates: list):
        """
        根据指定频率规则生成调仓日标记布尔序列

        【调仓日判定算法】
        :param dates: 回测日期字符串列表，按升序排列，如 ['2010-01-04', '2010-01-05', ...]
        :return: 布尔列表 is_rebal，长度与 dates 相同，True 代表当天收盘后需要触发调仓

        【三种模式的判定逻辑】
        1. 月末调仓 (is_month_end):
           比较当前交易日与下一个交易日的年月前缀 ('YYYY-MM')。
           若进入了新月份，或者已经到达全序列最后一天，则当前日判定为“月末最后一个交易日”。
        2. 宏观周期切换 (is_stage_changed):
           比较当天宏观阶段代码 stages[i] 与前一日 stages[i-1]。
           若发生变更，则当前日判定为“宏观状态切换日”。
        3. 综合模式 (M_or_stage_change):
           满足月末或宏观切换任意一个条件即标记为 True。
        """
        is_rebal = [False] * len(dates)
        
        # 提取 'YYYY-MM' 字符串前缀，用于识别跨月时点
        periods = [d[:7] for d in dates]
        # 提取每日宏观周期代码 (1~6)
        stages = [self.merged_df.loc[d, 'stage'] for d in dates]

        for i in range(len(dates)):
            flag = False
            # 1. 月末交易日判断：下一交易日跨月，或为整个序列的最后一天
            is_month_end = (i == len(dates) - 1) or (periods[i] != periods[i + 1])
            # 2. 宏观阶段切换判断：首日不计切换，从第 2 天起若周期代码与昨日不同则触发
            is_stage_changed = (i > 0) and (stages[i] != stages[i - 1])

            if self.rebalance_freq == "M":
                # 仅月末调仓
                flag = is_month_end
            elif self.rebalance_freq == "stage_change":
                # 仅宏观周期切换调仓
                flag = is_stage_changed
            elif self.rebalance_freq == "M_or_stage_change":
                # 双触发：月末或宏观周期切换均调仓 (推荐)
                flag = is_month_end or is_stage_changed
            else:
                flag = is_month_end

            is_rebal[i] = flag

        return is_rebal

    def run_backtest(self):
        """
        执行历史逐日全量量化回测模拟

        【回测核心时序流】
        1. 历史数据预热期校验 (History Warm-up Check)：
           由于动态风险预算需要滚动协方差矩阵（默认回溯 720 天），
           因此若 start_date 之前的数据不足 history_window，会自动平移回测起点以确保数学求解的严谨性。
        2. 逐日推演循环：
           - 状态判断：今日是否为调仓日 (is_rebal_day) 或首个回测交易日；
           - 若需调仓：
             a. 提取截至今日的历史收益率切片并计算样本协方差矩阵 Cov；
             b. 提取当前宏观周期对应的风险预算配额向量 Target TRC；
             c. 使用 SLSQP 算法求解满足权重上下界与 100% 满仓约束的最优权重向量 target_w；
             d. 计算双边换手率 turnover = sum(|target_w - current_weights|)；
             e. 扣除换手交易摩擦成本 fee_cost = turnover * transaction_cost；
             f. 更新当前持仓权重为 target_w；
           - 净值演进与自然漂移 (Weight Drift)：
             a. 计算当日策略扣费净收益率 daily_net_ret 与等权基准收益率 daily_eq_ret；
             b. 更新策略累计净值 strat_nav 与等权基准累计净值 eq_nav；
             c. 模拟盘中持仓资产因涨跌幅不同产生的权重自然漂移，计算收盘时刻的真实持仓权重；
           - 记录每日详细指标字典 record。
        3. 整理为 DataFrame 并计算多维金融绩效指标。
        """
        if self.merged_df is None:
            self.load_data()

        df = self.merged_df
        all_dates = list(df.index)

        # ---------------------------------------------------------------------
        # 1. 定位并校准回测起始日期
        # ---------------------------------------------------------------------
        valid_start_dates = [d for d in all_dates if d >= self.start_date]
        if not valid_start_dates:
            raise ValueError(f"回测起始日 {self.start_date} 超出数据范围！")

        start_idx = all_dates.index(valid_start_dates[0])
        # 确保回测起点前具备基础数据用于计算协方差矩阵（至少 60 个交易日）
        min_required = min(60, self.history_window)
        if start_idx < min_required:
            adjusted_idx = min_required
            print(f"[提示] 起始日 {all_dates[start_idx]} 前历史数据不足 {min_required} 天，自动调整起点至: {all_dates[adjusted_idx]}")
            start_idx = adjusted_idx

        # 筛选有效回测交易日序列
        bt_dates = [d for d in all_dates[start_idx:] if d <= self.end_date]
        rebalance_flags = self.get_rebalance_flags(bt_dates)

        n_assets = len(self.asset_keys)
        
        # ---------------------------------------------------------------------
        # 2. 初始化持仓与净值变量
        # ---------------------------------------------------------------------
        # current_weights: 策略当前持仓权重向量（numpy 数组，和为 1.0）
        current_weights = np.ones(n_assets) / n_assets
        # eq_weights: 等权重基准（1/N 持仓）权重向量
        eq_weights = np.ones(n_assets) / n_assets

        records = []               # 逐日收益率与净值明细记录列表
        self.rebalance_records = [] # 调仓事件详情记录列表

        # 累计净值均归一化为 1.0 (基准起点)
        strat_nav = 1.0
        eq_nav = 1.0
        # 各底层大类资产买入持有（Buy-and-Hold）累计净值，用于横向对照
        single_asset_navs = {k: 1.0 for k in self.asset_keys}

        print(f"\n[开始历史时序回测] 调仓机制: {self.rebalance_freq}, 协方差窗口: {self.history_window} 天...")
        t0 = datetime.now()

        # ---------------------------------------------------------------------
        # 3. 逐交易日时序回测循环 (Main Backtest Loop)
        # ---------------------------------------------------------------------
        for t_idx, current_date in enumerate(bt_dates):
            is_rebal_day = rebalance_flags[t_idx]
            # 当日各资产收益率向量 [r_1, r_2, ..., r_n]
            today_ret_series = df.loc[current_date, self.asset_keys].values.astype(float)
            # 当日宏观周期名称 (如 "阶段1-信用扩张")
            today_cycle = df.loc[current_date, 'cycle_name']

            turnover = 0.0  # 当日双边换手率
            fee_cost = 0.0  # 当日调仓摩擦成本

            # -----------------------------------------------------------------
            # 分支 A: 若今日触发调仓 (或为回测第 1 天进行初始建仓)
            # -----------------------------------------------------------------
            if is_rebal_day or t_idx == 0:
                # 1. 提取回溯窗口历史收益率数据 (严格截止到今日，无未来函数)
                global_idx = all_dates.index(current_date)
                window_start_idx = max(0, global_idx - self.history_window + 1)
                hist_returns = df.iloc[window_start_idx : global_idx + 1][self.asset_keys]

                # 2. 提取并对齐当前宏观周期的目标风险预算配额 (TRC 目标)
                rb_target = self.cycle_rb_rules.get(today_cycle, {})
                target_list = []
                for k in self.asset_keys:
                    info = self.asset_pool.get(k, {})
                    val = None
                    # 支持按 key (如 param1)、code (如 h00852_sh) 或 name (如 中证1000) 容错匹配
                    if k in rb_target:
                        val = rb_target[k]
                    elif info.get('code') in rb_target:
                        val = rb_target[info.get('code')]
                    elif info.get('name') in rb_target:
                        val = rb_target[info.get('name')]
                    target_list.append(float(val) if val is not None else (1.0 / n_assets))

                target_budgets = np.array(target_list)
                # 归一化，确保目标风险贡献总和严格等于 1.0
                if np.sum(target_budgets) > 0:
                    target_budgets = target_budgets / np.sum(target_budgets)
                else:
                    target_budgets = np.ones(n_assets) / n_assets

                # 3. 计算样本协方差矩阵 (Covariance Matrix)
                cov_matrix = hist_returns.cov().values
                # 强制对称化，消除浮点数计算导致的极小非对称误差，提高优化器稳定性
                cov_matrix = (cov_matrix + cov_matrix.T) / 2.0

                # 4. 设置优化约束条件与边界
                # 约束：各资产权重之和等于 1.0 (100% 满仓，无杠杆无空头)
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}]
                # 边界：每个资产的持仓权重范围 [min_w, max_w]
                bounds = [self.custom_bounds.get(k, (0.0, 1.0)) for k in self.asset_keys]

                # 5. 调用 SLSQP (Sequential Least Squares Programming) 求解非线性优化
                # 优化目标：最小化各资产实际风险贡献占比 (TRC) 与目标风险预算占比的均方误差
                # 多重优质初始猜测点：当前持仓权重 (热启动) 与逆波动率先验启发式权重
                vols = np.sqrt(np.maximum(np.diag(cov_matrix), 1e-8))
                inv_vol_w = target_budgets / vols
                inv_vol_w = inv_vol_w / np.sum(inv_vol_w)
                for i_b, (lb, ub) in enumerate(bounds):
                    inv_vol_w[i_b] = np.clip(inv_vol_w[i_b], lb, ub)
                inv_vol_w = inv_vol_w / np.sum(inv_vol_w)

                candidates = [current_weights, inv_vol_w]
                best_res = None
                best_fun = float('inf')

                for x0 in candidates:
                    res = minimize(
                        fun=DynamicRiskBudgetModel.risk_budget_objective,
                        x0=x0,
                        args=(cov_matrix, target_budgets),
                        method='SLSQP',
                        bounds=bounds,
                        constraints=constraints,
                        options={'ftol': 1e-12, 'disp': False}
                    )
                    if res.fun < best_fun:
                        best_fun = res.fun
                        best_res = res
                        if best_fun < 1e-8:
                            break

                if best_res is not None and (best_res.success or best_fun < 1e-2):
                    target_w = best_res.x
                else:
                    # 若优化偶发不收敛，维持当前权重，保证系统鲁棒性
                    target_w = current_weights

                # 6. 计算调仓换手率与摩擦成本
                # 双边换手率定义：所有资产权重变动的绝对值之和
                turnover = np.sum(np.abs(target_w - current_weights))
                # 摩擦成本 = 换手率 * 单边手续费/滑点率
                fee_cost = turnover * self.transaction_cost

                # 记录调仓明细日志
                self.rebalance_records.append({
                    "date": current_date,
                    "cycle": today_cycle,
                    "turnover": turnover,
                    "weights": {self.asset_keys[i]: target_w[i] for i in range(n_assets)}
                })

                # 更新当前持仓权重为调仓后的目标权重
                current_weights = target_w.copy()
                
                # 等权重基准调仓：在调仓日重置回 1/N 均匀分布
                if is_rebal_day:
                    eq_weights = np.ones(n_assets) / n_assets

            # -----------------------------------------------------------------
            # 分支 B: 模拟当日收益演进与净值更新
            # -----------------------------------------------------------------
            # 策略当日毛收益率 (扣费前) = 各资产持仓权重 * 当日资产收益率
            daily_gross_ret = np.sum(current_weights * today_ret_series)
            # 策略当日净收益率 (扣除调仓摩擦成本)
            daily_net_ret = daily_gross_ret - fee_cost

            # 等权重基准当日收益率 (基准不考虑微弱手续费)
            daily_eq_ret = np.sum(eq_weights * today_ret_series)

            # 更新策略与基准累计净值 (复利计算)
            strat_nav = strat_nav * (1.0 + daily_net_ret)
            eq_nav = eq_nav * (1.0 + daily_eq_ret)

            # 更新各单一资产买入持有净值
            for i, k in enumerate(self.asset_keys):
                single_asset_navs[k] = single_asset_navs[k] * (1.0 + today_ret_series[i])

            # -----------------------------------------------------------------
            # 分支 C: 资产权重自然漂移 (Weight Drift)
            # -----------------------------------------------------------------
            # 在非调仓日（或调仓完成后的日内运行期间），由于各资产收益率不相同，
            # 涨幅大的资产市值占比被动上升，跌幅大的资产市值占比被动缩小。
            # 收盘时资产 i 的实际持仓权重更新公式为:
            #   w_i(t, close) = [w_i(t) * (1 + r_i(t))] / [1 + R_gross(t)]
            current_weights = (current_weights * (1.0 + today_ret_series)) / (1.0 + daily_gross_ret)
            eq_weights = (eq_weights * (1.0 + today_ret_series)) / (1.0 + daily_eq_ret)

            # -----------------------------------------------------------------
            # 分支 D: 组装当日综合结果记录字典
            # -----------------------------------------------------------------
            record = {
                "trade_date": current_date,      # 交易日期 (YYYY-MM-DD)
                "cycle": today_cycle,            # 当日宏观周期阶段名称 (如 "阶段1-信用扩张")
                "daily_ret": daily_net_ret,      # 策略当日扣费后净收益率
                "daily_eq_ret": daily_eq_ret,    # 等权重基准当日收益率
                "strat_nav": strat_nav,          # 策略当日收盘累计净值 (起点归一为 1.0)
                "eq_nav": eq_nav,                # 等权重基准当日累计净值 (起点归一为 1.0)
                "turnover": turnover,            # 当日调仓双边换手率 (非调仓日为 0.0)
                "fee_cost": fee_cost             # 当日扣除的交易摩擦成本金额率 (非调仓日为 0.0)
            }
            # 记录各单资产在收盘时的漂移后权重、累计持有净值、当日收益率
            for i, k in enumerate(self.asset_keys):
                record[f"w_{k}"] = current_weights[i]       # 资产 k 当日收盘权重 (0.0 ~ 1.0)
                record[f"nav_{k}"] = single_asset_navs[k]   # 资产 k 累计净值
                record[f"ret_{k}"] = today_ret_series[i]   # 资产 k 当日实际涨跌幅

            records.append(record)

        time_elapsed = (datetime.now() - t0).total_seconds()
        print(f"[回测执行完毕] 耗时: {time_elapsed:.2f} 秒, 产生调仓次数: {len(self.rebalance_records)} 次")

        # 整理结果为 DataFrame，以交易日期为索引
        res_df = pd.DataFrame(records)
        res_df.set_index('trade_date', inplace=True)
        self.backtest_results_df = res_df

        # 计算全套金融量化指标
        self.calculate_metrics()
        return self.backtest_results_df

    def calculate_metrics(self):
        """
        计算全套金融机构级量化绩效评估指标

        【涵盖指标维度与数学公式】
        1. 累计收益率 (Total Return): NAV_end - 1.0
        2. 年化复合增长率 (CAGR): (NAV_end) ^ (1 / 年数) - 1.0
           - 年数折算标准：总交易日数 / 252 (金融通用每年交易日标准)。
        3. 年化波动率 (Annualized Volatility): std(daily_ret) * sqrt(252)
        4. 水下动态回撤曲线 (Underwater Drawdown) 与最大回撤 (MDD):
           - drawdown(t) = (NAV(t) - max_{s<=t}(NAV(s))) / max_{s<=t}(NAV(s))
           - max_drawdown = min(drawdown) （通常为负值，表示从历史最高点跌落的最深幅度）。
        5. 夏普比率 (Sharpe Ratio): (CAGR - rf) / 年化波动率
           - 衡量每承担一单位总波动风险所获得的超额回报。
        6. 卡玛比率 (Calmar Ratio): CAGR / |max_drawdown|
           - 衡量年化收益率与历史极端尾部亏损的性价比，卡玛比率越高说明收益承受的极端回撤代价越小。
        7. 索提诺比率 (Sortino Ratio): (CAGR - rf) / 年化下行波动率
           - 与夏普比率不同，索提诺比率只对负收益率（带来亏损的下行波动）进行惩罚，更贴合实际风控感知。
        8. 跟踪误差 (Tracking Error) 与信息比率 (Information Ratio, IR):
           - tracking_error = std(daily_ret - daily_eq_ret) * sqrt(252)
           - info_ratio = (CAGR - eq_CAGR) / tracking_error
           - 衡量主动管理超越基准的稳定性和持久性。
        9. 日度胜率 (Daily Win Rate) 与盈亏比 (Profit/Loss Ratio):
           - win_rate = count(daily_ret > 0) / count(total_days)
           - profit_loss_ratio = mean(正收益日涨幅) / |mean(负收益日跌幅)|
        10. 年均双边换手率 (Annualized Turnover): sum(turnover) / 年数
        """
        df = self.backtest_results_df
        days = len(df)
        years = days / 252.0  # 按中国A股市场惯例，以每年 252 个交易日折算

        daily_ret = df['daily_ret']
        daily_eq_ret = df['daily_eq_ret']

        # ---------------------------------------------------------------------
        # 1. 收益率指标
        # ---------------------------------------------------------------------
        total_return = df['strat_nav'].iloc[-1] - 1.0
        cagr = (df['strat_nav'].iloc[-1]) ** (1.0 / years) - 1.0

        eq_total_return = df['eq_nav'].iloc[-1] - 1.0
        eq_cagr = (df['eq_nav'].iloc[-1]) ** (1.0 / years) - 1.0

        # ---------------------------------------------------------------------
        # 2. 风险指标 (年化波动率)
        # ---------------------------------------------------------------------
        ann_vol = daily_ret.std() * np.sqrt(252)
        eq_ann_vol = daily_eq_ret.std() * np.sqrt(252)

        # ---------------------------------------------------------------------
        # 3. 水下动态回撤与最大回撤 (MDD)
        # ---------------------------------------------------------------------
        # 策略净值累计最高点 (Cummax) 与水下回撤
        cummax = df['strat_nav'].cummax()
        drawdown = (df['strat_nav'] - cummax) / cummax
        df['drawdown'] = drawdown
        max_drawdown = drawdown.min()

        # 等权基准净值累计最高点与水下回撤
        eq_cummax = df['eq_nav'].cummax()
        eq_drawdown = (df['eq_nav'] - eq_cummax) / eq_cummax
        df['eq_drawdown'] = eq_drawdown
        eq_max_drawdown = eq_drawdown.min()

        # 计算各个单一底层资产从买入持有以来的动态回撤
        for k in self.asset_keys:
            k_cummax = df[f"nav_{k}"].cummax()
            df[f"drawdown_{k}"] = (df[f"nav_{k}"] - k_cummax) / k_cummax

        # ---------------------------------------------------------------------
        # 4. 风险调整后收益指标
        # ---------------------------------------------------------------------
        # 夏普比率 (Sharpe Ratio)
        sharpe = (cagr - self.rf) / ann_vol if ann_vol > 0 else 0.0
        eq_sharpe = (eq_cagr - self.rf) / eq_ann_vol if eq_ann_vol > 0 else 0.0

        # 卡玛比率 (Calmar Ratio)
        calmar = cagr / abs(max_drawdown) if abs(max_drawdown) > 0 else 0.0
        eq_calmar = eq_cagr / abs(eq_max_drawdown) if abs(eq_max_drawdown) > 0 else 0.0

        # 索提诺比率 (Sortino Ratio): 仅惩罚日收益为负的下行波动率
        downside_ret = daily_ret[daily_ret < 0]
        downside_std = downside_ret.std() * np.sqrt(252) if len(downside_ret) > 0 else 1e-6
        sortino = (cagr - self.rf) / downside_std

        # 超额收益与信息比率 (Information Ratio, IR)
        excess_daily_ret = daily_ret - daily_eq_ret
        tracking_error = excess_daily_ret.std() * np.sqrt(252)
        info_ratio = (cagr - eq_cagr) / tracking_error if tracking_error > 0 else 0.0

        # ---------------------------------------------------------------------
        # 5. 交易胜率与换手质量指标
        # ---------------------------------------------------------------------
        daily_win_rate = np.sum(daily_ret > 0) / len(daily_ret)
        avg_gain = daily_ret[daily_ret > 0].mean() if np.sum(daily_ret > 0) > 0 else 0.0
        avg_loss = abs(daily_ret[daily_ret < 0].mean()) if np.sum(daily_ret < 0) > 0 else 1e-6
        profit_loss_ratio = avg_gain / avg_loss

        # 年均双边换手率 (Annualized Turnover)
        total_turnover = df['turnover'].sum()
        annual_turnover = total_turnover / years
        total_fee_cost = df['fee_cost'].sum() if 'fee_cost' in df.columns else 0.0

        # ---------------------------------------------------------------------
        # 6. 指标汇总与中文格式化映射
        # ---------------------------------------------------------------------
        self.metrics_summary = {
            "回测区间": f"{df.index[0]} ~ {df.index[-1]} ({years:.1f} 年)",
            "策略累计收益": f"{total_return * 100:.2f}%",
            "策略年化收益 (CAGR)": f"{cagr * 100:.2f}%",
            "策略年化波动率": f"{ann_vol * 100:.2f}%",
            "策略夏普比率 (rf=2%)": f"{sharpe:.2f}",
            "策略最大回撤 (MDD)": f"{max_drawdown * 100:.2f}%",
            "策略卡玛比率 (Calmar)": f"{calmar:.2f}",
            "策略索提诺比率 (Sortino)": f"{sortino:.2f}",
            "基准累计收益 (等权)": f"{eq_total_return * 100:.2f}%",
            "基准年化收益 (等权)": f"{eq_cagr * 100:.2f}%",
            "基准年化波动 (等权)": f"{eq_ann_vol * 100:.2f}%",
            "基准夏普比率 (等权)": f"{eq_sharpe:.2f}",
            "基准最大回撤 (等权)": f"{eq_max_drawdown * 100:.2f}%",
            "超额年化收益": f"{(cagr - eq_cagr) * 100:.2f}%",
            "信息比率 (IR)": f"{info_ratio:.2f}",
            "日度胜率": f"{daily_win_rate * 100:.2f}%",
            "盈亏比": f"{profit_loss_ratio:.2f}",
            "年均双边换手率": f"{annual_turnover * 100:.2f}%",
            "单边调仓费率": f"{self.transaction_cost * 100:.3f}% ({self.transaction_cost * 10000:.1f} bps)",
            "全周期累计摩擦损耗": f"{total_fee_cost * 100:.2f}%"
        }

    def print_summary(self):
        """
        在控制台以美观表格格式打印回测核心指标与分年度收益表
        """
        print("\n" + "=" * 65)
        print("【动态风险预算模型（Dynamic Risk Budget）全周期回测指标】")
        print("=" * 65)
        for k, v in self.metrics_summary.items():
            print(f"{k:25s}: {v}")
        print("=" * 65)

        # 打印各自然年度收益率明细表
        annual_df = self.get_annual_returns_table()
        print("\n【分年度历史收益率对比表 (Calendar Year Performance)】")
        print(annual_df.to_string())
        print("=" * 65)

    def get_annual_returns_table(self):
        """
        按自然年度（Calendar Year）统计收益率与年内最大回撤明细表

        :return: pd.DataFrame 包含各年度的策略净值收益、等权基准、超额收益、年内最大回撤及各单资产表现
        """
        df = self.backtest_results_df.copy()
        df['year'] = [d[:4] for d in df.index]

        annual_rows = []
        for year, group in df.groupby('year'):
            # 策略自然年复合收益率 = prod(1 + daily_ret) - 1
            strat_ann = ((1.0 + group['daily_ret']).prod() - 1.0) * 100
            # 等权基准自然年复合收益率
            eq_ann = ((1.0 + group['daily_eq_ret']).prod() - 1.0) * 100
            
            row = {
                "年份": year,
                "策略净值收益": f"{strat_ann:+.2f}%",
                "等权基准": f"{eq_ann:+.2f}%",
                "超额收益": f"{strat_ann - eq_ann:+.2f}%",
                "策略年内最大回撤": f"{group['drawdown'].min() * 100:.2f}%"
            }
            # 记录资产池中各个单资产在该自然年度的持有收益表现
            for k in self.asset_keys:
                name = self.asset_pool[k].get('name', k)
                asset_ret = ((1.0 + group[f"ret_{k}"]).prod() - 1.0) * 100
                row[name] = f"{asset_ret:+.2f}%"
            annual_rows.append(row)

        return pd.DataFrame(annual_rows)

    def plot_results(self, save_path: str = None):
        """
        绘制 4 合 1 宏观策略回测全景高清图表并保存至文件

        【四张子图设计规范】
        1. 子图 1 (gs[0]): 累计净值走势图 (Cumulative NAV)
           - 展示动态风险预算策略净值、等权基准净值以及主要单资产（股票/国债）持有曲线；
           - 底部叠加普林格宏观六周期的背景着色带 (axvspan)，直观验证策略在不同周期的表现。
        2. 子图 2 (gs[1]): 水下动态回撤曲线 (Underwater Drawdown)
           - 策略回撤面积图 vs 等权基准回撤线，展示回撤控制能力与危机修复速度。
        3. 子图 3 (gs[2]): 历史大类资产配置仓位堆叠图 (Stackplot 0~100%)
           - 展示底层大类资产仓位在各个宏观周期的动态流转轨迹。
        4. 子图 4 (gs[3]): 各自然年度收益率对比柱状图 (Calendar Year Returns Bar)
           - 逐年直观展示策略 vs 基准的年度超额收益分布。

        :param save_path: 图像输出绝对或相对路径，若为 None 则默认保存在当前脚本目录下。
        :return: 图像保存的实际绝对路径
        """
        df = self.backtest_results_df.copy()
        dates = pd.to_datetime(df.index)

        fig = plt.figure(figsize=(15, 14), dpi=150)
        gs = fig.add_gridspec(4, 1, height_ratios=[3.2, 1.8, 2.2, 2.0], hspace=0.32)

        # 经典机构级配色方案
        colors = {
            "strat": "#D32F2F",     # 鲜亮红（策略曲线，醒目主色）
            "eq": "#1976D2",        # 稳健蓝（等权基准曲线）
            "param1": "#E64A19",    # 股票资产：橙红色
            "param2": "#388E3C",    # 债券资产：深绿色
            "param3": "#FBC02D",    # 黄金资产：金黄色
            "param4": "#7B1FA2",    # 转债资产：紫色
            "param5": "#0097A7"     # 商品/其他资产：青色
        }

        # ---------------------------------------------------------------------
        # 子图 1: 累计净值走势图 (叠加宏观六周期背景色块)
        # ---------------------------------------------------------------------
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(dates, df['strat_nav'], 
                 label=f"动态风险预算策略 (总收益: {self.metrics_summary['策略累计收益']}, 年化: {self.metrics_summary['策略年化收益 (CAGR)']})", 
                 color=colors['strat'], linewidth=2.2, zorder=5)
        ax1.plot(dates, df['eq_nav'], 
                 label=f"等权重风险预算基准 (总收益: {self.metrics_summary['基准累计收益 (等权)']}, 年化: {self.metrics_summary['基准年化收益 (等权)']})", 
                 color=colors['eq'], linewidth=1.6, linestyle="--", alpha=0.9, zorder=4)

        # 绘制前两项核心单一资产（通常为股票与国债）作为参考参照系
        for k in self.asset_keys[:2]:
            name = self.asset_pool[k].get('name', k)
            c = colors.get(k, '#888888')
            ax1.plot(dates, df[f"nav_{k}"], label=f"{name} (单资产持有)", color=c, linewidth=1.0, alpha=0.45, linestyle=":", zorder=3)

        # 宏观周期背景染色字典 (浅色柔和系，避免干扰净值曲线)
        cycle_color_map = {
            "阶段1-信用扩张": "#E3F2FD",  # 淡蓝 (信贷启动)
            "阶段2-经济复苏": "#E8F5E9",  # 淡绿 (增长繁荣)
            "阶段3-货币退潮": "#FFF3E0",  # 淡橙 (抗通胀紧缩)
            "阶段4-信用退潮": "#FFEBEE",  # 淡粉 (滞胀防御)
            "阶段5-经济放缓": "#F3E5F5",  # 淡紫 (衰退防守)
            "阶段6-货币扩张": "#E0F7FA"   # 淡青 (宽松启动)
        }

        # 提取周期区间并为背景染色
        current_cycle = df['cycle'].iloc[0]
        span_start = dates[0]
        for i in range(1, len(df)):
            if df['cycle'].iloc[i] != current_cycle or i == len(df) - 1:
                span_end = dates[i]
                c = cycle_color_map.get(current_cycle, "#FAFAFA")
                ax1.axvspan(span_start, span_end, color=c, alpha=0.5, zorder=1)
                span_start = dates[i]
                current_cycle = df['cycle'].iloc[i]

        ax1.set_title("动态风险预算策略累计净值走势 vs 基准（2007 ~ 2026 全景回测，背景为宏观六周期）", fontsize=13, fontweight='bold', pad=10)
        ax1.set_ylabel("累计净值 (NAV)", fontsize=10)
        ax1.grid(True, linestyle="--", alpha=0.4)
        ax1.legend(loc="upper left", framealpha=0.9, fontsize=9)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        # ---------------------------------------------------------------------
        # 子图 2: 水下动态回撤曲线 (Underwater Drawdown)
        # ---------------------------------------------------------------------
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        ax2.plot(dates, df['drawdown'] * 100, 
                 label=f"策略动态回撤 (最大回撤: {self.metrics_summary['策略最大回撤 (MDD)']})", 
                 color=colors['strat'], linewidth=1.5)
        # 填充红色半透明区域表示回撤痛苦区
        ax2.fill_between(dates, df['drawdown'] * 100, 0, color=colors['strat'], alpha=0.25)
        ax2.plot(dates, df['eq_drawdown'] * 100, 
                 label=f"等权基准回撤 (最大回撤: {self.metrics_summary['基准最大回撤 (等权)']})", 
                 color=colors['eq'], linewidth=1.2, linestyle="--", alpha=0.7)
        ax2.set_ylabel("回撤幅度 (%)", fontsize=10)
        ax2.yaxis.set_major_formatter(PercentFormatter(decimals=0))
        ax2.grid(True, linestyle="--", alpha=0.4)
        ax2.legend(loc="lower left", framealpha=0.9, fontsize=9)

        # ---------------------------------------------------------------------
        # 子图 3: 历史大类资产配置仓位堆叠图 (Stackplot)
        # ---------------------------------------------------------------------
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        w_data = [df[f"w_{k}"] * 100 for k in self.asset_keys]
        labels = [self.asset_pool[k].get('name', k) for k in self.asset_keys]
        stack_colors = [colors.get(k, '#999999') for k in self.asset_keys]

        ax3.stackplot(dates, w_data, labels=labels, colors=stack_colors, alpha=0.85)
        ax3.set_ylabel("资产配置权重 (%)", fontsize=10)
        ax3.set_ylim(0, 100)
        ax3.yaxis.set_major_formatter(PercentFormatter(decimals=0))
        ax3.grid(True, linestyle="--", alpha=0.4)
        ax3.legend(loc="upper left", framealpha=0.9, fontsize=9, ncol=len(self.asset_keys))

        # ---------------------------------------------------------------------
        # 子图 4: 各自然年度收益率对比柱状图 (Calendar Year Performance)
        # ---------------------------------------------------------------------
        ax4 = fig.add_subplot(gs[3])
        annual_df = self.get_annual_returns_table()
        years_list = annual_df['年份'].tolist()
        strat_returns = [float(v.replace('%', '')) for v in annual_df['策略净值收益']]
        eq_returns = [float(v.replace('%', '')) for v in annual_df['等权基准']]

        x = np.arange(len(years_list))
        width = 0.38

        rects1 = ax4.bar(x - width/2, strat_returns, width, label='动态风险预算策略', color=colors['strat'], alpha=0.85)
        rects2 = ax4.bar(x + width/2, eq_returns, width, label='等权重基准', color=colors['eq'], alpha=0.85)

        ax4.axhline(0, color='black', linewidth=0.8, linestyle='-')
        ax4.set_ylabel("年度收益率 (%)", fontsize=10)
        ax4.set_xticks(x)
        ax4.set_xticklabels(years_list, rotation=35, ha='right', fontsize=9)
        ax4.yaxis.set_major_formatter(PercentFormatter(decimals=0))
        ax4.grid(True, linestyle="--", alpha=0.4, axis='y')
        ax4.legend(loc="upper left", framealpha=0.9, fontsize=9)
        ax4.set_title("2007 ~ 2026 各自然年度收益率对比 (Calendar Year Returns)", fontsize=11, fontweight='bold', pad=8)

        # ---------------------------------------------------------------------
        # 图表保存
        # ---------------------------------------------------------------------
        if save_path is None:
            save_path = os.path.join(os.path.dirname(__file__), "backtest_dynamic_risk_budget_results.png")
        
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
        print(f"\n[可视化图表已生成并保存] -> {save_path}")
        return save_path


def run_backtest_api(payload: dict) -> dict:
    """
    提供给前端界面及 HTTP RESTful API 调用的动态风险预算回测通用接口

    【入参 payload 字段详解】
    :param payload: dict 字典结构，包含以下字段：
        - asset_pool: 资产定义字典，格式如:
          {"param1": {"code": "h00852_sh", "name": "中证1000全收益"}, "param2": {...}}
          (兼顾兼容 asset_pool_major / asset_pool_sector 别名)
        - cycle_rb_rules: 宏观6周期对应的目标风险预算配额字典，格式如:
          {"阶段1-信用扩张": {"param1": 0.40, "param2": 0.10, ...}, ...}
          (兼顾兼容 cycle_rb_rules_major / cycle_rb_rules_sector 别名)
        - data_table: 数据库收益率表名 (默认为 "stock_returns")
        - start_date: 回测起始日期 (格式 "YYYY-MM-DD"，默认 "2010-01-01")
        - end_date: 回测截止日期 (格式 "YYYY-MM-DD"，默认 "2025-12-31")
        - rebalance_freq: 调仓模式:
          * "M": 每月最后一个交易日调仓
          * "stage_change": 仅当宏观周期切换时调仓
          * "M_or_stage_change": 月末或宏观周期切换时触发调仓 (默认推荐)
        - custom_bounds: 资产持仓权重边界硬约束 (可选)，例如: {"param1": [0.0, 0.20]}
        - history_window: 协方差估计的历史滚动交易日窗口 (整数，默认 720)
        - transaction_cost: 单边调仓交易摩擦成本率 (浮点数，默认 0.0003 即万分之三)
        - rf: 无风险年化利率 (浮点数，默认 0.02 即 2.0%)

    【返回字典返回值字段详解 (return dict)】
    :return: dict 包含完整量化分析结果与可视化时序数据：
        - success: bool，执行是否成功 (True/False)
        - metrics_summary: dict，已格式化为带百分号/单位字符串的核心指标总览
        - raw_metrics: dict，未格式化的纯浮点数指标（供前端组件取值、卡片展示与阈值判断）：
            * cagr: 策略年化复合收益率 (%)
            * total_return: 策略累计总收益率 (%)
            * ann_vol: 策略年化波动率 (%)
            * sharpe: 策略夏普比率
            * max_drawdown: 策略最大回撤幅度 (%)，为负数
            * calmar: 策略卡玛比率
            * sortino: 策略索提诺比率
            * win_rate: 策略日度胜率 (%)
            * annual_turnover: 策略年均双边换手率 (%)
            * eq_cagr: 等权基准年化复合收益率 (%)
            * eq_total_return: 等权基准累计总收益率 (%)
            * eq_ann_vol: 等权基准年化波动率 (%)
            * eq_sharpe: 等权基准夏普比率
            * eq_max_drawdown: 等权基准最大回撤幅度 (%)
            * excess_cagr: 策略相对等权基准的年化超额收益率 (%)
        - annual_table: list[dict]，各自然年度的策略收益、基准收益、超额收益与最大回撤表
        - nav_series: list[dict]，逐日净值与回撤时序，供 ECharts 绘制第一和第二子图：
            * date: 交易日期 (YYYY-MM-DD)
            * cycle: 当日宏观周期阶段名称
            * strat_nav: 策略累计净值
            * eq_nav: 等权基准累计净值
            * drawdown: 策略当日水下回撤百分比 (%)
            * eq_drawdown: 等权基准当日水下回撤百分比 (%)
            * asset_navs: 各底层大类资产买入持有累计净值字典
            * asset_drawdowns: 各底层大类资产动态回撤百分比字典
        - allocation_series: list[dict]，逐日资产仓位权重时序，供 ECharts 绘制第三子图堆叠面积图：
            * date: 交易日期 (YYYY-MM-DD)
            * weights: 各资产当日收盘权重百分比字典 (0~100)
        - cycle_spans: list[dict]，宏观周期区间的起止时间，供前端 ECharts markArea 绘制背景染色色块：
            * cycle: 宏观周期中文名
            * start: 区间起始日期
            * end: 区间截止日期
        - asset_list: list[dict]，资产池元信息列表 (id, name, code)
        - rebalances_count: int，整个回测周期内实际触发调仓的总次数
        - date_range: str，回测实际覆盖的有效日期范围字符串 (如 "2010-01-04 ~ 2025-12-31")
    """
    # 兼容 Pydantic BaseModel 对象
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(exclude_unset=True)
    elif hasattr(payload, "dict"):
        payload = payload.dict(exclude_unset=True)

    # 兼容多种入参命名（支持大类资产与行业超额两套场景传参）
    asset_pool = payload.get('asset_pool') or payload.get('asset_pool_major') or payload.get('asset_pool_sector')
    cycle_rb_rules = payload.get('cycle_rb_rules') or payload.get('cycle_rb_rules_major') or payload.get('cycle_rb_rules_sector')
    data_table = payload.get('data_table') or payload.get('data_table_sector') or payload.get('data_table_major') or 'stock_returns'


    if not asset_pool or not cycle_rb_rules:
        raise ValueError("缺少必填参数: asset_pool, cycle_rb_rules 均为必选参数")

    # 规范化 custom_bounds 为 tuple 格式 (min_w, max_w)
    custom_bounds_raw = payload.get('custom_bounds') or {}
    clean_bounds = {}
    for k, v in custom_bounds_raw.items():
        if isinstance(v, (list, tuple)) and len(v) == 2:
            clean_bounds[k] = (float(v[0]), float(v[1]))

    # 自动识别主要股票指数代码，若用户未显式指定上限，则添加默认 20% 上限约束以防范单边极端波动风险
    for k, info in asset_pool.items():
        code = str(info.get('code', '')).upper().strip('`')
        if code in ['H00852.SH', 'H00300.CSI', '000300.SH', '000852.SH', 'H00852_SH', 'H00300_CSI'] or 'stock' in str(k).lower():
            if k not in clean_bounds:
                clean_bounds[k] = (0.0, 0.20)

    # 提取可选运行参数并赋予稳健默认值
    start_date = payload.get('start_date') or "2007-01-01"
    end_date = payload.get('end_date') or "2026-08-31"
    rebalance_freq = payload.get('rebalance_freq') or "M_or_stage_change"
    history_window = int(payload.get('history_window', 720))
    try:
        raw_cost = payload.get('transaction_cost')
        transaction_cost = float(raw_cost) if raw_cost is not None else 0.0003
    except (TypeError, ValueError):
        transaction_cost = 0.0003
    rf = float(payload.get('rf', 0.02))
    api_base_url = payload.get('api_base_url')

    # 实例化回测引擎
    engine = RiskBudgetBacktestEngine(
        asset_pool=asset_pool,
        cycle_rb_rules=cycle_rb_rules,
        data_table=data_table,
        start_date=start_date,
        end_date=end_date,
        rebalance_freq=rebalance_freq,
        custom_bounds=clean_bounds,
        history_window=history_window,
        transaction_cost=transaction_cost,
        rf=rf,
        api_base_url=api_base_url
    )


    # 执行回测
    engine.run_backtest()
    df = engine.backtest_results_df

    # -------------------------------------------------------------------------
    # 1. 提取逐日净值与仓位权重时序 (供前端 ECharts 图表渲染)
    # -------------------------------------------------------------------------
    nav_series = []
    allocation_series = []
    for date_str, row in df.iterrows():
        # 净值与回撤时序
        nav_series.append({
            "date": str(date_str),
            "cycle": str(row["cycle"]),
            "strat_nav": round(float(row["strat_nav"]), 4),
            "eq_nav": round(float(row["eq_nav"]), 4),
            "drawdown": round(float(row["drawdown"]) * 100, 2),
            "eq_drawdown": round(float(row["eq_drawdown"]) * 100, 2),
            "asset_navs": {k: round(float(row[f"nav_{k}"]), 4) for k in engine.asset_keys},
            "asset_drawdowns": {k: round(float(row.get(f"drawdown_{k}", 0.0)) * 100, 2) for k in engine.asset_keys}
        })
        # 资产持仓权重分布时序 (转为 0~100 百分比数值)
        allocation_series.append({
            "date": str(date_str),
            "weights": {k: round(float(row[f"w_{k}"]) * 100, 2) for k in engine.asset_keys}
        })

    # -------------------------------------------------------------------------
    # 2. 分自然年度收益与回撤对比表
    # -------------------------------------------------------------------------
    annual_df = engine.get_annual_returns_table()
    annual_table = annual_df.to_dict(orient="records")

    # -------------------------------------------------------------------------
    # 3. 资产信息简表 (供前端配置展示)
    # -------------------------------------------------------------------------
    asset_list = []
    for k in engine.asset_keys:
        info = asset_pool.get(k, {})
        asset_list.append({
            "id": k,
            "name": info.get("name", k),
            "code": info.get("code", "")
        })

    # -------------------------------------------------------------------------
    # 4. 宏观周期背景色块区间划分 (供前端 ECharts markArea 绘制使用)
    # -------------------------------------------------------------------------
    cycle_spans = []
    if len(df) > 0:
        cur_cycle = str(df['cycle'].iloc[0])
        s_date = str(df.index[0])
        for i in range(1, len(df)):
            c_name = str(df['cycle'].iloc[i])
            if c_name != cur_cycle or i == len(df) - 1:
                e_date = str(df.index[i])
                cycle_spans.append({
                    "cycle": cur_cycle,
                    "start": s_date,
                    "end": e_date
                })
                cur_cycle = c_name
                s_date = str(df.index[i])

    # -------------------------------------------------------------------------
    # 5. 提取纯浮点数量化指标字典 (raw_metrics, 供前端看板与卡片渲染)
    # -------------------------------------------------------------------------
    days = len(df)
    years = max(days / 252.0, 0.1)
    daily_ret = df['daily_ret']
    daily_eq_ret = df['daily_eq_ret']
    total_return = float(df['strat_nav'].iloc[-1] - 1.0)
    cagr = float((df['strat_nav'].iloc[-1]) ** (1.0 / years) - 1.0)
    eq_total_return = float(df['eq_nav'].iloc[-1] - 1.0)
    eq_cagr = float((df['eq_nav'].iloc[-1]) ** (1.0 / years) - 1.0)
    ann_vol = float(daily_ret.std() * np.sqrt(252))
    eq_ann_vol = float(daily_eq_ret.std() * np.sqrt(252))
    max_drawdown = float(df['drawdown'].min())
    eq_max_drawdown = float(df['eq_drawdown'].min())
    sharpe = float((cagr - rf) / ann_vol) if ann_vol > 0 else 0.0
    eq_sharpe = float((eq_cagr - rf) / eq_ann_vol) if eq_ann_vol > 0 else 0.0
    calmar = float(cagr / abs(max_drawdown)) if abs(max_drawdown) > 0 else 0.0
    downside_ret = daily_ret[daily_ret < 0]
    downside_std = float(downside_ret.std() * np.sqrt(252)) if len(downside_ret) > 0 else 1e-6
    sortino = float((cagr - rf) / downside_std)
    daily_win_rate = float(np.sum(daily_ret > 0) / len(daily_ret))
    annual_turnover = float(df['turnover'].sum() / years)
    total_fee_cost = float(df['fee_cost'].sum()) if 'fee_cost' in df.columns else 0.0

    # 计算主动超额收益序列、年化跟踪误差与信息比率 (Information Ratio)
    excess_daily_ret = daily_ret - daily_eq_ret
    tracking_error = float(excess_daily_ret.std() * np.sqrt(252)) if len(excess_daily_ret) > 0 else 1e-6
    info_ratio = float((cagr - eq_cagr) / tracking_error) if tracking_error > 0 else 0.0

    raw_metrics = {
        "cagr": round(cagr * 100, 2),                   # 策略年化复合收益率 (%)
        "total_return": round(total_return * 100, 2),   # 策略累计全周期收益率 (%)
        "ann_vol": round(ann_vol * 100, 2),             # 策略年化波动率 (%)
        "sharpe": round(sharpe, 2),                     # 策略夏普比率
        "max_drawdown": round(max_drawdown * 100, 2),   # 策略最大回撤 (%)
        "calmar": round(calmar, 2),                     # 策略卡玛比率
        "sortino": round(sortino, 2),                   # 策略索提诺比率
        "ir": round(info_ratio, 2),                     # 策略信息比率 (IR)
        "tracking_error": round(tracking_error * 100, 2), # 年化跟踪误差 (%)
        "win_rate": round(daily_win_rate * 100, 2),     # 策略日度胜率 (%)
        "annual_turnover": round(annual_turnover * 100, 2), # 策略年均双边换手率 (%)
        "transaction_cost": transaction_cost,           # 单边调仓费率数值 (如 0.0003)
        "transaction_cost_pct": round(transaction_cost * 100, 4), # 单边调仓费率百分比 (如 0.03%)
        "total_fee_cost": round(total_fee_cost * 100, 2), # 全周期累计交易摩擦损耗 (%)
        "eq_cagr": round(eq_cagr * 100, 2),             # 等权基准年化收益率 (%)
        "eq_total_return": round(eq_total_return * 100, 2), # 等权基准累计收益率 (%)
        "eq_ann_vol": round(eq_ann_vol * 100, 2),       # 等权基准年化波动率 (%)
        "eq_sharpe": round(eq_sharpe, 2),               # 等权基准夏普比率
        "eq_max_drawdown": round(eq_max_drawdown * 100, 2), # 等权基准最大回撤 (%)
        "excess_cagr": round((cagr - eq_cagr) * 100, 2) # 策略年化超额收益率 (%)
    }

    return {
        "success": True,
        "metrics_summary": engine.metrics_summary,  # 中文格式化汇总
        "raw_metrics": raw_metrics,                # 纯浮点数量化指标
        "annual_table": annual_table,              # 分自然年度收益表
        "nav_series": nav_series,                  # 每日净值与回撤时序
        "allocation_series": allocation_series,    # 每日各资产持仓权重时序
        "cycle_spans": cycle_spans,                # 宏观周期色块区间划分
        "asset_list": asset_list,                  # 资产池列表信息
        "rebalances_count": len(engine.rebalance_records), # 调仓总次数
        "date_range": f"{df.index[0]} ~ {df.index[-1]}"    # 回测有效日期区间
    }


def run_full_backtest_demo():
    """
    一键运行全量大类资产动态风险预算策略回测演示函数

    【演示组合资产配置】
    1. 股票资产 (param1): 中证1000全收益 (h00852_sh) - 高波动、高成长弹性资产
    2. 国债资产 (param2): 中债-国债总财富7-10年 (cba00651_cs) - 防御型安全资产，避险对冲
    3. 黄金资产 (param3): SGE黄金9999 (au9999_sge) - 经典抗通胀与地缘对冲资产
    4. 转债资产 (param4): 中证转债 (idx_000832_csi) - 兼具股性与债性的混合收益增强资产

    【宏观六周期目标风险预算设置逻辑】
    - 阶段1-信用扩张：宽信用初期，股票与转债弹性高，分配较高风险预算 (40% 股 / 30% 转债)；
    - 阶段2-经济复苏：经济繁荣上行期，超配股票风险预算 (50% 股 / 40% 转债)；
    - 阶段3-货币退潮：通胀升温、货币紧缩，适当均衡黄金与转债 (40% 股 / 45% 转债 / 10% 债)；
    - 阶段4-信用退潮：滞胀风险显现，大幅提升国债避险预算 (60% 国债 / 20% 黄金)；
    - 阶段5-经济放缓：经济衰退期，超配国债与黄金防守 (50% 国债 / 40% 黄金 / 仅 5% 股票)；
    - 阶段6-货币扩张：宽货币降息初期，长端国债迎来牛市，国债风险预算最高 (65% 国债 / 25% 黄金)。
    """
    # 1. 资产池定义
    asset_pool_major = {
        "param1": {"code": "H00852.SH", "name": "中证1000全收益"},
        "param2": {"code": "CBA00651.CS", "name": "中债-国债总财富(7-10年)指数"},
        "param3": {"code": "AU9999.SGE", "name": "SGE黄金9999"},
        "param4": {"code": "000832.CSI", "name": "中证转债"}
    }

    # 2. 宏观6周期对应的目标风险预算配额 (TRC 目标)
    cycle_rb_rules_major = {
        "阶段1-信用扩张": {"param1": 0.40, "param2": 0.10, "param3": 0.20, "param4": 0.30},
        "阶段2-经济复苏": {"param1": 0.50, "param2": 0.05, "param3": 0.05, "param4": 0.40},
        "阶段3-货币退潮": {"param1": 0.40, "param2": 0.10, "param3": 0.05, "param4": 0.45},
        "阶段4-信用退潮": {"param1": 0.10, "param2": 0.60, "param3": 0.20, "param4": 0.10},
        "阶段5-经济放缓": {"param1": 0.05, "param2": 0.50, "param3": 0.40, "param4": 0.05},
        "阶段6-货币扩张": {"param1": 0.05, "param2": 0.65, "param3": 0.25, "param4": 0.05}
    }

    # 3. 股票与转债仓位边界硬约束 (股票上限 20%，黄金 50%，转债 50%，防范单边尾部黑天鹅风险)
    custom_bounds = {
        "param1": (0.0, 0.20),
        "param2": (0.0, 1.0),
        "param3": (0.0, 0.50),
        "param4": (0.0, 0.50)
    }

    # 4. 构建回测引擎实例
    engine = RiskBudgetBacktestEngine(
        asset_pool=asset_pool_major,
        cycle_rb_rules=cycle_rb_rules_major,
        data_table="stock_returns",
        start_date="2007-01-01",
        end_date="2026-08-31",
        rebalance_freq="M_or_stage_change",
        custom_bounds=custom_bounds,
        history_window=720,
        transaction_cost=0.0003,
        rf=0.02
    )

    # 5. 执行回测、打印指标汇总表并绘制全景高清图
    engine.run_backtest()
    engine.print_summary()
    save_img = engine.plot_results()
    return engine, save_img


if __name__ == "__main__":
    # 本地直接运行此脚本进行全量回测演示验证
    run_full_backtest_demo()
