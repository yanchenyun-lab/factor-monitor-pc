# -*- coding: utf-8 -*-
"""
动态风险预算模型核心代码 (支持任意动态入参，纯 HTTP API 数据源)

【适用场景】
专为内网微服务/云桌面隔离环境设计，不依赖任何数据库直连 (pymysql 已彻底移除)。
行情收益率数据与宏观经济周期数据全部通过 smartIR Java 后端 HTTP 接口 (POST /api/returns/risk-data) 实时获取。

核心入参说明：
1. asset_pool: 资产池定义字典 (key为任意标识，如 param1, param2 等)
2. cycle_rb_rules: 宏观6周期对应的目标风险预算配额字典
3. data_table: 收益率数据类型/表标识 (默认 "stock_returns")
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import requests

# 重新配置标准输出编码，兼容Windows控制台
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# smartIR Java 后端数据服务基础地址 (内网环境可通过环境变量 SMARTIR_API_BASE 自定义)
DEFAULT_SMARTIR_API_BASE = os.environ.get("SMARTIR_API_BASE", "http://127.0.0.1:8080")

# 普林格宏观六周期映射表
CYCLE_MAP = {
    1: "阶段1-信用扩张",
    2: "阶段2-经济复苏",
    3: "阶段3-货币退潮",
    4: "阶段4-信用退潮",
    5: "阶段5-经济放缓",
    6: "阶段6-货币扩张"
}


class DynamicRiskBudgetModel:
    def __init__(self, 
                 asset_pool: dict, 
                 cycle_rb_rules: dict, 
                 data_table: str = "stock_returns", 
                 custom_bounds: dict = None, 
                 history_window: int = 720,
                 api_base_url: str = None,
                 **kwargs):
        """
        初始化动态风险预算模型 (纯 HTTP 数据源，无直连数据库依赖)
        :param asset_pool: 资产池字典，格式如 {"param1": {"code": "H00852.SH", "name": "中证1000全收益"}, ...}
        :param cycle_rb_rules: 宏观周期风险预算配额字典，如 {"阶段1-信用扩张": {"param1": 0.4, ...}, ...}
        :param data_table: 数据标识 (默认 "stock_returns")
        :param custom_bounds: 权重边界约束字典 (如 {"param1": (0.0, 0.2)})，未指定资产默认 (0.0, 1.0)
        :param history_window: 协方差回溯交易日窗口 (默认 720 天)
        :param api_base_url: smartIR Java 后端 HTTP 服务基地址，默认取环境变量 SMARTIR_API_BASE 或 http://127.0.0.1:8080
        """
        self.asset_pool = asset_pool
        self.asset_keys = list(asset_pool.keys())
        self.cycle_rb_rules = cycle_rb_rules
        self.data_table = data_table
        self.custom_bounds = custom_bounds or {}
        self.history_window = history_window
        self.api_base_url = api_base_url or DEFAULT_SMARTIR_API_BASE
        self.logger = logging.getLogger(f"DynamicRiskBudget_{self.data_table}")

    def fetch_data_from_api(self, end_date: str):
        """
        通过 smartIR Java 后端提供的 HTTP 接口获取宏观阶段与资产收益率时序
        适用于内网隔离环境中无法直连 MySQL 数据库的场景
        """
        raw_codes = [str(info['code']).strip('`') for info in self.asset_pool.values()]
        url = f"{self.api_base_url.rstrip('/')}/api/returns/risk-data"
        payload = {
            "assetCodes": raw_codes,
            "endDate": end_date,
            "historyWindow": self.history_window
        }
        self.logger.info(f"正在从 Java API 获取风险数据: {url}, assetCodes={raw_codes}, endDate={end_date}")
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到 smartIR Java 后端服务 ({url})，请确认 Java 项目 (端口 8080) 已启动或检查环境变量 SMARTIR_API_BASE")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求 smartIR Java 后端服务超时 (超过 30s): {url}")
        except Exception as e:
            raise RuntimeError(f"请求 smartIR Java 接口失败: {url}, 错误: {e}")

        # 支持不同包装格式: 统一返回实体 {"code": 200, "data": {...}} 或直接 {...}
        data_bundle = res_json.get('data') if isinstance(res_json, dict) and 'data' in res_json else res_json
        if not data_bundle or not isinstance(data_bundle, dict):
            raise ValueError(f"从 Java 接口 {url} 获取数据为空或格式不正确: {res_json}")

        # 解析最新宏观阶段
        current_cycle = data_bundle.get('latestCycleName') or CYCLE_MAP.get(data_bundle.get('latestStage', 1), "阶段1-信用扩张")
        
        # 解析资产收益率时序列表
        raw_returns = data_bundle.get('returns') or []
        if not raw_returns:
            raise ValueError(f"未能通过接口获取到相关资产收益率数据 (returns 列表为空)")

        df_raw = pd.DataFrame(raw_returns)
        # 兼容驼峰和下划线命名
        trade_date_col = 'tradeDate' if 'tradeDate' in df_raw.columns else 'trade_date'
        asset_code_col = 'assetCode' if 'assetCode' in df_raw.columns else 'asset_code'
        return_rate_col = 'returnRate' if 'returnRate' in df_raw.columns else 'return_rate'

        df_raw['trade_date'] = df_raw[trade_date_col].astype(str)
        df = df_raw.pivot(index='trade_date', columns=asset_code_col, values=return_rate_col)

        # 构建大小写不敏感的列名映射，将代码重命名为 asset_pool 的 key (如 param1, param2)
        lower_rename_map = {str(info['code']).lower().strip('`'): key for key, info in self.asset_pool.items()}
        new_columns = []
        for col in df.columns:
            col_clean = str(col).lower().strip('`')
            col_key = lower_rename_map.get(col_clean, col)
            new_columns.append(col_key)
        df.columns = new_columns

        # 数值清洗：转为 float 并减 1 得到真实涨跌幅
        for col in self.asset_keys:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float) - 1.0

        df.dropna(inplace=True)
        max_date = data_bundle.get('maxDate') or (df.index[-1] if len(df) > 0 else end_date)
        return current_cycle, df, max_date

    @staticmethod
    def risk_budget_objective(w, cov_matrix, target_risk_budgets):
        """
        优化目标函数：最小化 (当前资产风险贡献占比 - 目标风险预算占比) 的平方差总和
        """
        w = np.array(w).reshape(-1, 1)
        target_risk_budgets = np.array(target_risk_budgets).reshape(-1, 1)

        # 组合方差与波动率
        port_var = np.dot(w.T, np.dot(cov_matrix, w))[0, 0]
        port_vol = np.sqrt(max(port_var, 1e-12))

        # 边际风险贡献 MRC = (Sigma * w) / sigma
        mrc = np.dot(cov_matrix, w) / port_vol

        # 风险贡献占比 TRC = (w * MRC) / sigma
        trc = (w * mrc) / port_vol

        # 均方差目标函数
        return np.sum(np.square(trc - target_risk_budgets))

    def solve_constrained_risk_budget(self, rb_ratio_dict, returns_df):
        """
        使用 SLSQP 算法求解带约束条件的风险预算最优权重
        """
        n = len(self.asset_keys)

        # 1. 计算协方差矩阵 (保证对称性)
        cov_matrix = returns_df[self.asset_keys].cov().values
        cov_matrix = (cov_matrix + cov_matrix.T) / 2.0

        # 2. 提取并对齐目标风险预算 (容错匹配 key, code, 或 name)
        target_list = []
        for asset in self.asset_keys:
            rb_val = None
            if asset in rb_ratio_dict:
                rb_val = rb_ratio_dict[asset]
            else:
                asset_code = self.asset_pool[asset].get('code')
                asset_name = self.asset_pool[asset].get('name')
                for k, v in rb_ratio_dict.items():
                    k_str = str(k).strip('`')
                    if k_str == asset_code or k_str == asset_name:
                        rb_val = v
                        break
            if rb_val is None:
                raise ValueError(f"资产 {asset} 在周期规则中未找到对应的风险预算比例")
            target_list.append(float(rb_val))

        target_risk_budgets = np.array(target_list)
        total_rb = np.sum(target_risk_budgets)
        if total_rb <= 0:
            target_risk_budgets = np.ones(n) / n
        else:
            target_risk_budgets = target_risk_budgets / total_rb

        # 3. 约束条件：权重和为 1
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]

        # 4. 边界条件：单资产上下限
        bounds = []
        for asset in self.asset_keys:
            if asset in self.custom_bounds:
                b = self.custom_bounds[asset]
                bounds.append((float(b[0]), float(b[1])))
            else:
                bounds.append((0.0, 1.0))

        # 5. 多初值多重优化，防止局部收敛失败
        best_res = None
        min_fun = np.inf

        init_guesses = [
            np.ones(n) / n,
            target_risk_budgets.copy()
        ]

        vol = np.sqrt(np.diag(cov_matrix))
        inv_vol = 1.0 / np.where(vol == 0, 1e-6, vol)
        init_guesses.append(inv_vol / np.sum(inv_vol))

        for w0 in init_guesses:
            try:
                res = minimize(
                    fun=self.risk_budget_objective,
                    x0=w0,
                    args=(cov_matrix, target_risk_budgets),
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints,
                    options={'ftol': 1e-9, 'maxiter': 500, 'disp': False}
                )
                if res.success and res.fun < min_fun:
                    min_fun = res.fun
                    best_res = res
            except Exception:
                continue

        # 降级备用：等权投影
        if best_res is None or not best_res.success:
            self.logger.warning("SLSQP优化未能完全收敛，采用投影裁剪法生成近似满足约束的权重")
            w_fallback = np.ones(n) / n
            for i, (low, high) in enumerate(bounds):
                w_fallback[i] = np.clip(w_fallback[i], low, high)
            final_w = w_fallback / np.sum(w_fallback)
        else:
            final_w = best_res.x

        return {self.asset_keys[i]: float(final_w[i]) for i in range(n)}

    def run(self, end_date: str = None):
        """
        主运行流程 (纯通过 Java 后端 HTTP 接口获取数据，无数据库访问)
        """
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        current_cycle, returns_df, max_date = self.fetch_data_from_api(end_date)
        rb_target = self.cycle_rb_rules.get(current_cycle, {})

        final_position = self.solve_constrained_risk_budget(
            rb_ratio_dict=rb_target,
            returns_df=returns_df
        )

        return current_cycle, final_position, max_date


def run_dynamic_risk_budget(asset_pool: dict, 
                            cycle_rb_rules: dict, 
                            data_table: str = "stock_returns", 
                            end_date: str = None, 
                            custom_bounds: dict = None,
                            api_base_url: str = None,
                            **kwargs):
    """
    通用动态风险预算快捷入口 (纯 HTTP API 数据源，不依赖数据库)
    :param asset_pool: 资产池定义字典 (key 为任意标识，如 param1, param2)
    :param cycle_rb_rules: 宏观 6 周期风险预算配额字典
    :param data_table: 数据标识 (默认 "stock_returns")
    :param end_date: 截止日期 (YYYY-MM-DD)，可选，默认最新交易日
    :param custom_bounds: 权重边界硬约束 (如 {"param1": (0.0, 0.2)})，可选
    :param api_base_url: smartIR Java 后端 HTTP 服务基地址，可选
    :return: (current_cycle, positions, calc_date)
        positions 为列表结构: [{"id": "param1", "name": "...", "code": "...", "weight": 0.25}, ...]
    """
    if hasattr(asset_pool, "model_dump"):
        asset_pool = asset_pool.model_dump(exclude_unset=True)
    elif hasattr(asset_pool, "dict"):
        asset_pool = asset_pool.dict(exclude_unset=True)

    if hasattr(cycle_rb_rules, "model_dump"):
        cycle_rb_rules = cycle_rb_rules.model_dump(exclude_unset=True)
    elif hasattr(cycle_rb_rules, "dict"):
        cycle_rb_rules = cycle_rb_rules.dict(exclude_unset=True)

    model = DynamicRiskBudgetModel(
        asset_pool=asset_pool,
        cycle_rb_rules=cycle_rb_rules,
        data_table=data_table,
        custom_bounds=custom_bounds,
        api_base_url=api_base_url
    )
    current_cycle, pos, calc_date = model.run(end_date=end_date)

    positions = []
    for k, v in pos.items():
        asset_info = asset_pool.get(k, {})
        positions.append({
            "id": k,
            "name": asset_info.get("name", k),
            "code": asset_info.get("code", ""),
            "weight": float(v)
        })

    return current_cycle, positions, calc_date


# ==================== 演示用例 ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("【测试1】大类资产动态配置 (通过 Java API POST /api/returns/risk-data 获取数据)")
    print("="*60)
    
    asset_pool_major = {
        "param1": {"code": "H00852.SH", "name": "中证1000全收益"},
        "param2": {"code": "CBA00651.CS", "name": "中债-国债总财富(7-10年)指数"},
        "param3": {"code": "AU9999.SGE", "name": "SGE黄金9999"},
        "param4": {"code": "000832.CSI", "name": "中证转债"}
    }
    cycle_rb_rules_major = {
        "阶段1-信用扩张": {"param1": 0.4, "param2": 0.1, "param3": 0.2, "param4": 0.3},
        "阶段2-经济复苏": {"param1": 0.5, "param2": 0.05, "param3": 0.05, "param4": 0.4},
        "阶段3-货币退潮": {"param1": 0.4, "param2": 0.1, "param3": 0.05, "param4": 0.45},
        "阶段4-信用退潮": {"param1": 0.1, "param2": 0.6, "param3": 0.2, "param4": 0.1},
        "阶段5-经济放缓": {"param1": 0.05, "param2": 0.5, "param3": 0.4, "param4": 0.05},
        "阶段6-货币扩张": {"param1": 0.05, "param2": 0.65, "param3": 0.25, "param4": 0.05}
    }

    try:
        cycle1, positions1, calc_date1 = run_dynamic_risk_budget(
            asset_pool=asset_pool_major,
            cycle_rb_rules=cycle_rb_rules_major,
            data_table="stock_returns",
            end_date="2024-05-10"
        )
        print(f"当前经济周期: {cycle1} (截止计算日: {calc_date1})")
        print("最终建议仓位:")
        for item in positions1:
            print(f"[{item['id']}] {item['name']} ({item['code']}): {item['weight']:.4f} ({item['weight']*100:.2f}%)")
    except Exception as e:
        print(f"运行测试失败: {e}")
