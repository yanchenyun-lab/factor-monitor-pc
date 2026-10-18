<template>
  <div class="risk-budget-backtest-container">
    <el-card class="box-card mb-20">
      <div slot="header" class="clearfix">
        <span class="card-title-lg"><i class="el-icon-s-marketing"></i> 动态风险预算策略回测</span>
        <el-tooltip effect="dark" content="基于配置的资产池与各宏观周期的风险预算配额，执行长周期的动态调整并展示回测结果" placement="top-start">
          <i class="el-icon-question help-icon"></i>
        </el-tooltip>
        
        <div class="header-controls" style="float: right; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <el-radio-group v-model="form.type" size="small" @change="onTypeChange">
            <el-radio-button label="major">大类资产模式</el-radio-button>
            <el-radio-button label="sector">行业板块模式</el-radio-button>
          </el-radio-group>
          
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            size="small"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="yyyy-MM-dd"
            style="width: 245px"
            :clearable="false"
            @change="onDateRangeChange">
          </el-date-picker>

          <el-select v-model="form.rebalance_freq" size="small" style="width: 140px">
            <el-option label="月末调仓" value="M"></el-option>
            <el-option label="周期切换调仓" value="stage_change"></el-option>
            <el-option label="双触发调仓" value="M_or_stage_change"></el-option>
          </el-select>

          <!-- 单边调仓交易摩擦成本配置 -->
          <div class="fee-control-box" style="display: flex; align-items: center; gap: 5px;">
            <span style="font-size: 13px; color: #606266; white-space: nowrap;">调仓费率:</span>
            <el-select 
              v-model="feePreset" 
              size="small" 
              style="width: 150px" 
              placeholder="选择费率"
              @change="onFeePresetChange">
              <el-option label="万一 (0.01% 场内)" value="0.0001"></el-option>
              <el-option label="万二 (0.02%)" value="0.0002"></el-option>
              <el-option label="万三 (0.03% 默认)" value="0.0003"></el-option>
              <el-option label="千一 (0.10% 场外优惠)" value="0.0010"></el-option>
              <el-option label="千一点二 (0.12% 机构专户)" value="0.0012"></el-option>
              <el-option label="千一点五 (0.15%)" value="0.0015"></el-option>
              <el-option label="千五 (0.50% 普通申赎)" value="0.0050"></el-option>
              <el-option label="零费率 (0% 理想基准)" value="0"></el-option>
              <el-option label="自定义费率" value="custom"></el-option>
            </el-select>
            <template v-if="feePreset === 'custom'">
              <el-input-number 
                v-model="customFeePercent" 
                size="small" 
                :precision="4" 
                :step="0.01" 
                :min="0" 
                :max="10" 
                controls-position="right"
                style="width: 105px"
                placeholder="费率%"
                @change="onCustomFeeChange">
              </el-input-number>
              <span style="font-size: 12px; color: #909399;">%</span>
            </template>
          </div>

          <el-button 
            type="primary" 
            size="small" 
            icon="el-icon-video-play" 
            :loading="loading"
            @click="runBacktest">
            执行回测
          </el-button>
        </div>
      </div>

      <!-- 未运行提示 -->
      <div v-if="!hasRun" class="empty-state">
        <el-empty description="尚未执行回测，请在上方参数配置面板中点击【保存并重新计算】联动或在此点击【执行回测】" :image-size="120"></el-empty>
      </div>

      <div v-else class="backtest-results" v-loading="loading" element-loading-text="正在进行历史时序推演与测算...">
        <!-- KPI 指标卡片组 -->
        <el-row :gutter="15" class="kpi-panel mb-20">
          <el-col 
            :span="6" 
            v-for="(kpi, index) in kpiList" 
            :key="index"
            class="kpi-col"
            style="height: auto !important; min-height: 110px !important;">
            <div class="kpi-card" :class="kpi.colorClass">
              <div class="kpi-title">{{ kpi.title }}</div>
              <div class="kpi-value">{{ kpi.value }}</div>
              <div class="kpi-sub">
                <template v-if="kpi.subValue">{{ kpi.subText }}: <span>{{ kpi.subValue }}</span></template>
                <template v-else>&nbsp;</template>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 图表区：净值、回撤、仓位 -->
        <el-row :gutter="20">
          <el-col :span="24" style="min-height: 450px;">
            <!-- 累计净值曲线 -->
            <div class="section-title mb-10">
              <span class="card-title-md">累计净值走势</span>
              <el-tooltip effect="dark" content="策略净值与等权重基准的累计收益走势对比，背景色块代表不同的宏观周期阶段" placement="top-start">
                <i class="el-icon-question help-icon"></i>
              </el-tooltip>
            </div>
            <div class="chart-wrapper mb-20" style="height: 400px; min-height: 400px;">
              <div ref="navChart" class="chart-container" style="width: 100%; height: 400px; min-height: 400px;"></div>
            </div>
          </el-col>
          <el-col :span="24" style="min-height: 300px;">
            <!-- 动态回撤 -->
            <div class="section-title mb-10">
              <span class="card-title-md">水下动态回撤 (%)</span>
              <el-tooltip effect="dark" content="回测区间内策略及基准的动态最大回撤曲线，衡量下行风险水平" placement="top-start">
                <i class="el-icon-question help-icon"></i>
              </el-tooltip>
            </div>
            <div class="chart-wrapper mb-20" style="height: 250px; min-height: 250px;">
              <div ref="drawdownChart" class="chart-container" style="width: 100%; height: 250px; min-height: 250px;"></div>
            </div>
          </el-col>
          <el-col :span="24" style="min-height: 400px;">
            <!-- 动态仓位配置 -->
            <div class="section-title mb-10">
              <span class="card-title-md">历史动态仓位分布 (%)</span>
              <el-tooltip effect="dark" content="回测区间内各类资产基于风险预算模型的真实持仓占比堆叠图" placement="top-start">
                <i class="el-icon-question help-icon"></i>
              </el-tooltip>
            </div>
            <div class="chart-wrapper mb-20" style="height: 350px; min-height: 350px;">
              <div ref="allocationChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
            </div>
          </el-col>
        </el-row>
        
        <!-- 分年度收益表 -->
        <div class="annual-table-wrapper" style="min-height: 400px;">
          <div class="section-title mb-10">
            <span class="card-title-md"><i class="el-icon-date"></i> 策略分年度表现对比</span>
            <el-tooltip effect="dark" content="统计各个自然年度内策略的净值收益、等权基准表现及最大回撤等关键指标" placement="top-start">
              <i class="el-icon-question help-icon"></i>
            </el-tooltip>
          </div>
          <div class="chart-wrapper" style="height: 350px; min-height: 350px;">
            <div ref="annualChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
/**
 * @file RiskBudgetBacktest.vue
 * @description 动态风险预算模型历史回测系统
 * 负责接收上方【自定义动态风险预算模型】(DynamicRiskBudget.vue) 传递的资产池定义与 6 个周期的风险预算配额，
 * 调用后端回测引擎接口 (/api/dynamic-risk-budget/backtest) 进行全历史区间定期调仓与风险预算优化求解，
 * 并可视化展示核心业绩 KPI 指标卡、累计净值走势 (NAV)、水下动态回撤、历史动态仓位分布 (堆叠面积图) 以及分年度收益表现柱状图。
 */
import axios from 'axios'
import * as echarts from 'echarts'

/**
 * 宏观六周期背景色映射表 (用于在时序折线图背景中以柔和浅色区块标示经济周期)
 */
const STAGE_COLORS = {
  1: '#85C1E9', // 阶段1-信用扩张
  2: '#E74C3C', // 阶段2-经济复苏
  3: '#F5B041', // 阶段3-货币退潮
  4: '#AAB7B8', // 阶段4-信用退潮
  5: '#2E86C1', // 阶段5-经济放缓
  6: '#7DCEA0'  // 阶段6-货币扩张
}

/**
 * 宏观六周期中文名称映射表
 */
const STAGE_NAMES = {
  1: '信用扩张',
  2: '经济复苏',
  3: '货币退潮',
  4: '信用退潮',
  5: '经济放缓',
  6: '货币扩张'
}

/**
 * 默认调色盘序列（与上方“资产仓位建议”与“板块仓位建议”饼图严格一致的柔和清新浅色系）
 */
const MAJOR_PALETTE = ['#5CA1FC', '#2BBCCF', '#F7DE54', '#4EE0B3', '#86CE46', '#FCA56E']
const SECTOR_PALETTE = ['#5CA1FC', '#2BBCCF', '#4EE0B3', '#86CE46', '#F7DE54', '#FCA56E']

/**
 * 标的资产/板块名称到专属色彩的精准映射
 * 作用：保证不论数据返回的系列顺序如何变动，时序图中的曲线和堆叠面积色彩均与上方饼图 1:1 保持完全一致
 */
const ASSET_COLOR_MAP = {
  // 大类资产 (对齐资产仓位建议)
  '中证1000全收益': '#5CA1FC',
  '中债-国债总财富(7-10年)指数': '#2BBCCF',
  'SGE黄金9999': '#F7DE54',
  '中证转债': '#4EE0B3',

  // 行业板块 (对齐板块仓位建议：天蓝 -> 湖青 -> 薄荷绿 -> 春草绿 -> 浅柠檬黄)
  '消费(风格.中信)': '#5CA1FC',
  '科技产业(中信)': '#2BBCCF',
  '周期产业(中信)': '#4EE0B3',
  '金融产业(中信)': '#86CE46',
  '稳定(风格.中信)': '#F7DE54'
}

/**
 * 默认大类资产池定义（四大固定底层基石）
 */
const DEFAULT_MAJOR_ASSET_POOL = {
  "stock": { "code": "H00852.SH", "name": "中证1000全收益" },
  "bond": { "code": "CBA00651.CS", "name": "中债-国债总财富(7-10年)指数" },
  "gold": { "code": "AU9999.SGE", "name": "SGE黄金9999" },
  "commodity": { "code": "000832.CSI", "name": "中证转债" }
}

/**
 * 默认大类资产在 6 个宏观周期下的目标风险预算配额
 */
const DEFAULT_MAJOR_CYCLE_RB_RULES = {
  "阶段1-信用扩张": { "stock": 0.40, "bond": 0.30, "gold": 0.15, "commodity": 0.15 },
  "阶段2-经济复苏": { "stock": 0.50, "bond": 0.10, "gold": 0.20, "commodity": 0.20 },
  "阶段3-货币退潮": { "stock": 0.40, "bond": 0.15, "gold": 0.15, "commodity": 0.30 },
  "阶段4-信用退潮": { "stock": 0.10, "bond": 0.70, "gold": 0.10, "commodity": 0.10 },
  "阶段5-经济放缓": { "stock": 0.05, "bond": 0.70, "gold": 0.05, "commodity": 0.20 },
  "阶段6-货币扩张": { "stock": 0.05, "bond": 0.80, "gold": 0.05, "commodity": 0.10 }
}

/**
 * 默认行业板块资产池定义
 */
const DEFAULT_SECTOR_ASSET_POOL = {
  "param1": { "code": "CI005919.WI", "name": "消费(风格.中信)" },
  "param2": { "code": "CI005929.WI", "name": "科技产业(中信)" },
  "param3": { "code": "CI005925.WI", "name": "周期产业(中信)" },
  "param4": { "code": "CI005931.WI", "name": "金融产业(中信)" },
  "param5": { "code": "CI005921.WI", "name": "稳定(风格.中信)" }
}

/**
 * 默认行业板块在 6 个宏观周期下的目标风险预算配额
 */
const DEFAULT_SECTOR_CYCLE_RB_RULES = {
  "阶段1-信用扩张": { "param1": 0.15, "param2": 0.20, "param3": 0.30, "param4": 0.25, "param5": 0.10 },
  "阶段2-经济复苏": { "param1": 0.35, "param2": 0.30, "param3": 0.15, "param4": 0.10, "param5": 0.10 },
  "阶段3-货币退潮": { "param1": 0.20, "param2": 0.10, "param3": 0.35, "param4": 0.25, "param5": 0.10 },
  "阶段4-信用退潮": { "param1": 0.25, "param2": 0.15, "param3": 0.05, "param4": 0.15, "param5": 0.40 },
  "阶段5-经济放缓": { "param1": 0.25, "param2": 0.15, "param3": 0.05, "param4": 0.10, "param5": 0.45 },
  "阶段6-货币扩张": { "param1": 0.20, "param2": 0.40, "param3": 0.10, "param4": 0.15, "param5": 0.15 }
}

export default {
  name: 'RiskBudgetBacktest',
  data() {
    return {
      /** @property {boolean} hasRun - 是否已执行完成过一次回测测算（用于控制下方业绩图表展示） */
      hasRun: false,
      /** @property {boolean} loading - 回测接口计算中遮罩状态 */
      loading: false,
      /** @property {Array} dateRange - 回测起止日期范围绑定值 [start_date, end_date] */
      dateRange: ['2007-01-01', '2026-08-31'],
      /** @property {Object} form - 回测配置表单 */
      form: {
        type: 'major', // 回测标的模式：'major'（大类资产模式）或 'sector'（行业板块模式）
        rebalance_freq: 'M', // 调仓频率：'M'（月度调仓）、'W'（周度调仓）、'Q'（季度调仓）
        start_date: '2007-01-01', // 回测历史起点日期
        end_date: '2026-08-31', // 回测历史截止日期
        transaction_cost: 0.0003, // 单边调仓交易摩擦成本（默认 0.0003，即万三）
        asset_pool: JSON.parse(JSON.stringify(DEFAULT_MAJOR_ASSET_POOL)), // 默认初始化大类资产池定义映射
        cycle_rb_rules: JSON.parse(JSON.stringify(DEFAULT_MAJOR_CYCLE_RB_RULES)) // 默认初始化大类资产配额字典
      },
      /** @property {string} feePreset - 调仓费率预设下拉选项绑定值 ('0.0003', 'custom' 等) */
      feePreset: '0.0003',
      /** @property {number} customFeePercent - 自定义调仓费率百分比 (单位 %, 默认 0.03 即万三) */
      customFeePercent: 0.03,
      /** @property {Object} metrics - 后端计算返回的核心业绩指标摘要数据 */
      metrics: {},
      /** @property {Array} annualTable - 分年度收益表现、基准对比与最大回撤表格数据 */
      annualTable: [],
      /** @property {Array} navSeries - 日频累计净值走势序列（策略净值、等权基准净值、动态回撤、单资产净值等） */
      navSeries: [],
      /** @property {Array} allocationSeries - 历史动态资产持仓权重演变序列（用于堆叠面积图） */
      allocationSeries: [],
      /** @property {Array} cycleSpans - 历史宏观周期的起始与结束时间区间片段（用于图表背景颜色遮罩） */
      cycleSpans: [],
      /** @property {Object} charts - ECharts 实例引用缓存字典 */
      charts: {
        nav: null,        // 净值走势图
        drawdown: null,   // 水下回撤图
        allocation: null, // 仓位演变堆叠面积图
        annual: null      // 分年度表现对比柱状图
      }
    }
  },
  computed: {
    /**
     * 计算并格式化核心业绩指标卡片列表 (KPI Dashboard)
     * 将后端返回的原始数字加工为带有正负号、百分比以及红涨绿跌色彩样式的卡片视图
     * @returns {Array<Object>} 格式化后的 KPI 指标项数组
     */
    kpiList() {
      if (!this.metrics || this.metrics.total_return === undefined) return []
      const m = this.metrics
      return [
        {
          title: '累计收益率',
          value: m.total_return.toFixed(2) + '%',
          colorClass: m.total_return > 0 ? 'kpi-red' : 'kpi-green'
        },
        {
          title: '年化复合收益 (CAGR)',
          value: m.cagr.toFixed(2) + '%',
          colorClass: m.cagr > 0 ? 'kpi-red' : 'kpi-green',
          subText: '基准 CAGR',
          subValue: m.eq_cagr.toFixed(2) + '%'
        },
        {
          title: '最大回撤 (MDD)',
          value: m.max_drawdown.toFixed(2) + '%',
          colorClass: 'kpi-green',
          subText: '基准 MDD',
          subValue: m.eq_max_drawdown.toFixed(2) + '%'
        },
        {
          title: '夏普比率 (Sharpe)',
          value: m.sharpe.toFixed(2),
          colorClass: 'kpi-blue',
          subText: '卡玛比率',
          subValue: m.calmar.toFixed(2)
        },
        {
          title: '年化波动率',
          value: m.ann_vol.toFixed(2) + '%',
          colorClass: 'kpi-gray'
        },
        {
          title: '日度胜率 (vs基准)',
          value: m.win_rate.toFixed(2) + '%',
          colorClass: m.win_rate > 50 ? 'kpi-red' : 'kpi-gray'
        },
        {
          title: '年均换手率',
          value: m.annual_turnover.toFixed(2) + '%',
          colorClass: 'kpi-gray',
          subText: '调仓 / 累计磨损',
          subValue: `${this.metrics.rebalance_count || '--'} 次 (${m.total_fee_cost !== undefined ? m.total_fee_cost.toFixed(2) + '%' : '--'})`
        },
        {
          title: '信息比率 (IR)',
          value: (m.ir !== undefined ? m.ir : 0).toFixed(2),
          colorClass: (m.ir || 0) > 0 ? 'kpi-red' : ((m.ir || 0) < 0 ? 'kpi-blue' : 'kpi-gray'),
          subText: '跟踪误差',
          subValue: m.tracking_error !== undefined ? m.tracking_error.toFixed(2) + '%' : '--'
        }
      ]
    }
  },
  mounted() {
    // 监听来自上方 DynamicRiskBudget 组件触发的 'sync-backtest' 全局同步事件
    this.$bus.$on('sync-backtest', this.handleSyncBacktest)
    // 监听浏览器视口 resize 事件，自适应刷新所有回测图表尺寸
    window.addEventListener('resize', this.resizeCharts)

    // 页面初始化展示时默认调用大类资产模式回测接口并展示回测信息
    this.$nextTick(() => {
      this.runBacktest()
    })
  },
  beforeDestroy() {
    // 组件销毁前注销 EventBus 事件，防止内存泄漏或多次触发
    this.$bus.$off('sync-backtest', this.handleSyncBacktest)
    window.removeEventListener('resize', this.resizeCharts)
    // 销毁所有 ECharts 实例，彻底释放 GPU 与 Canvas 内存
    this.disposeCharts()
  },
  methods: {
    /**
     * 响应上方组件传递的同步参数事件
     * 接收资产池与各周期风险预算配额，自动更新回测表单并立即触发回测求解
     * @param {Object} payload - 包含 type, asset_pool, cycle_rb_rules 的载荷对象
     */
    handleSyncBacktest(payload) {
      if (payload) {
        this.form.type = payload.type || 'major'
        this.form.asset_pool = payload.asset_pool || {}
        this.form.cycle_rb_rules = payload.cycle_rb_rules || {}
        this.runBacktest()
      }
    },
    /**
     * 标的类型切换响应（大类资产 / 行业板块）
     */
    onTypeChange(val) {
      if (val === 'sector') {
        this.form.asset_pool = JSON.parse(JSON.stringify(DEFAULT_SECTOR_ASSET_POOL))
        this.form.cycle_rb_rules = JSON.parse(JSON.stringify(DEFAULT_SECTOR_CYCLE_RB_RULES))
      } else {
        this.form.asset_pool = JSON.parse(JSON.stringify(DEFAULT_MAJOR_ASSET_POOL))
        this.form.cycle_rb_rules = JSON.parse(JSON.stringify(DEFAULT_MAJOR_CYCLE_RB_RULES))
      }
      this.runBacktest()
    },
    /**
     * 调仓费率预设下拉项切换响应
     * @param {string} val - 选中的预设值或 'custom'
     */
    onFeePresetChange(val) {
      if (val === 'custom') {
        this.form.transaction_cost = Number(((this.customFeePercent || 0) / 100).toFixed(6))
      } else {
        this.form.transaction_cost = parseFloat(val)
      }
    },
    /**
     * 自定义调仓费率输入变更响应
     * @param {number} val - 用户输入的百分比数值 (例如 0.03 代表 0.03%)
     */
    onCustomFeeChange(val) {
      this.form.transaction_cost = Number(((val || 0) / 100).toFixed(6))
    },
    /**
     * 日期范围选择器变更回调
     * @param {Array<string>} val - ['YYYY-MM-DD', 'YYYY-MM-DD']
     */
    onDateRangeChange(val) {
      if (val && val.length === 2) {
        this.form.start_date = val[0]
        this.form.end_date = val[1]
      }
    },
    /**
     * 执行回测主计算流程
     * 1. 校验资产池是否已有效配置；
     * 2. 底层统一查询资产及行业收益率纵表 stock_returns；
     * 3. 组装请求体并异步 POST 至后端回测服务 /api/dynamic-risk-budget/backtest；
     * 4. 解析返回的指标卡、年化表、日频净值、仓位演变与周期划分，并触发 ECharts 绘制。
     */
    async runBacktest() {
      // 基础前置参数校验
      if (!this.form.asset_pool || Object.keys(this.form.asset_pool).length === 0) {
        this.$message.warning('请先在上方配置资产池并同步到回测引擎！')
        return
      }

      this.loading = true
      
      // 保证提交的 transaction_cost 与当前界面输入严格同步
      if (this.feePreset === 'custom') {
        this.form.transaction_cost = Number(((this.customFeePercent || 0) / 100).toFixed(6))
      } else {
        this.form.transaction_cost = parseFloat(this.feePreset)
      }

      // 底层统一使用合并后的纵表 stock_returns
      const payload = {
        asset_pool: this.form.asset_pool,
        cycle_rb_rules: this.form.cycle_rb_rules,
        data_table: 'stock_returns',
        start_date: this.form.start_date,
        end_date: this.form.end_date,
        rebalance_freq: this.form.rebalance_freq,
        transaction_cost: this.form.transaction_cost
      }

      try {
        const apiHost = window.location.hostname || 'localhost'
        const res = await axios.post(`http://${apiHost}:8000/api/dynamic-risk-budget/backtest`, payload)
        if (res.data && res.data.success) {
          const result = res.data.data
          // 提取核心指标、分年度统计、日度净值、动态仓位与周期切片
          this.metrics = result.raw_metrics || {}
          this.annualTable = result.annual_table
          this.navSeries = result.nav_series
          this.allocationSeries = result.allocation_series
          this.cycleSpans = result.cycle_spans || []
          this.metrics.rebalance_count = result.rebalances_count
          
          this.hasRun = true
          // 在 DOM 更新后统一重绘 4 组 ECharts 图表，并配合多重延时 resize 保证自适应展开
          this.$nextTick(() => {
            this.renderCharts()
            this.resizeCharts()
            setTimeout(() => {
              this.resizeCharts()
            }, 150)
            setTimeout(() => {
              this.resizeCharts()
            }, 400)
          })
          this.$message.success('回测测算完成！')
        } else {
          throw new Error(res.data?.message || res.data?.error || '返回数据为空或格式不正确')
        }
      } catch (error) {
        console.error("Backtest failed", error)
        this.$message.error('回测执行失败: ' + (error.response?.data?.message || error.response?.data?.error || error.message))
      } finally {
        this.loading = false
      }
    },
    
    // ================= 图表渲染与生命周期管理 ================= //
    /**
     * 销毁所有已实例化的 ECharts 对象，释放内存资源
     */
    disposeCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) chart.dispose()
      })
    },
    /**
     * 响应视口重设尺寸，驱动全部图表容器平滑重绘
     */
    resizeCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) chart.resize()
      })
    },
    /**
     * 构建 ECharts 的宏观经济周期 markArea 背景色块配置
     * 特性：支持像素级动态宽度检测（利用 chart.convertToPixel 测量当前可视像素宽度）：
     * - 当区块可视像素宽度 >= 50px 时：正常展示中文周期名称（如“信用扩张”）；
     * - 当缩放后时间跨度很窄、可视像素宽度 < 50px 时：自动隐藏文字，防止文字重叠混乱。
     * @param {Object} [chart] - ECharts 实例对象
     * @returns {Array} markArea 数据项配置数组
     */
    buildMarkArea(chart) {
      if (!this.cycleSpans || this.cycleSpans.length === 0) return []
      
      const CYCLE_COLOR_MAP = {
        "阶段1-信用扩张": "#E3F2FD",
        "阶段2-经济复苏": "#E8F5E9",
        "阶段3-货币退潮": "#FFF3E0",
        "阶段4-信用退潮": "#FFEBEE",
        "阶段5-经济放缓": "#F3E5F5",
        "阶段6-货币扩张": "#E0F7FA"
      }
      
      const CYCLE_TEXT_COLOR_MAP = {
        "阶段1-信用扩张": "#1976D2",
        "阶段2-经济复苏": "#D32F2F",
        "阶段3-货币退潮": "#E64A19",
        "阶段4-信用退潮": "#7F8C8D",
        "阶段5-经济放缓": "#2C3E50",
        "阶段6-货币扩张": "#388E3C"
      }
      
      let markAreaData = []
      this.cycleSpans.forEach(span => {
        let showText = false;
        if (chart && typeof chart.convertToPixel === 'function') {
          try {
            const p1 = chart.convertToPixel({ xAxisIndex: 0 }, span.start);
            const p2 = chart.convertToPixel({ xAxisIndex: 0 }, span.end);
            if (typeof p1 === 'number' && typeof p2 === 'number' && !isNaN(p1) && !isNaN(p2)) {
              const widthPx = Math.abs(p2 - p1);
              showText = widthPx >= 50; // 可视像素宽度 >= 50px 时展示阶段中文标签
            } else {
              showText = true;
            }
          } catch (e) {
            showText = true;
          }
        } else {
          showText = true;
        }

        const stageName = span.cycle.split('-')[1] || span.cycle
        markAreaData.push([
          { 
            name: showText ? stageName : '',
            xAxis: span.start, 
            itemStyle: { color: CYCLE_COLOR_MAP[span.cycle] || '#FAFAFA', opacity: 0.5 },
            label: { show: true, position: 'insideTop', color: CYCLE_TEXT_COLOR_MAP[span.cycle] || '#333', fontWeight: 'bold' }
          },
          { xAxis: span.end }
        ])
      })
      return markAreaData
    },
    /**
     * 为图表绑定防抖缩放 (datazoom) 事件监听
     * 当用户拖动下方时间滑块时，防抖 30ms 重新测算并刷新背景周期的文字可见性
     * @param {Object} chart - ECharts 实例对象
     */
    bindZoomHandler(chart) {
      if (!chart) return;
      if (chart._hasZoomBound) return;
      chart._hasZoomBound = true;

      let zoomTimer = null;
      chart.on('datazoom', () => {
        if (zoomTimer) clearTimeout(zoomTimer);
        zoomTimer = setTimeout(() => {
          this.refreshChartMarkArea(chart);
        }, 30);
      });
    },
    /**
     * 局部高效更新图表中的 markArea 背景色块配置
     * @param {Object} chart - ECharts 实例对象
     */
    refreshChartMarkArea(chart) {
      if (!chart) return;
      const markAreaData = this.buildMarkArea(chart);
      chart.setOption({
        series: [
          {
            markArea: {
              data: markAreaData
            }
          }
        ]
      });
    },
    
    /**
     * 统一渲染回测全部 4 组可视化图表
     * 1. 策略净值走势图 (NAV 图表)
     * 2. 水下动态回撤图 (Drawdown 图表)
     * 3. 历史动态仓位分布图 (Allocation 堆叠面积图)
     * 4. 策略分年度表现对比柱状图 (Annual 图表)
     */
    renderCharts() {
      if (!this.hasRun) return
      
      const dates = this.navSeries.map(d => d.date)
      const stratNav = this.navSeries.map(d => d.strat_nav)
      const eqNav = this.navSeries.map(d => d.eq_nav)
      const drawdown = this.navSeries.map(d => d.drawdown)
      const markArea = this.buildMarkArea()

      // ================= 1. 策略累计净值走势图 (NAV) =================
      if (!this.charts.nav) this.charts.nav = echarts.init(this.$refs.navChart)
      
      const STRAT_COLOR = '#D32F2F'
      const BENCH_COLOR = '#1976D2'
      const assetColors = ["#E65100", "#2E7D32", "#F57F17", "#6A1B9A", "#00838F", "#C2185B"]

      let seriesList = [
        {
          name: '动态风险预算策略',
          type: 'line',
          data: stratNav,
          color: STRAT_COLOR,
          itemStyle: { color: STRAT_COLOR },
          lineStyle: { width: 2.2, color: STRAT_COLOR },
          showSymbol: false,
          markArea: { data: markArea },
          z: 5
        },
        {
          name: '等权基准',
          type: 'line',
          data: eqNav,
          color: BENCH_COLOR,
          itemStyle: { color: BENCH_COLOR },
          lineStyle: { width: 1.6, type: 'dashed', color: BENCH_COLOR },
          showSymbol: false,
          z: 4
        }
      ]
      let legendData = ['动态风险预算策略', '等权基准']
      
      const assetKeys = Object.keys(this.form.asset_pool)
      assetKeys.slice(0, 2).forEach((key, idx) => {
        const name = this.form.asset_pool[key].name || key
        const aColor = assetColors[idx % assetColors.length]
        // 保留与 xAxis 日期数组等长，切勿 filter 丢弃 null，避免时序数据错位
        const assetNavData = this.navSeries.map(d => (d.asset_navs && d.asset_navs[key] !== undefined && d.asset_navs[key] !== null) ? d.asset_navs[key] : null)
        if (assetNavData.some(v => v !== null)) {
          seriesList.push({
            name: name + ' (单资产)',
            type: 'line',
            data: assetNavData,
            color: aColor,
            itemStyle: { color: aColor },
            lineStyle: { width: 1.2, type: 'dotted', color: aColor, opacity: 0.8 }, 
            connectNulls: true,
            showSymbol: false,
            z: 3
          })
          legendData.push(name + ' (单资产)')
        }
      })

      this.charts.nav.setOption({
        color: seriesList.map(s => s.color),
        tooltip: { 
          trigger: 'axis',
          formatter: function(params) {
            let html = `<div style="font-size: 12px; margin-bottom: 6px; font-weight: bold; color: #334155;">${params[0].name}</div>`;
            params.forEach(p => {
              const val = typeof p.value === 'number' ? p.value.toFixed(4) : (p.value !== null && p.value !== undefined ? p.value : '--');
              html += `<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 12px; line-height: 20px;">
                <span>${p.marker} <span style="color: #475569;">${p.seriesName}</span></span>
                <span style="font-weight: bold; color: #1e293b; font-family: monospace;">${val}</span>
              </div>`;
            });
            return html;
          }
        },
        legend: { data: legendData, left: 'center', top: 5, type: 'scroll' },
        grid: { left: '3%', right: '4%', bottom: '12%', top: 55, containLabel: true },
        dataZoom: [{ type: 'slider', show: true, bottom: 5, start: 0, end: 100 }],
        xAxis: { type: 'category', boundaryGap: false, data: dates },
        yAxis: { type: 'value', min: 'dataMin' },
        series: seriesList
      }, true)

      // ================= 2. 水下动态回撤图 (Drawdown 图表) =================
      // 展示策略与基准从历史最高净值回落的百分比走势（0% 轴以下，负向填充半透明渐变红阴影）
      if (!this.charts.drawdown) this.charts.drawdown = echarts.init(this.$refs.drawdownChart)
      
      const eqDrawdown = this.navSeries.map(d => d.eq_drawdown)
      
      let ddSeriesList = [
        {
          name: '策略动态回撤',
          type: 'line',
          data: drawdown,
          color: STRAT_COLOR,
          itemStyle: { color: STRAT_COLOR },
          lineStyle: { width: 1.6, color: STRAT_COLOR },
          showSymbol: false,
          z: 5,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(211, 47, 47, 0.35)' },
              { offset: 1, color: 'rgba(211, 47, 47, 0.05)' }
            ])
          }
        },
        {
          name: '等权基准回撤',
          type: 'line',
          data: eqDrawdown,
          color: BENCH_COLOR,
          itemStyle: { color: BENCH_COLOR },
          lineStyle: { width: 1.4, type: 'dashed', color: BENCH_COLOR },
          showSymbol: false,
          z: 4
        }
      ]
      
      let ddLegendData = ['策略动态回撤', '等权基准回撤']
      
      // 提取资产池前两大代表资产的单资产回撤作为参照
      assetKeys.slice(0, 2).forEach((key, idx) => {
        const name = this.form.asset_pool[key].name || key
        const aColor = assetColors[idx % assetColors.length]
        const assetDrawdownData = this.navSeries.map(d => (d.asset_drawdowns && d.asset_drawdowns[key] !== undefined && d.asset_drawdowns[key] !== null) ? d.asset_drawdowns[key] : null)
        if (assetDrawdownData.some(v => v !== null)) {
          ddSeriesList.push({
            name: name + ' (单资产回撤)',
            type: 'line',
            data: assetDrawdownData,
            color: aColor,
            itemStyle: { color: aColor },
            lineStyle: { width: 1.2, type: 'dotted', color: aColor, opacity: 0.8 },
            connectNulls: true,
            showSymbol: false,
            z: 3
          })
          ddLegendData.push(name + ' (单资产回撤)')
        }
      })

      this.charts.drawdown.setOption({
        color: ddSeriesList.map(s => s.color),
        tooltip: { 
          trigger: 'axis',
          formatter: function(params) {
            let html = `<div style="font-size: 12px; margin-bottom: 6px; font-weight: bold; color: #334155;">${params[0].name}</div>`;
            params.forEach(p => {
              const val = typeof p.value === 'number' ? p.value.toFixed(2) + '%' : (p.value !== null && p.value !== undefined ? p.value + '%' : '--');
              html += `<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 12px; line-height: 20px;">
                <span>${p.marker} <span style="color: #475569;">${p.seriesName}</span></span>
                <span style="font-weight: bold; color: #1e293b; font-family: monospace;">${val}</span>
              </div>`;
            });
            return html;
          }
        },
        legend: { data: ddLegendData, left: 'center', top: 5, type: 'scroll' },
        grid: { left: '3%', right: '4%', bottom: '5%', top: 35, containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: dates },
        yAxis: { type: 'value', max: 0, axisLabel: { formatter: '{value}%' } },
        series: ddSeriesList
      }, true)

      // ================= 3. 历史动态仓位分布图 (Allocation 堆叠面积图) =================
      // 各资产权重纵向累加为 100%，直观展示宏观周期切换驱动的资产轮动过程
      if (!this.charts.allocation) this.charts.allocation = echarts.init(this.$refs.allocationChart)
      
      const isSector = this.form.type === 'sector'
      const palette = isSector ? SECTOR_PALETTE : MAJOR_PALETTE
      const allocDates = this.allocationSeries.map(d => d.date)
      const allocSeries = assetKeys.map((key, idx) => {
        const assetName = this.form.asset_pool[key].name || key
        const color = ASSET_COLOR_MAP[assetName] || palette[idx % palette.length]
        return {
          name: assetName,
          type: 'line',
          stack: 'Total',
          itemStyle: { color: color },
          lineStyle: { width: 1.0, color: color },
          areaStyle: {
            color: color,
            opacity: 0.90
          },
          emphasis: {
            focus: 'series',
            areaStyle: { opacity: 0.98 }
          },
          showSymbol: false,
          data: this.allocationSeries.map(d => d.weights[key])
        }
      })

      this.charts.allocation.setOption({
        color: allocSeries.map(s => s.itemStyle.color),
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'line',
            lineStyle: {
              color: '#94a3b8',
              type: 'dashed'
            }
          },
          formatter: function(params) {
            let html = `<div style="font-size: 12px; margin-bottom: 6px; font-weight: bold; color: #334155;">${params[0].name} 动态仓位分布</div>`;
            const list = [...params].reverse();
            list.forEach(p => {
              const val = typeof p.value === 'number' ? p.value.toFixed(2) : (p.value || '0.00');
              html += `<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 12px; line-height: 22px;">
                <span>${p.marker} <span style="color: #475569;">${p.seriesName}</span></span>
                <span style="font-weight: bold; color: #1e293b; font-family: monospace;">${val}%</span>
              </div>`;
            });
            return html;
          }
        },
        legend: {
          type: 'scroll',
          left: 'center',
          top: 5,
          data: assetKeys.map(k => this.form.asset_pool[k].name || k),
          textStyle: { color: '#475569', fontSize: 12 }
        },
        grid: { left: '3%', right: '4%', bottom: '12%', top: 45, containLabel: true },
        dataZoom: [{ type: 'slider', show: true, bottom: 5, start: 0, end: 100 }],
        xAxis: { type: 'category', boundaryGap: false, data: allocDates },
        yAxis: {
          type: 'value',
          max: 100,
          axisLabel: { formatter: '{value}%' }
        },
        series: allocSeries
      }, true) // 传入 true 清除旧系列数据（切换大类/板块模式时避免数据残留）
      
      // 多图表联动缩放：将净值走势图、回撤图、仓位分布图的时间滑块进行 1:1 轴向联动
      echarts.connect([this.charts.nav, this.charts.drawdown, this.charts.allocation])
      
      // ================= 4. 策略分年度表现对比图表 (Annual 图表) =================
      // 包含策略收益柱、等权基准柱、超额收益折线、年内最大回撤虚线
      if (!this.charts.annual) this.charts.annual = echarts.init(this.$refs.annualChart)
      
      const years = this.annualTable.map(d => d['年份'])
      const stratReturns = this.annualTable.map(d => parseFloat(d['策略净值收益'].replace('%', '')))
      const eqReturns = this.annualTable.map(d => parseFloat(d['等权基准'].replace('%', '')))
      const excessReturns = this.annualTable.map(d => parseFloat(d['超额收益'].replace('%', '')))
      const maxDrawdowns = this.annualTable.map(d => parseFloat(d['策略年内最大回撤'].replace('%', '')))
      
      this.charts.annual.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: function(params) {
            let html = `<div style="font-size: 12px; margin-bottom: 5px; color: #64748b; font-weight: bold;">${params[0].name}年度表现</div>`;
            params.forEach(p => {
              let isDrawdown = p.seriesName.includes('回撤');
              let color = p.value > 0 ? '#ef4444' : (p.value < 0 ? '#10b981' : '#64748b');
              if (isDrawdown) color = '#10b981'; // 回撤属于下行风险指标，采用绿色标示
              let weight = p.seriesName === '超额收益' ? 'bold' : 'normal';
              let sign = (p.value > 0 && !isDrawdown) ? '+' : '';
              html += `<div>${p.marker} ${p.seriesName}: <span style="font-weight:${weight}; color:${color}">${sign}${p.value}%</span></div>`;
            });
            return html;
          }
        },
        legend: { data: ['策略收益', '等权基准', '超额收益', '年内最大回撤'], left: 'center', top: 5 },
        grid: { left: '3%', right: '4%', bottom: '5%', top: 40, containLabel: true },
        xAxis: { type: 'category', data: years, axisPointer: { type: 'shadow' } },
        yAxis: { type: 'value', axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [
          {
            name: '策略收益',
            type: 'bar',
            barGap: '10%',
            barMaxWidth: 25,
            itemStyle: { color: '#ef4444', borderRadius: [3, 3, 0, 0], opacity: 0.85 },
            data: stratReturns
          },
          {
            name: '等权基准',
            type: 'bar',
            barMaxWidth: 25,
            itemStyle: { color: '#3b82f6', borderRadius: [3, 3, 0, 0], opacity: 0.85 },
            data: eqReturns
          },
          {
            name: '超额收益',
            type: 'line',
            symbol: 'emptyCircle',
            symbolSize: 6,
            itemStyle: { color: '#f59e0b' },
            lineStyle: { width: 2 },
            data: excessReturns
          },
          {
            name: '年内最大回撤',
            type: 'line',
            symbol: 'diamond',
            symbolSize: 6,
            itemStyle: { color: '#10b981' },
            lineStyle: { width: 1.5, type: 'dotted' },
            data: maxDrawdowns
          }
        ]
      }, true)
      
      // 配置动态周期区域标签 (markArea 动态文本响应)
      this.bindZoomHandler(this.charts.nav)
      this.$nextTick(() => {
        this.refreshChartMarkArea(this.charts.nav)
        this.resizeCharts()
      })
    }
  }
}
</script>

<style scoped>
.risk-budget-backtest-container {
  width: 100%;
  box-sizing: border-box;
}
.empty-state {
  padding: 40px 0;
  background-color: #f8fafc;
  border-radius: 8px;
}
.kpi-panel {
  display: flex;
  flex-wrap: wrap;
}

/* 彻底覆盖内网全局针对 .el-col-6 强加的 height: 69px !important 限制 */
.risk-budget-backtest-container .kpi-panel .el-col,
.risk-budget-backtest-container .kpi-panel .el-col-6,
.risk-budget-backtest-container .kpi-col {
  height: auto !important;
  min-height: 110px !important;
  box-sizing: border-box;
}

.kpi-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 15px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
  transition: transform 0.2s;
  box-sizing: border-box;
  min-height: 95px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.kpi-title {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 6px;
  line-height: 1.2;
}
.kpi-sub {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}
.kpi-sub span {
  font-weight: 500;
  color: #475569;
}
.kpi-red .kpi-value { color: #ef4444; }
.kpi-green .kpi-value { color: #10b981; }
.kpi-blue .kpi-value { color: #3b82f6; }
.kpi-gray .kpi-value { color: #475569; }

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 250px;
}
.annual-table-wrapper {
  margin-top: 20px;
}
.fw-bold {
  font-weight: bold;
}

/* 回测结果区域撑开保证 — 显式声明最小总高度，彻底杜绝被内网父容器压扁 */
.backtest-results {
  width: 100%;
  min-height: 1600px;
  display: block;
}

/* 图表区 section 标题 */
.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-title-md {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.mb-10 {
  margin-bottom: 10px;
}

/* chart-wrapper 撑高保证 — 防止在 overflow:hidden 容器下被压缩 */
.chart-wrapper {
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

/* 兼容内网：el-col 样式强化，禁用 flex 收缩并保证内容撑开 */
.risk-budget-backtest-container .el-col {
  box-sizing: border-box;
  flex: none !important;
}

.el-col .chart-wrapper {
  overflow: visible;
}

/* 穿透覆盖 el-card__body，确保在回测渲染后高度顺畅自适应延展 */
/deep/ .el-card__body {
  overflow: visible !important;
  height: auto !important;
}
.box-card /deep/ .el-card__body {
  overflow: visible;
}
</style>
