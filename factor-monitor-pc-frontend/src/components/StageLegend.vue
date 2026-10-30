<template>
  <div class="stage-legend-container">
    <!-- 顶部全局标题栏 -->
    <div v-if="showHeader" class="app-header-bar">
      <div class="header-title-wrapper">
        <h2 class="app-title-text">三因子宏观经济周期划分的风险预算资产配置模型</h2>
        <el-tooltip effect="dark" placement="bottom">
          <div slot="content" style="max-width: 460px; line-height: 1.6; font-size: 13px;">
            先基于三因子判断该时期的经济处于宏观周期中的哪个阶段，再根据该阶段下各类资产/板块的长期风险收益特征，用风险预算模型计算出最优仓位。
          </div>
          <i class="el-icon-question header-help-icon"></i>
        </el-tooltip>
      </div>
    </div>

    <!-- 主体内容区域 -->
    <div class="stage-content-body">
      <!-- 第一层级：宏观周期概况与阶段推荐 -->
    <el-row :gutter="20" type="flex" align="stretch" class="mb-20">
      <!-- 左侧：宏观周期概况 -->
      <el-col :span="12" class="flex-col-container" style="min-height: 320px;">
        <transition name="el-fade-in">
          <div class="recommendations-panel macro-summary-panel flex-1-col" v-loading="loading">
            <div class="rec-header">
              <div class="rec-title-group">
                <span class="rec-title">宏观周期概况</span>
                <el-tooltip effect="dark" content="当前截止日期下的三因子状态解读" placement="top-start">
                  <i class="el-icon-question help-icon"></i>
                </el-tooltip>
              </div>
              <el-tag v-if="latestMacro && latestMacro.tradeDate" size="mini" type="info" effect="plain" class="header-date-tag">
                <i class="el-icon-date"></i> 截止日期: {{ latestMacro.tradeDate }}
              </el-tag>
            </div>
            <template v-if="latestMacro">
              <div class="macro-inner-box">
                <!-- 左侧文本与六周期状态区 -->
                <div class="macro-text-part">
                  <div class="macro-stage-title">
                    <span>宏观六周期</span>
                    <el-tooltip effect="dark" placement="top-start">
                      <div slot="content" style="max-width: 520px; line-height: 1.6; font-size: 12px;">
                        <div style="font-weight: bold; margin-bottom: 4px;">中国经济六周期阶段划分：</div>
                        <div>1.信用扩张：货币持续宽松，借贷成本降低，投资和消费信心逐渐恢复，促进信用开始扩张；</div>
                        <div>2.经济复苏：货币供应充裕，信贷市场活跃，推动了经济的快速发展，投资和消费活动增加，经济整体处于高速增长的繁荣状态；</div>
                        <div>3.货币退潮：经济发展逐渐过热，信贷活动仍然活跃，为了平衡经济增长或抑制通胀，货币政策开始调整收紧；</div>
                        <div>4.信用退潮：货币供应持续紧缩，借贷成本增加，市场流动性紧缺，信贷活动开始减少；</div>
                        <div>5.经济放缓：信用退潮导致经济疲软，投资和消费活动减少，经济增长逐步放缓；</div>
                        <div>6.货币扩张：经济不确定性较高，信贷需求仍然较弱，货币政策采取宽松措施以刺激信贷活动和经济增长。</div>
                      </div>
                      <i class="el-icon-question help-icon"></i>
                    </el-tooltip>
                  </div>
                  <div class="macro-cycles-wrapper">
                    <!-- 6个周期横向展示 -->
                    <div class="stage-cycles-grid">
                      <div
                        v-for="stage in stageDefinitions"
                        :key="stage.id"
                        class="cycle-pill"
                        :class="{ 'is-active': latestMacro.stage === stage.id }"
                        :style="getCycleItemStyle(stage)"
                      >
                        <span class="cycle-pill-num">{{ stage.id }}</span>
                        <span class="cycle-pill-name">{{ stage.name }}</span>
                        <i v-if="latestMacro.stage === stage.id" class="el-icon-check active-check-icon"></i>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 右侧仪表盘区 -->
                <div class="macro-gauges-part">
                  <div class="macro-stage-title">
                    <span>三因子</span>
                    <el-tooltip effect="dark" placement="top-start">
                      <div slot="content" style="max-width: 500px; line-height: 1.6; font-size: 12px;">
                        <div style="font-weight: bold; margin-bottom: 4px;">货币-信用-增长三因子设计：</div>
                        <div>1.货币：货币传导从央行的货币投放开始，传导至银行端，其周期性体现为货币政策的放宽与收紧，看货币政策工具的边际变化扩散指数；</div>
                        <div>2.信用：进一步传导到实体需要通过银行与实体部门间的借贷行为，其周期性体现为信贷的扩张与收缩，看中长期贷款脉冲的季度变化；</div>
                        <div>3.增长：借贷资金流入实体后在各部门间循环流通，其周期性体现为实体部门生产、消费等经济活动的扩张与收缩，看PMI脉冲的季度变化。</div>
                      </div>
                      <i class="el-icon-question help-icon"></i>
                    </el-tooltip>
                  </div>
                  <div class="macro-gauges-row">
                    <div class="gauge-wrapper">
                      <div ref="gaugeMoney" class="gauge-chart"></div>
                      <div v-if="gaugeFactors.length" class="gauge-title">
                        货币 <span :class="gaugeFactors[0].colorClass">{{ gaugeFactors[0].text }} <i :class="gaugeFactors[0].iconClass"></i></span>
                      </div>
                    </div>
                    <div class="gauge-wrapper">
                      <div ref="gaugeCredit" class="gauge-chart"></div>
                      <div v-if="gaugeFactors.length" class="gauge-title">
                        信用 <span :class="gaugeFactors[1].colorClass">{{ gaugeFactors[1].text }} <i :class="gaugeFactors[1].iconClass"></i></span>
                      </div>
                    </div>
                    <div class="gauge-wrapper">
                      <div ref="gaugeGrowth" class="gauge-chart"></div>
                      <div v-if="gaugeFactors.length" class="gauge-title">
                        增长 <span :class="gaugeFactors[2].colorClass">{{ gaugeFactors[2].text }} <i :class="gaugeFactors[2].iconClass"></i></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- AI 文字总结与警醒提示区 -->
              <div class="macro-ai-summary-box">
                <div class="ai-summary-content">
                  <div class="ai-summary-item">
                    <span class="factor-badge">1</span><strong class="factor-name">货币端：</strong><span>{{ currentPringSummary.money }}</span>
                  </div>
                  <div class="ai-summary-item">
                    <span class="factor-badge">2</span><strong class="factor-name">信用端：</strong><span>{{ currentPringSummary.credit }}</span>
                  </div>
                  <div class="ai-summary-item">
                    <span class="factor-badge">3</span><strong class="factor-name">增长端：</strong><span>{{ currentPringSummary.growth }}</span>
                  </div>
                </div>
                <div class="ai-summary-divider"></div>
                <div class="ai-summary-disclaimer">
                  <i class="el-icon-warning-outline disclaimer-icon"></i>
                  <span>AI生成内容，请仔细甄别。</span>
                </div>
              </div>
            </template>
            <div v-else-if="!loading" style="flex: 1; display: flex; align-items: center; justify-content: center; min-height: 250px; color: #909399;">
              <i class="el-icon-info" style="margin-right: 6px;"></i> 暂无宏观周期数据
            </div>
          </div>
        </transition>
      </el-col>
      
      <!-- 右侧：阶段历史表现推荐区 -->
      <el-col :span="12" class="flex-col-container" style="min-height: 320px;">
        <transition name="el-fade-in">
          <div class="recommendations-panel rec-panel-wrapper flex-1-col" v-loading="loading">
            <div class="rec-header">
              <div class="rec-title-group">
                <span class="rec-title">阶段历史表现推荐</span>
                <el-tooltip effect="dark" content="基于全局时间范围与当前宏观阶段历史回测，推荐年化收益表现最好的前三大类资产与前三行业板块" placement="top-start">
                  <i class="el-icon-question help-icon"></i>
                </el-tooltip>
              </div>
              <div class="header-date-filter">
                <span class="date-label"><i class="el-icon-date"></i> 全局时间范围:</span>
                <el-date-picker
                  v-model="currentDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="yyyy-MM-dd"
                  size="mini"
                  :clearable="false"
                  :picker-options="pickerOptions"
                  @change="handleDateRangeChange"
                  class="global-date-picker"
                ></el-date-picker>
              </div>
            </div>
            <el-row v-if="currentStageRecommendations" :gutter="20" class="rec-content flex-1-row" type="flex" align="stretch">
              <el-col :span="12" style="display: flex; flex-direction: column; min-height: 250px;">
                <el-card shadow="never" class="rec-card asset-rec-card h-100" style="display: flex; flex-direction: column; flex: 1; min-height: 250px;">
                  <div slot="header" class="clearfix">
                    <span><i class="el-icon-trophy"></i> 历史当前阶段资产收益（Top3）</span>
                    <el-tooltip effect="dark" content="基于当前所处宏观阶段，历史回测中年化收益率表现最好的前三大类资产" placement="top-start">
                      <i class="el-icon-question help-icon"></i>
                    </el-tooltip>
                  </div>
                  <div class="rec-items" style="flex: 1; display: flex; flex-direction: column; justify-content: space-around;">
                    <div v-for="(item, index) in currentStageRecommendations.assets" :key="index" class="rec-item">
                      <span class="rec-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
                      <span class="rec-name">{{ item.name }}</span>
                      <span class="rec-val" :class="Number(item.value) > 0 ? 'text-danger' : (Number(item.value) < 0 ? 'text-success' : 'text-muted')">
                        {{ formatReturnValue(item.value) }}
                      </span>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12" style="display: flex; flex-direction: column; min-height: 250px;">
                <el-card shadow="never" class="rec-card sector-rec-card h-100" style="display: flex; flex-direction: column; flex: 1; min-height: 250px;">
                  <div slot="header" class="clearfix">
                    <span><i class="el-icon-medal"></i> 历史当前阶段板块收益（Top3）</span>
                    <el-tooltip effect="dark" content="基于当前所处宏观阶段，历史回测中年化超额收益率表现最好的前三行业板块" placement="top-start">
                      <i class="el-icon-question help-icon"></i>
                    </el-tooltip>
                  </div>
                  <div class="rec-items" style="flex: 1; display: flex; flex-direction: column; justify-content: space-around;">
                    <div v-for="(item, index) in currentStageRecommendations.sectors" :key="index" class="rec-item">
                      <span class="rec-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
                      <span class="rec-name">{{ item.name }}</span>
                      <span class="rec-val" :class="Number(item.value) > 0 ? 'text-danger' : (Number(item.value) < 0 ? 'text-success' : 'text-muted')">
                        {{ formatReturnValue(item.value) }}
                      </span>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <div v-else-if="!loading" style="flex: 1; display: flex; align-items: center; justify-content: center; min-height: 250px; color: #909399;">
              <i class="el-icon-info" style="margin-right: 6px;"></i> 暂无当前阶段推荐数据
            </div>
          </div>
        </transition>
      </el-col>
    </el-row>

    <!-- 自定义动态风险预算模型（支持大类资产与行业板块配置及强制配额校验） -->
    <DynamicRiskBudget :global-date-range="currentDateRange" class="mb-20" />

    <!-- 动态风险预算模型回测系统 -->
    <RiskBudgetBacktest class="mb-20" />

    <!-- 第三层级：宏观环境与三因子走势 -->
    <el-card class="box-card mb-20" v-loading="loading">
      <div slot="header" class="clearfix">
        <span class="card-title-lg">宏观环境与三因子</span>
        <el-tooltip effect="dark" content="展示宏观经济六个周期的趋势以及对应的货币、信用、增长三因子的变化情况" placement="top-start">
          <i class="el-icon-question help-icon"></i>
        </el-tooltip>
        <el-tag v-if="dateRangeText" size="mini" type="info" effect="plain" style="float: right; margin-top: 2px;">
          <i class="el-icon-date"></i> {{ dateRangeText }}
        </el-tag>
      </div>
      <el-tabs v-model="activeMacroTab" @tab-click="handleTabClick">
        <el-tab-pane label="综合周期阶段" name="stage">
          <div class="legend-boxes mb-15">
            <div class="legend-item" v-for="(stage, index) in stageDefinitions" :key="index">
              <div class="color-box" :style="{ backgroundColor: stage.color }"></div>
              <div class="stage-info">
                <strong>{{ stage.id }}: {{ stage.name }}</strong>
              </div>
            </div>
          </div>
          <div class="chart-wrapper">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('stageChart', '宏观环境与三因子 - 综合周期阶段', { includeStageLegend: true, fileName: '综合周期阶段' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="stageChart" class="chart-container"></div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="货币因子" name="money">
          <div class="chart-wrapper">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('moneyChart', '宏观环境与三因子 - 货币因子走势', { fileName: '货币因子走势' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="moneyChart" class="chart-container"></div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="信用因子" name="credit">
          <div class="chart-wrapper">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('creditChart', '宏观环境与三因子 - 信用因子走势', { fileName: '信用因子走势' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="creditChart" class="chart-container"></div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="增长因子" name="growth">
          <div class="chart-wrapper">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('growthChart', '宏观环境与三因子 - 增长因子走势', { fileName: '增长因子走势' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="growthChart" class="chart-container"></div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 第四层级：资产与板块收益历史趋势 -->
    <el-row :gutter="20">
      <el-col :span="12" style="min-height: 420px;">
        <el-card class="box-card mb-20" v-loading="loading" style="min-height: 420px;">
          <div slot="header" class="clearfix">
            <span class="card-title">资产收益历史趋势</span>
            <el-tooltip effect="dark" content="各大类资产（如300收益、中证1000等）的累计净值走势，背景颜色代表不同的宏观阶段" placement="top-start">
              <i class="el-icon-question help-icon"></i>
            </el-tooltip>
          </div>
          <div class="chart-wrapper" style="width: 100%; height: 350px; min-height: 350px;">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('assetChart', '资产收益历史趋势', { fileName: '资产收益历史趋势' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="assetChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12" style="min-height: 420px;">
        <el-card class="box-card mb-20" v-loading="loading" style="min-height: 420px;">
          <div slot="header" class="clearfix">
            <span class="card-title">板块超额收益历史趋势</span>
            <el-tooltip effect="dark" content="各中信一级行业板块相对于基准的累计超额收益走势，背景颜色代表不同的宏观阶段" placement="top-start">
              <i class="el-icon-question help-icon"></i>
            </el-tooltip>
          </div>
          <div class="chart-wrapper" style="width: 100%; height: 350px; min-height: 350px;">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn sector-download-btn" @click="exportStatsChart('sectorChart', '板块超额历史趋势', { fileName: '板块超额历史趋势' })">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="sectorChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第五层级：资产与板块年化收益统计 -->
    <el-row :gutter="20">
      <el-col :span="12" style="min-height: 420px;">
        <el-card class="box-card mb-20" v-loading="loading" style="min-height: 420px;">
          <div slot="header" class="clearfix">
            <span class="card-title">资产收益统计 (年化)</span>
            <el-tooltip effect="dark" content="统计不同大类资产在各个宏观阶段的年化收益率" placement="top-start">
              <i class="el-icon-question help-icon"></i>
            </el-tooltip>
            <el-tag v-if="dateRangeText" size="mini" type="info" effect="plain" style="float: right; margin-top: 2px;">
              <i class="el-icon-date"></i> {{ dateRangeText }}
            </el-tag>
          </div>
          <div class="chart-wrapper" style="width: 100%; height: 350px; min-height: 350px;">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn" @click="exportStatsChart('assetStatsChart', '资产收益统计 (年化)')">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="assetStatsChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12" style="min-height: 420px;">
        <el-card class="box-card mb-20" v-loading="loading" style="min-height: 420px;">
          <div slot="header" class="clearfix">
            <span class="card-title">板块超额统计 (年化)</span>
            <el-tooltip effect="dark" content="统计不同行业板块在各个宏观阶段的年化超额收益率" placement="top-start">
              <i class="el-icon-question help-icon"></i>
            </el-tooltip>
            <el-tag v-if="dateRangeText" size="mini" type="info" effect="plain" style="float: right; margin-top: 2px;">
              <i class="el-icon-date"></i> {{ dateRangeText }}
            </el-tag>
          </div>
          <div class="chart-wrapper" style="width: 100%; height: 350px; min-height: 350px;">
            <el-tooltip effect="dark" content="导出为图片" placement="top">
              <div class="dashboard-download-btn sector-download-btn" @click="exportStatsChart('sectorStatsChart', '板块超额统计 (年化)')">
                <i class="el-icon-download"></i>
              </div>
            </el-tooltip>
            <div ref="sectorStatsChart" class="chart-container" style="width: 100%; height: 350px; min-height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    </div>
  </div>
</template>

<script>
/**
 * @file StageLegend.vue
 * @description 三因子宏观经济周期划分与大类资产/行业板块收益监控看板
 * 
 * 【系统架构定位与核心功能】：
 * 本组件作为整个监控系统的一级视图容器，核心功能包括：
 * 1. 宏观经济六周期划分：基于货币（DR007利率）、信用（中长期贷款脉冲）、增长（PMI脉冲）三因子，将宏观周期切分为六大阶段；
 * 2. 实时宏观仪表盘：通过半环形仪表盘实时反映最新交易日的货币松紧、信用扩张/收缩与经济增长方向，并展示对应的普林格阶段研判摘要；
 * 3. 嵌入下级配置与回测引擎：
 *    - <DynamicRiskBudget>: 自定义动态风险预算模型（资产与板块超额建议）；
 *    - <RiskBudgetBacktest>: 动态风险预算历史回测与绩效分析系统；
 * 4. 资产与板块历史走势分析：
 *    - 展示大类资产（300收益、中证1000、中债国债、黄金、转债）与行业板块（中信消费、科技、周期、金融、稳定）的累计净值曲线；
 *    - 曲线背景中融合 macro cycle markArea 背景着色块，并具备 zoom 像素测算动态显隐阶段文字的能力；
 * 5. 年化收益统计柱状图：统计两大资产池在各宏观周期下的历史年化复合收益率与当前最优投资标的推荐；
 * 6. 高分辨率卡片图片导出：通过 2x Canvas 合成包含完整标题栏、日期标签与六周期图例的高清 PNG 报告图片。
 */
import axios from 'axios'
import * as echarts from 'echarts'
import DynamicRiskBudget from './DynamicRiskBudget.vue'
import RiskBudgetBacktest from './RiskBudgetBacktest.vue'

export default {
  name: 'StageLegend',
  components: {
    DynamicRiskBudget,
    RiskBudgetBacktest
  },
  props: {
    showHeader: {
      type: Boolean,
      default: true
    },
    globalDateRange: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      /**
       * 当前组件内部自控的全局交易日期范围 [开始日期, 结束日期]
       * 优先使用父组件传入的 globalDateRange，若未传则在挂载后自驱动拉取并计算近3年时间区间
       */
      currentDateRange: (this.globalDateRange && this.globalDateRange.length === 2)
        ? [...this.globalDateRange]
        : [],
      /** 日期范围快捷筛选配置 */
      pickerOptions: {
        shortcuts: [
          {
            text: '近1年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setFullYear(end.getFullYear() - 1);
              picker.$emit('pick', [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]);
            }
          },
          {
            text: '近3年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setFullYear(end.getFullYear() - 3);
              picker.$emit('pick', [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]);
            }
          },
          {
            text: '近5年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setFullYear(end.getFullYear() - 5);
              picker.$emit('pick', [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]);
            }
          }
        ]
      },
      /** @property {boolean} loading - 全局数据异步加载状态 */
      loading: false,
      /**
       * 宏观经济六周期标准定义表
       * money: 1(宽松)/-1(收紧)
       * credit: 1(扩张)/-1(收缩)
       * growth: 1(繁荣扩张)/-1(下行放缓)
       */
      stageDefinitions: [
        { id: 1, name: '信用扩张', money: 1, credit: 1, growth: -1, color: '#85C1E9' },
        { id: 2, name: '经济复苏', money: 1, credit: 1, growth: 1, color: '#E74C3C' },
        { id: 3, name: '货币退潮', money: -1, credit: 1, growth: 1, color: '#F5B041' },
        { id: 4, name: '信用退潮', money: -1, credit: -1, growth: 1, color: '#AAB7B8' },
        { id: 5, name: '经济放缓', money: -1, credit: -1, growth: -1, color: '#2E86C1' },
        { id: 6, name: '货币扩张', money: 1, credit: -1, growth: -1, color: '#7DCEA0' }
      ],
      /** @property {Array} tableData - 宏观周期阶段日历数据（tradeDate, stage, money, credit, growth） */
      tableData: [],
      /** @property {Array} moneyList - 货币方向因子历史序列（DR007相关） */
      moneyList: [],
      /** @property {Array} creditGrowthList - 信用与增长因子历史序列（贷款脉冲、PMI脉冲等） */
      creditGrowthList: [],
      /** @property {Array} assetReturnsList - 大类资产日频累计净值走势序列 */
      assetReturnsList: [],
      /** @property {Array} sectorReturnsList - 行业板块日频累计超额净值走势序列 */
      sectorReturnsList: [],
      /** @property {Array} assetStatsList - 大类资产在各宏观阶段的年化收益率统计结果 */
      assetStatsList: [],
      /** @property {Array} sectorStatsList - 行业板块在各宏观阶段的年化超额收益率统计结果 */
      sectorStatsList: [],
      /** @property {Object} charts - 组件内部全部 ECharts 实例缓存字典 */
      charts: {},
      /** @property {string} activeMacroTab - 宏观环境走势当前激活标签页 ('stage'|'money'|'credit'|'growth') */
      activeMacroTab: 'stage',
      /**
       * 普林格经济周期六阶段权威研判综述文本字典（用于在卡片中为投资经理提供基本面环境解读）
       */
      pringStageSummaries: {
        1: {
          stageName: '信用扩张',
          money: 'DR007利率低位平稳运行，央行维持适度流动性投放，资金面整体保持合理充裕。',
          credit: '信贷与社融规模企稳回升，企业中长期贷款显著放量，宽信用效能稳步显现，信用扩张动能持续走强。',
          growth: '制造业PMI在收缩区间低位筑底，生产活动初现弱修复迹象，终端有效需求仍在恢复积累中。'
        },
        2: {
          stageName: '经济复苏',
          money: '货币政策维持稳健宽松，流动性保持充裕，政策利率引导实体融资成本稳中有降。',
          credit: '信贷供求两旺，居民与企业中长贷双双保持较好增长，社融增速稳步上行，信用扩张态势稳固。',
          growth: '制造业PMI重回荣枯线以上并加速上行，供需两侧指标共振，新订单指数反弹，经济复苏动能强劲。'
        },
        3: {
          stageName: '货币退潮',
          money: '央行公开市场净回笼，短端资金利率波动加大，DR007中枢有所抬升，流动性边际收敛。',
          credit: '信贷扩张保持较强韧性，企业资本开支需求强劲，信贷增量维持高位，信用端仍处高景气通道。',
          growth: 'PMI处于高位繁荣区间，工业增加值与产能利用率旺盛，经济处于阶段性过热阶段。'
        },
        4: {
          stageName: '信用退潮',
          money: 'DR007震荡。',
          credit: '7月新增社融1.4万亿，新增信贷-0.34万亿，信贷负增，信用扩张动能趋弱。结构上，居民端中长贷(新增-1202亿)和企业中长期(新增-2300亿)均低于市场预期。',
          growth: '7月制造业PMI为49.2，环比下降0.9;非制造业PMI为49，环比下降1.2,PMI超季节性回落。'
        },
        5: {
          stageName: '经济放缓',
          money: '资金面维持中性偏紧，DR007利率围绕政策利率窄幅震荡，央行操作以精准对冲到期为主。',
          credit: '实体信贷需求偏弱，居民加杠杆意愿不足，中长期信贷增速放缓，社融总量承压，信用动能边际收缩。',
          growth: '制造业PMI录于荣枯线下方，新订单与新出口订单指数回落，供需两端景气度承压，经济动能延续放缓。'
        },
        6: {
          stageName: '货币扩张',
          money: '逆周期货币政策发力，降准降息预期升温，流动性充裕宽裕，资金利率显著低于政策利率。',
          credit: '宽货币向宽信用传导仍存时滞，金融机构风险偏好较低，社融与信贷尚未显现持续改善，信用端仍处收缩期。',
          growth: '经济下行压力犹存，内外需延续承压走弱，PMI位于收缩区间寻底，宏观逆周期调节紧迫性提升。'
        }
      }
    }
  },
  watch: {
    /**
     * 监听父组件传入的全局日期范围变动（若存在），同步至内部并触发重新拉取
     */
    globalDateRange: {
      handler(newVal) {
        if (newVal && newVal.length === 2 && JSON.stringify(newVal) !== JSON.stringify(this.currentDateRange)) {
          this.currentDateRange = [...newVal];
          this.fetchAllData();
        }
      },
      deep: true
    }
  },
  computed: {
    /**
     * 获取最新交易日的宏观经济周期数据项
     * @returns {Object|null} 包含 tradeDate, stage, money, credit, growth 的最新对象
     */
    latestMacro() {
      if (this.tableData && this.tableData.length > 0) {
        return this.tableData[this.tableData.length - 1];
      }
      return null;
    },
    /**
     * 将最新宏观三因子的松紧方向转化为半环形仪表盘与卡片标签所需的显示数据
     * 包含货币、信用、增长三因子的中文状态（宽松/收紧、扩张/收缩）、颜色类名与图标
     * @returns {Array<Object>} 仪表盘配置列表
     */
    gaugeFactors() {
      if (!this.latestMacro) return [];
      const m = this.latestMacro;
      return [
        { 
          ref: 'gaugeMoney', name: '货币', value: m.money, 
          text: m.money < 0 ? '收紧' : (m.money > 0 ? '宽松' : '不变'), 
          colorClass: m.money < 0 ? 'text-danger' : (m.money > 0 ? 'text-success' : 'text-muted'),
          iconClass: m.money < 0 ? 'el-icon-bottom' : (m.money > 0 ? 'el-icon-top' : 'el-icon-minus')
        },
        { 
          ref: 'gaugeCredit', name: '信用', value: m.credit, 
          text: m.credit < 0 ? '收缩' : (m.credit > 0 ? '扩张' : '不变'), 
          colorClass: m.credit < 0 ? 'text-danger' : (m.credit > 0 ? 'text-success' : 'text-muted'),
          iconClass: m.credit < 0 ? 'el-icon-bottom' : (m.credit > 0 ? 'el-icon-top' : 'el-icon-minus')
        },
        { 
          ref: 'gaugeGrowth', name: '增长', value: m.growth, 
          text: m.growth < 0 ? '收缩' : (m.growth > 0 ? '扩张' : '不变'), 
          colorClass: m.growth < 0 ? 'text-danger' : (m.growth > 0 ? 'text-success' : 'text-muted'),
          iconClass: m.growth < 0 ? 'el-icon-bottom' : (m.growth > 0 ? 'el-icon-top' : 'el-icon-minus')
        }
      ];
    },
    /**
     * 获取当前最新宏观周期阶段所对应的普林格环境研判综述
     * 提取货币资金面、信用社融脉冲、增长制造业PMI的权威成因分析文本
     */
    currentPringSummary() {
      if (!this.latestMacro) {
        return {
          stageName: '信用退潮',
          money: 'DR007震荡。',
          credit: '7月新增社融1.4万亿，新增信贷-0.34万亿，信贷负增，信用扩张动能趋弱。结构上，居民端中长贷(新增-1202亿)和企业中长期(新增-2300亿)均低于市场预期。',
          growth: '7月制造业PMI为49.2，环比下降0.9;非制造业PMI为49，环比下降1.2,PMI超季节性回落。'
        };
      }
      const stage = this.latestMacro.stage;
      return this.pringStageSummaries[stage] || this.pringStageSummaries[4];
    },
    /**
     * 计算当前宏观阶段下的最优资产与板块投资建议
     * 依据当前宏观阶段（1~6）的历史回测年化收益率进行从大到小降序排序，
     * 自动提取出在该周期下表现最强的前三名资产与前三名行业板块
     * @returns {Object|null} 包含 stageName, stageColor, assets(Top3), sectors(Top3)
     */
    currentStageRecommendations() {
      if (!this.tableData || !this.tableData.length || !this.assetStatsList || !this.assetStatsList.length || !this.sectorStatsList || !this.sectorStatsList.length) return null;
      
      const lastData = this.tableData[this.tableData.length - 1];
      if (!lastData || lastData.stage === undefined || lastData.stage === null) return null;
      const currentStageId = Number(lastData.stage);
      if (!currentStageId) return null;
      
      const stageDef = this.stageDefinitions.find(s => Number(s.id) === currentStageId);
      const stageName = stageDef ? `${stageDef.id}${stageDef.name}` : `阶段${currentStageId}`;
      
      const assetStats = this.assetStatsList.find(s => Number(s.stage) === currentStageId);
      const sectorStats = this.sectorStatsList.find(s => Number(s.stage) === currentStageId);
      
      if (!assetStats || !sectorStats) return null;
      
      const getVal = (obj, code, camel) => {
        if (!obj) return 0;
        if (obj[code] !== undefined && obj[code] !== null && obj[code] !== '') return Number(obj[code]);
        if (obj[camel] !== undefined && obj[camel] !== null && obj[camel] !== '') return Number(obj[camel]);
        if (obj.returns && obj.returns[code] !== undefined && obj.returns[code] !== null && obj.returns[code] !== '') return Number(obj.returns[code]);
        if (obj.returns && obj.returns[camel] !== undefined && obj.returns[camel] !== null && obj.returns[camel] !== '') return Number(obj.returns[camel]);
        return 0;
      };

      const assets = [
        { name: '300收益', value: getVal(assetStats, 'H00300.CSI', 'h00300Csi') },
        { name: '中证1000全收益', value: getVal(assetStats, 'H00852.SH', 'h00852Sh') },
        { name: '中证转债', value: getVal(assetStats, '000832.CSI', 'idx000832Csi') },
        { name: 'SGE黄金9999', value: getVal(assetStats, 'AU9999.SGE', 'au9999Sge') },
        { name: '中债-国债(1-3年)', value: getVal(assetStats, 'CBA00621.CS', 'cba00621Cs') },
        { name: '中债-国债(7-10年)', value: getVal(assetStats, 'CBA00651.CS', 'cba00651Cs') }
      ];
      
      const sectors = [
        { name: '消费产业(中信)', value: getVal(sectorStats, 'CI005919.WI', 'ci005919Wi') },
        { name: '科技产业(中信)', value: getVal(sectorStats, 'CI005929.WI', 'ci005929Wi') },
        { name: '周期产业(中信)', value: getVal(sectorStats, 'CI005925.WI', 'ci005925Wi') },
        { name: '金融产业(中信)', value: getVal(sectorStats, 'CI005931.WI', 'ci005931Wi') },
        { name: '稳定(风格.中信)', value: getVal(sectorStats, 'CI005921.WI', 'ci005921Wi') }
      ];
      
      // 降序排序提取 Top 3
      assets.sort((a, b) => b.value - a.value);
      sectors.sort((a, b) => b.value - a.value);
      
      return {
        stageName: stageName,
        stageColor: stageDef ? stageDef.color : '#409EFF',
        assets: assets.slice(0, 3),
        sectors: sectors.slice(0, 3)
      };
    },
    /**
     * 格式化全局时间区间文本，如 '2023-09-20 ~ 2026-09-20'，用于展示与图片导出
     */
    dateRangeText() {
      if (this.currentDateRange && this.currentDateRange.length === 2) {
        return `${this.currentDateRange[0]} ~ ${this.currentDateRange[1]}`;
      }
      return '';
    }
  },
  mounted() {
    window.addEventListener('resize', this.resizeCharts);
    // 优先使用已存在的有效日期范围（如父组件传参），若未提供则自驱动向后端拉取最新交易日并初始化近3年
    if (this.currentDateRange && this.currentDateRange.length === 2) {
      this.fetchAllData();
    } else {
      this.initDefaultDateRange();
    }
  },
  beforeDestroy() {
    // 销毁前解绑窗口监听并销毁全部已创建的 ECharts 实例，彻底释放显存
    window.removeEventListener('resize', this.resizeCharts);
    Object.values(this.charts).forEach(chart => {
      if (chart) chart.dispose();
    });
  },
  methods: {
    /**
     * 自驱动初始化全局日期范围：
     * 向后端接口获取数据库中已有的最新交易日，并自动倒推3年作为默认的系统分析跨度
     */
    initDefaultDateRange() {
      this.loading = true;
      axios.post('/api/factors/stage/list', {}).then(response => {
        const data = (response.data && response.data.status) ? response.data.data : [];
        if (data && data.length > 0) {
          const latestData = data[data.length - 1];
          const endDateStr = latestData.tradeDate;
          
          const end = new Date(endDateStr);
          const start = new Date(endDateStr);
          start.setFullYear(end.getFullYear() - 3);
          const startStr = start.toISOString().split('T')[0];
          
          this.currentDateRange = [startStr, endDateStr];
          // 复用此次响应的 stage 数据，避免 fetchAllData 再次重复请求 stage/list
          this.fetchAllData({ prefetchedStageData: data });
        } else {
          this.setFallbackDate();
          this.fetchAllData();
        }
      }).catch(error => {
        console.error("Failed to fetch default dates in StageLegend:", error);
        this.setFallbackDate();
        this.fetchAllData();
      });
    },
    /**
     * 设置兜底的全局日期范围（当前系统日期往前倒推3年）
     */
    setFallbackDate() {
      const today = new Date();
      const end = today.toISOString().split('T')[0];
      const threeYearsAgo = new Date();
      threeYearsAgo.setFullYear(today.getFullYear() - 3);
      const start = threeYearsAgo.toISOString().split('T')[0];
      this.currentDateRange = [start, end];
    },
    /**
     * 用户在页面右上角手动切换全局时间范围时的响应函数
     * 自动向父级组件派发事件，并驱动全页面所有模块和子组件重新请求测算
     */
    handleDateRangeChange(val) {
      if (val && val.length === 2) {
        this.currentDateRange = val;
        this.$emit('change-date-range', val);
        this.$emit('update:globalDateRange', val);
        this.fetchAllData();
      }
    },
    /**
     * 视口尺寸变化响应函数
     * 依次驱动所有图表重设尺寸，并刷新资产与板块趋势图中的周期 markArea 动态文字
     */
    resizeCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) chart.resize();
      });
      if (this.charts['assetChart']) {
        this.refreshChartMarkArea(this.charts['assetChart'], this.assetReturnsList);
      }
      if (this.charts['sectorChart']) {
        this.refreshChartMarkArea(this.charts['sectorChart'], this.sectorReturnsList);
      }
    },
    /**
     * 获取周期标签项的样式（当前周期高亮）
     */
    getCycleItemStyle(stage) {
      if (!this.latestMacro) return {};
      const isCurrent = this.latestMacro.stage === stage.id;
      if (isCurrent) {
        return {
          backgroundColor: stage.color,
          borderColor: stage.color,
          color: '#ffffff',
          boxShadow: `0 2px 8px ${stage.color}66`
        };
      }
      return {};
    },
    /**
     * 根据阶段ID获取对应的颜色
     * @param {number} stageId - 宏观周期阶段ID (1-6)
     * @returns {string} 颜色的十六进制字符串
     */
    getStageColor(stageId) {
      if (!stageId) return '#DCDFE6';
      const stage = this.stageDefinitions.find(s => s.id === stageId);
      return stage ? stage.color : '#DCDFE6';
    },
    /**
     * 根据阶段ID获取对应的中文名称
     * @param {number} stageId - 宏观周期阶段ID (1-6)
     * @returns {string} 阶段的中文名称
     */
    getStageName(stageId) {
      if (!stageId) return '未知';
      const stage = this.stageDefinitions.find(s => s.id === stageId);
      return stage ? stage.name : '未知';
    },
    /**
     * 根据阶段ID获取深色文字颜色（确保在浅色背景上高可读性）
     * @param {number} stageId - 宏观周期阶段ID (1-6)
     * @returns {string} 颜色的十六进制字符串
     */
    getStageTextColor(stageId) {
      const textColors = {
        1: '#1F618D', // 信用扩张 深蓝
        2: '#C0392B', // 经济复苏 深红
        3: '#D35400', // 货币退潮 深橙
        4: '#5D6D7E', // 信用退潮 深灰蓝
        5: '#1B4F72', // 经济放缓 藏蓝
        6: '#196F3D'  // 货币扩张 深绿
      };
      return textColors[stageId] || this.getStageColor(stageId);
    },
    /**
     * 格式化收益率数值为百分比字符串（支持正负号）
     * @param {number|string} val - 收益率小数（例如 0.0814 或 -0.0509）
     * @returns {string} 格式化后的百分比字符串（例如 +8.14% 或 -5.09%）
     */
    formatReturnValue(val) {
      if (val === undefined || val === null || val === '' || isNaN(Number(val))) {
        return '--';
      }
      const num = Number(val);
      const sign = num > 0 ? '+' : '';
      return `${sign}${(num * 100).toFixed(2)}%`;
    },
    /**
     * 构建 ECharts 的 markArea 宏观阶段背景色块配置
     * 用于在资产/板块趋势图中，背景上用颜色区块划分不同的宏观阶段，并在顶部显示对应阶段中文
     * 特性：支持像素级动态宽度检测（利用 chart.convertToPixel 测量可视像素宽度）：
     * - 可视像素宽度 >= 50px 时：横向展示 4 个汉字（如“经济复苏”）；
     * - 可视像素宽度 < 50px 时：文字自动隐藏，避免在缩小视野时标签彼此重叠遮挡。
     * @param {Object} [chart] - ECharts 实例
     * @param {Array} list - 带有 tradeDate 和 stage 属性的时间序列数据列表
     * @returns {Array} markArea 的 data 配置项
     */
    buildMarkAreaData(chart, list) {
      if (!list || list.length === 0) return [];
      const markAreaData = [];
      let currentStage = null;
      let startX = null;
      let startIndex = 0;
      
      // 合并连续相同阶段的交易日区间
      const segments = [];
      list.forEach((item, index) => {
        if (item.stage !== currentStage) {
          if (currentStage !== null) {
            segments.push({
              stage: currentStage,
              startX: startX,
              endX: list[index - 1].tradeDate,
              spanLength: index - startIndex
            });
          }
          currentStage = item.stage;
          startX = item.tradeDate;
          startIndex = index;
        }
      });
      if (currentStage !== null) {
        segments.push({
          stage: currentStage,
          startX: startX,
          endX: list[list.length - 1].tradeDate,
          spanLength: list.length - startIndex
        });
      }

      segments.forEach(seg => {
        let showText = false;
        if (chart && typeof chart.convertToPixel === 'function') {
          try {
            const p1 = chart.convertToPixel({ xAxisIndex: 0 }, seg.startX);
            const p2 = chart.convertToPixel({ xAxisIndex: 0 }, seg.endX);
            if (typeof p1 === 'number' && typeof p2 === 'number' && !isNaN(p1) && !isNaN(p2)) {
              const widthPx = Math.abs(p2 - p1);
              // 4个汉字在 12px 字体下大约需要 48-52px 空间，小于 50px 时自动隐藏
              showText = widthPx >= 50;
            } else {
              showText = (seg.spanLength / list.length) * 800 >= 50;
            }
          } catch (e) {
            showText = (seg.spanLength / list.length) * 800 >= 50;
          }
        } else {
          showText = (seg.spanLength / list.length) * 800 >= 50;
        }

        const stageName = this.getStageName(seg.stage);
        const stageColor = this.getStageColor(seg.stage);
        const textColor = this.getStageTextColor(seg.stage);

        markAreaData.push([
          {
            xAxis: seg.startX,
            name: showText ? stageName : '',
            itemStyle: { color: stageColor, opacity: 0.12 },
            label: {
              position: 'insideTop',
              distance: 6,
              color: textColor,
              fontSize: 12,
              fontWeight: 'bold'
            }
          },
          { xAxis: seg.endX }
        ]);
      });

      return markAreaData;
    },
    /**
     * 绑定趋势图的 dataZoom 事件，实现放大展示周期文字、缩小装不下时自动隐藏
     * @param {Object} chart - ECharts 实例
     * @param {Array} list - 包含 tradeDate 和 stage 的时间序列
     */
    bindZoomHandler(chart, list) {
      if (!chart) return;
      if (chart._hasZoomBound) return;
      chart._hasZoomBound = true;

      let zoomTimer = null;
      chart.on('datazoom', () => {
        if (zoomTimer) clearTimeout(zoomTimer);
        zoomTimer = setTimeout(() => {
          this.refreshChartMarkArea(chart, list);
        }, 30);
      });
    },
    /**
     * 根据当前可视区域像素宽度，动态刷新 markArea 周期文字
     */
    refreshChartMarkArea(chart, list) {
      if (!chart || !list || list.length === 0) return;
      const markAreaData = this.buildMarkAreaData(chart, list);
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
     * 抓取宏观相关的核心数据
     * 包括阶段列表、货币因子、信用增长因子，并触发相应的图表渲染
     * @param {Object} [opts] - 可选参数
     * @param {Array} [opts.prefetchedStageData] - 预取的阶段数据（可复用 initDefaultDateRange 的响应，避免双重请求）
     */
    fetchAllData(opts) {
      this.loading = true;
      let params = {};
      if (this.currentDateRange && this.currentDateRange.length === 2) {
        params.startDate = this.currentDateRange[0];
        params.endDate = this.currentDateRange[1];
      }

      const stagePromise = (opts && opts.prefetchedStageData)
        ? Promise.resolve({ data: { status: true, data: opts.prefetchedStageData } })
        : axios.post('/api/factors/stage/list', params);

        return Promise.all([
        stagePromise,
        axios.post('/api/factors/money/list', params),
        axios.post('/api/factors/credit-growth/list', params)
      ]).then(responses => {
        this.tableData = (responses[0].data && responses[0].data.status) ? responses[0].data.data : [];
        this.moneyList = ((responses[1].data && responses[1].data.status ? responses[1].data.data : []) || []).reverse();
        this.creditGrowthList = ((responses[2].data && responses[2].data.status ? responses[2].data.data : []) || []).reverse();
        
        this.renderAllCharts();
        return this.fetchStatsData();
      }).catch(error => {
        console.error("Failed to fetch data:", error);
        this.$message.error('获取数据失败，请检查后端服务。');
      }).finally(() => {
        this.loading = false;
      });
    },
    /**
     * 抓取大类资产与行业板块相关的统计与日频收益率数据
     * 计算累计净值（以基期为 1.0 的连乘曲线，严格保障时序对齐与 null 空值安全），并渲染收益走势与年化柱状图
     */
    fetchStatsData() {
      let params = {};
      if (this.currentDateRange && this.currentDateRange.length === 2) {
        params.startDate = this.currentDateRange[0];
        params.endDate = this.currentDateRange[1];
      }
      
      this.loading = true;
      return Promise.all([
        axios.post('/api/returns/asset/stats', params),          // 大类资产年化收益统计
        axios.post('/api/returns/sector-excess/stats', params),   // 行业板块超额收益统计
        axios.post('/api/returns/asset/list', {}),               // 大类资产全历史日频收益序列
        axios.post('/api/returns/sector-excess/list', {})        // 行业板块全历史日频超额序列
      ]).then(responses => {
        this.assetStatsList = (responses[0].data && responses[0].data.status) ? responses[0].data.data : [];
        this.sectorStatsList = (responses[1].data && responses[1].data.status) ? responses[1].data.data : [];
        
        /**
         * 计算大类资产累计净值走势
         * 原理：数据源返回的每一天数值为 (1 + r_t)，累计净值从 1.0 开始每日连乘：curNav *= val
         * 关键健壮性处理：
         * 早期历史某些资产可能尚未上市（值为 null/空），若直接连乘会导致 1 * null = 0 使整条曲线归零；
         * 因此引入 started 标志位：在首个有效收益日之前保留为 null，自首日开始连乘，上市后缺失值则保持平盘净值。
         */
        const assetList = (responses[2].data && responses[2].data.status) ? responses[2].data.data : [];
        const majorDefs = [
          { code: 'H00300.CSI', camel: 'h00300Csi' },
          { code: 'H00852.SH', camel: 'h00852Sh' },
          { code: '000832.CSI', camel: 'idx000832Csi' },
          { code: 'AU9999.SGE', camel: 'au9999Sge' },
          { code: 'CBA00621.CS', camel: 'cba00621Cs' },
          { code: 'CBA00651.CS', camel: 'cba00651Cs' }
        ];
        const curNavA = {};
        const startedA = {};
        majorDefs.forEach(d => {
          curNavA[d.code] = 1;
          startedA[d.code] = false;
        });

        this.assetReturnsList = assetList.map(item => {
          const row = { ...item };
          majorDefs.forEach(d => {
            const rawVal = (item[d.code] !== undefined && item[d.code] !== null && item[d.code] !== '')
              ? item[d.code]
              : item[d.camel];
            if (rawVal !== null && rawVal !== undefined && !isNaN(rawVal) && rawVal !== '') {
              startedA[d.code] = true;
              curNavA[d.code] *= Number(rawVal);
              const navVal = Number(curNavA[d.code].toFixed(4));
              row[d.code] = navVal;
              row[d.camel] = navVal;
            } else {
              const navVal = startedA[d.code] ? Number(curNavA[d.code].toFixed(4)) : null;
              row[d.code] = navVal;
              row[d.camel] = navVal;
            }
          });
          return row;
        });

        /**
         * 计算行业板块累计超额净值走势（同样采用 null 安全的连乘算法）
         */
        const sectorList = (responses[3].data && responses[3].data.status) ? responses[3].data.data : [];
        const sectorDefs = [
          { code: '881001.WI', camel: 'wi881001' },
          { code: 'CI005919.WI', camel: 'ci005919Wi' },
          { code: 'CI005929.WI', camel: 'ci005929Wi' },
          { code: 'CI005925.WI', camel: 'ci005925Wi' },
          { code: 'CI005931.WI', camel: 'ci005931Wi' },
          { code: 'CI005921.WI', camel: 'ci005921Wi' }
        ];
        const curNavS = {};
        const startedS = {};
        sectorDefs.forEach(d => {
          curNavS[d.code] = 1;
          startedS[d.code] = false;
        });

        this.sectorReturnsList = sectorList.map(item => {
          const row = { ...item };
          sectorDefs.forEach(d => {
            const rawVal = (item[d.code] !== undefined && item[d.code] !== null && item[d.code] !== '')
              ? item[d.code]
              : item[d.camel];
            if (rawVal !== null && rawVal !== undefined && !isNaN(rawVal) && rawVal !== '') {
              startedS[d.code] = true;
              curNavS[d.code] *= Number(rawVal);
              const navVal = Number(curNavS[d.code].toFixed(4));
              row[d.code] = navVal;
              row[d.camel] = navVal;
            } else {
              const navVal = startedS[d.code] ? Number(curNavS[d.code].toFixed(4)) : null;
              row[d.code] = navVal;
              row[d.camel] = navVal;
            }
          });
          return row;
        });
        
        this.renderAssetStatsChart();
        this.renderSectorStatsChart();
        this.renderAssetChart();
        this.renderSectorChart();

        // 双重延时自适应，彻底防御多标签页和云桌面初次布局尺寸计算滞后问题
        this.$nextTick(() => {
          this.resizeCharts();
          setTimeout(() => {
            this.resizeCharts();
          }, 250);
        });
      }).catch(error => {
        console.error("Failed to fetch stats data:", error);
        this.$message.error('获取统计数据失败。');
      }).finally(() => {
        this.loading = false;
      });
    },
    /**
     * 宏观环境走势选项卡切换响应函数
     * 在 DOM 渲染更新完毕后对激活标签下的 ECharts 实例触发 resize()，避免选项卡隐藏导致的尺寸坍缩
     * @param {Object} tab - Element-UI tab 实例
     */
    handleTabClick(tab) {
      this.$nextTick(() => {
        const chartName = tab.name + 'Chart';
        if (this.charts[chartName]) {
          this.charts[chartName].resize();
        }
      });
    },
    /**
     * 统一渲染所有宏观环境相关的基础图表（阶段、货币、信用、增长及三个半环形仪表盘）
     */
    renderAllCharts() {
      this.renderStageChart();
      this.renderMoneyChart();
      this.renderCreditChart();
      this.renderGrowthChart();
      this.renderGauges();
    },
    /**
     * 渲染货币、信用、增长三个宏观因子的半环形仪表盘 (Gauge Charts)
     * 将各因子的数值（-1/0/+1）映射为 -100 到 +100 的指针旋转弧度，并采用红绿两色线段指示松紧方向
     */
    renderGauges() {
      if (!this.latestMacro) return;
      this.$nextTick(() => {
        this.gaugeFactors.forEach(f => {
          const chart = this.initChart(f.ref);
          if (!chart) return;
          
          // 数值放大至 -100 ~ 100 弧度区间
          let displayVal = Math.max(-100, Math.min(100, f.value * 50));
          if (f.value === 0) displayVal = 0;
          
          const option = {
            series: [
              {
                type: 'gauge',
                startAngle: 180, // 半环起点
                endAngle: 0,     // 半环终点
                min: -100,
                max: 100,
                radius: '100%',
                center: ['50%', '80%'],
                axisLine: {
                  lineStyle: {
                    width: 8,
                    color: [
                      [0.5, '#409EFF'], // 左半轴：蓝色（收紧/收缩）
                      [1, '#F56C6C']    // 右半轴：红色（宽松/扩张）
                    ]
                  }
                },
                pointer: { length: '60%', width: 3 },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                detail: { show: false },
                title: { show: false },
                data: [{ value: displayVal }]
              }
            ]
          };
          chart.setOption(option);
        });
      });
    },
    /**
     * 按需初始化图表实例并缓存于 this.charts 中，避免重复 new 创建导致内存浪费
     * @param {string} refName - 组件 template 中的 ref 标识符
     * @returns {Object|null} ECharts 实例对象
     */
    initChart(refName) {
      const el = this.$refs[refName];
      if (!el) return null;
      let existingInstance = echarts.getInstanceByDom(el);
      if (existingInstance) {
        this.charts[refName] = existingInstance;
        return existingInstance;
      }
      if (this.charts[refName]) {
        try {
          this.charts[refName].dispose();
        } catch (e) {}
      }
      const chart = echarts.init(el);
      this.charts[refName] = chart;
      return chart;
    },
    /**
     * 渲染综合周期阶段图表 (瀑布图变体)
     * X轴为日期，Y轴为所处阶段(1-6)，并配置了带有三因子状态中文翻译的定制化提示框
     */
    renderStageChart() {
      const chart = this.initChart('stageChart');
      if (!chart) return;
      
      const xAxisData = this.tableData.map(item => item.tradeDate);
      const baseData = [];
      const barData = [];
      
      this.tableData.forEach(item => {
        const s = item.stage;
        if (s) {
          baseData.push(s - 1);
          barData.push({
            value: 1,
            itemStyle: { color: this.getStageColor(s) }
          });
        } else {
          baseData.push(0);
          barData.push(0);
        }
      });

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: params => {
            const index = params[0].dataIndex;
            const item = this.tableData[index];
            if (!item || !item.stage) return '';
            
            const date = item.tradeDate;
            const stageName = this.getStageName(item.stage);
            const moneyStr = item.money < 0 ? '收紧' : (item.money > 0 ? '宽松' : '不变');
            const creditStr = item.credit < 0 ? '收缩' : (item.credit > 0 ? '扩张' : '不变');
            const growthStr = item.growth < 0 ? '收缩' : (item.growth > 0 ? '扩张' : '不变');
            
            return `${date}<br/>阶段：${stageName}；货币：${moneyStr}；信用：${creditStr}；增长：${growthStr}；`;
          }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: xAxisData },
        yAxis: [
          { 
            type: 'value', 
            min: 0, 
            max: 6, 
            interval: 1,
            axisLabel: { show: false },
            splitLine: { show: true }
          },
          {
            type: 'value',
            min: 0,
            max: 6,
            interval: 0.5,
            position: 'left',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: {
              formatter: (value) => {
                if (value % 1 !== 0) {
                  return this.getStageName(Math.ceil(value));
                }
                return '';
              }
            }
          }
        ],
        series: [
          {
            name: 'Base', type: 'bar', stack: 'Total',
            itemStyle: { borderColor: 'transparent', color: 'transparent' },
            data: baseData
          },
          { name: 'Stage', type: 'bar', stack: 'Total', barWidth: '100%', data: barData }
        ]
      };
      chart.setOption(option);
    },
    /**
     * 渲染货币因子趋势图
     * 展示货币方向因子的历史走势
     */
    renderMoneyChart() {
      const chart = this.initChart('moneyChart');
      if (!chart) return;

      const xAxisData = this.moneyList.map(item => item.tradeDate);
      const data = this.moneyList.map(item => item.moneyDirectionFactor || 0);

      const option = {
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: xAxisData },
        yAxis: { type: 'value' },
        series: [
          {
            name: '货币方向因子',
            type: 'line',
            step: 'end',
            data: data,
            showSymbol: false,
            itemStyle: { color: '#555' },
            lineStyle: { width: 1 },
            areaStyle: { color: '#e1f5e1' } // 浅绿色阴影填充
          }
        ]
      };
      chart.setOption(option);
    },
    /**
     * 渲染信用因子趋势图
     * 包含信用方向因子 (左轴) 和中长期贷款脉冲 (右轴，加粗红线)
     */
    renderCreditChart() {
      const chart = this.initChart('creditChart');
      if (!chart) return;

      const xAxisData = this.creditGrowthList.map(item => item.tradeDate);
      const directionData = this.creditGrowthList.map(item => item.creditDirectionFactor || 0);
      const pulseData = this.creditGrowthList.map(item => item.finLoanMidLongPulse || 0);

      const option = {
        tooltip: { trigger: 'axis' },
        legend: { 
          data: ['信用方向', '中长期贷款脉冲'],
          top: 0,
          left: 'center',
          padding: [0, 45, 0, 0]
        },
        grid: { top: 40, left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: xAxisData },
        yAxis: [
          { type: 'value', name: '方向' },
          { type: 'value', name: '脉冲', splitLine: { show: false } }
        ],
        series: [
          {
            name: '信用方向',
            type: 'line',
            step: 'end',
            data: directionData,
            showSymbol: false,
            itemStyle: { color: '#555' },
            lineStyle: { width: 1 },
            areaStyle: { color: '#e1f5e1' }
          },
          {
            name: '中长期贷款脉冲',
            type: 'line',
            yAxisIndex: 1,
            data: pulseData,
            showSymbol: false,
            itemStyle: { color: '#e74c3c' },
            lineStyle: { width: 1 }
          }
        ]
      };
      chart.setOption(option);
    },
    /**
     * 渲染增长因子趋势图
     * 包含增长方向扩散指数 (左轴) 和多项PMI脉冲指标 (右轴)
     */
    renderGrowthChart() {
      const chart = this.initChart('growthChart');
      if (!chart) return;

      const xAxisData = this.creditGrowthList.map(item => item.tradeDate);
      const directionData = this.creditGrowthList.map(item => item.growthDirectionFactor || 0);
      const mfgPulseData = this.creditGrowthList.map(item => item.manufacturePmiPulse || 0);
      const nonMfgPulseData = this.creditGrowthList.map(item => item.nonManufacturePmiPulse || 0);
      const unofficialPulseData = this.creditGrowthList.map(item => item.pmiUnofficialPulse || 0);

      const option = {
        tooltip: { trigger: 'axis' },
        legend: { 
          data: ['增长方向扩散指数', 'PMI脉冲 中采制造业', 'PMI脉冲 中采非制造业', 'PMI脉冲 财新制造业'],
          top: 0,
          left: 'center',
          padding: [0, 45, 0, 0]
        },
        grid: { top: 40, left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: xAxisData },
        yAxis: [
          { type: 'value', name: '扩散指数' },
          { type: 'value', name: 'PMI脉冲', splitLine: { show: false } }
        ],
        series: [
          {
            name: '增长方向扩散指数',
            type: 'line',
            step: 'end',
            data: directionData,
            showSymbol: false,
            itemStyle: { color: '#555' },
            lineStyle: { width: 1 },
            areaStyle: { color: '#e1f5e1' }
          },
          {
            name: 'PMI脉冲 中采制造业',
            type: 'line',
            yAxisIndex: 1,
            data: mfgPulseData,
            showSymbol: false,
            itemStyle: { color: '#e74c3c' },
            lineStyle: { width: 1 }
          },
          {
            name: 'PMI脉冲 中采非制造业',
            type: 'line',
            yAxisIndex: 1,
            data: nonMfgPulseData,
            showSymbol: false,
            itemStyle: { color: '#3498db' },
            lineStyle: { width: 1 }
          },
          {
            name: 'PMI脉冲 财新制造业',
            type: 'line',
            yAxisIndex: 1,
            data: unofficialPulseData,
            showSymbol: false,
            itemStyle: { color: '#95a5a6' },
            lineStyle: { width: 1 }
          }
        ]
      };
      chart.setOption(option);
    },
    /**
     * 渲染资产收益历史趋势图
     * 展示各大类资产的累计净值走势，并在背景中叠加宏观六阶段的颜色划分 (markArea)
     */
    renderAssetChart() {
      const chart = this.initChart('assetChart');
      if (!chart) return;

      const xAxisData = this.assetReturnsList.map(item => item.tradeDate);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            const index = params[0].dataIndex;
            const item = this.assetReturnsList[index];
            const stageName = this.getStageName(item.stage);
            const stageColor = this.getStageColor(item.stage);
            let tooltipHtml = `<div style="margin-bottom: 5px;">${item.tradeDate} 
              <span style="display:inline-block;padding:2px 6px;border-radius:4px;color:#fff;background-color:${stageColor};font-size:12px;margin-left:8px;">${stageName}</span></div>`;
            params.forEach(p => {
              const valDisplay = (p.value !== null && p.value !== undefined && !isNaN(p.value)) ? Number(p.value).toFixed(4) : '--';
              tooltipHtml += `<div>${p.marker} ${p.seriesName}: <strong>${valDisplay}</strong></div>`;
            });
            return tooltipHtml;
          }
        },
        legend: {
          data: ['300收益', '中证1000全收益', '中证转债', 'SGE黄金9999', '中债-国债(1-3年)', '中债-国债(7-10年)'],
          top: 0,
          padding: [0, 45, 0, 0]
        },
        grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { type: 'slider', start: 0, end: 100, bottom: 0 }
        ],
        xAxis: { type: 'category', data: xAxisData, boundaryGap: false },
        yAxis: { type: 'value', scale: true, name: '净值/收益' },
        series: [
          { 
            name: '300收益', 
            type: 'line', 
            smooth: true, 
            showSymbol: false,
            connectNulls: true,
            data: this.assetReturnsList.map(i => i.h00300Csi),
            markArea: {
              silent: true,
              data: this.buildMarkAreaData(chart, this.assetReturnsList)
            }
          },
          { name: '中证1000全收益', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.assetReturnsList.map(i => i.h00852Sh) },
          { name: '中证转债', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.assetReturnsList.map(i => i.idx000832Csi) },
          { name: 'SGE黄金9999', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.assetReturnsList.map(i => i.au9999Sge) },
          { name: '中债-国债(1-3年)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.assetReturnsList.map(i => i.cba00621Cs) },
          { name: '中债-国债(7-10年)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.assetReturnsList.map(i => i.cba00651Cs) }
        ]
      };
      chart.setOption(option);
      this.bindZoomHandler(chart, this.assetReturnsList);
      this.$nextTick(() => {
        this.refreshChartMarkArea(chart, this.assetReturnsList);
      });
    },
    /**
     * 渲染板块超额收益历史趋势图
     * 展示各中信一级行业板块的累计净值走势，同样在背景叠加阶段划分
     */
    renderSectorChart() {
      const chart = this.initChart('sectorChart');
      if (!chart) return;

      const xAxisData = this.sectorReturnsList.map(item => item.tradeDate);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            const index = params[0].dataIndex;
            const item = this.sectorReturnsList[index];
            const stageName = this.getStageName(item.stage);
            const stageColor = this.getStageColor(item.stage);
            let tooltipHtml = `<div style="margin-bottom: 5px;">${item.tradeDate} 
              <span style="display:inline-block;padding:2px 6px;border-radius:4px;color:#fff;background-color:${stageColor};font-size:12px;margin-left:8px;">${stageName}</span></div>`;
            params.forEach(p => {
              const valDisplay = (p.value !== null && p.value !== undefined && !isNaN(p.value)) ? Number(p.value).toFixed(4) : '--';
              tooltipHtml += `<div>${p.marker} ${p.seriesName}: <strong>${valDisplay}</strong></div>`;
            });
            return tooltipHtml;
          }
        },
        legend: {
          data: ['万得全A', '消费(中信)', '科技(中信)', '周期(中信)', '金融(中信)', '稳定(中信)'],
          top: 0,
          padding: [0, 45, 0, 0]
        },
        grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { type: 'slider', start: 0, end: 100, bottom: 0 }
        ],
        xAxis: { type: 'category', data: xAxisData, boundaryGap: false },
        yAxis: { type: 'value', scale: true, name: '净值/超额' },
        series: [
          { 
            name: '万得全A', 
            type: 'line', 
            smooth: true, 
            showSymbol: false,
            connectNulls: true,
            data: this.sectorReturnsList.map(i => i.wi881001), 
            itemStyle: {color: '#e74c3c'}, 
            lineStyle: {width: 2},
            markArea: {
              silent: true,
              data: this.buildMarkAreaData(chart, this.sectorReturnsList)
            }
          },
          { name: '消费(中信)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.sectorReturnsList.map(i => i.ci005919Wi) },
          { name: '科技(中信)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.sectorReturnsList.map(i => i.ci005929Wi) },
          { name: '周期(中信)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.sectorReturnsList.map(i => i.ci005925Wi) },
          { name: '金融(中信)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.sectorReturnsList.map(i => i.ci005931Wi) },
          { name: '稳定(中信)', type: 'line', smooth: true, showSymbol: false, connectNulls: true, data: this.sectorReturnsList.map(i => i.ci005921Wi) }
        ]
      };
      chart.setOption(option);
      this.bindZoomHandler(chart, this.sectorReturnsList);
      this.$nextTick(() => {
        this.refreshChartMarkArea(chart, this.sectorReturnsList);
      });
    },
    /**
     * 渲染资产收益统计(年化)柱状图
     * 将每个大类资产在 6 个宏观阶段的年化收益率并排展示，以阶段颜色区分
     */
    renderAssetStatsChart() {
      const chart = this.initChart('assetStatsChart');
      if (!chart) return;

      const assets = ['300收益', '中证1000全收益', '中证转债', 'SGE黄金9999', '中债-国债(1-3年)', '中债-国债(7-10年)'];
      const assetCodes = ['H00300.CSI', 'H00852.SH', '000832.CSI', 'AU9999.SGE', 'CBA00621.CS', 'CBA00651.CS'];
      const fields = ['h00300Csi', 'h00852Sh', 'idx000832Csi', 'au9999Sge', 'cba00621Cs', 'cba00651Cs'];
      
      const series = this.stageDefinitions.map(stageDef => {
        const stageData = this.assetStatsList.find(s => s.stage === stageDef.id);
        const data = stageData ? assetCodes.map((code, idx) => {
          const val = stageData[code] !== undefined ? stageData[code] : stageData[fields[idx]];
          return (Number(val || 0) * 100).toFixed(2);
        }) : [0,0,0,0,0,0];
        
        return {
          name: `${stageDef.id}${stageDef.name}`,
          type: 'bar',
          barGap: 0,
          barCategoryGap: '45%',
          itemStyle: { color: stageDef.color },
          label: { show: false },
          data: data
        };
      });

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          valueFormatter: value => value + '%'
        },
        legend: {
          data: this.stageDefinitions.map(s => `${s.id}${s.name}`),
          bottom: 0
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '15%', containLabel: true },
        xAxis: [
          {
            type: 'category',
            axisTick: { show: false },
            axisLabel: { interval: 0, rotate: 15, fontSize: 11, fontWeight: 'bold', color: '#303133', margin: 15, align: 'center' },
            data: assets
          }
        ],
        yAxis: [
          {
            type: 'value',
            axisLabel: { formatter: '{value} %' }
          }
        ],
        series: series
      };
      chart.setOption(option);
    },
    /**
     * 渲染板块超额统计(年化)柱状图
     * 将每个行业板块在 6 个宏观阶段的年化收益率并排展示，以阶段颜色区分
     */
    renderSectorStatsChart() {
      const chart = this.initChart('sectorStatsChart');
      if (!chart) return;

      const sectors = ['万得全A', '消费(中信)', '科技(中信)', '周期(中信)', '金融(中信)', '稳定(中信)'];
      const sectorCodes = ['881001.WI', 'CI005919.WI', 'CI005929.WI', 'CI005925.WI', 'CI005931.WI', 'CI005921.WI'];
      const fields = ['wi881001', 'ci005919Wi', 'ci005929Wi', 'ci005925Wi', 'ci005931Wi', 'ci005921Wi'];
      
      const series = this.stageDefinitions.map(stageDef => {
        const stageData = this.sectorStatsList.find(s => s.stage === stageDef.id);
        const data = stageData ? sectorCodes.map((code, idx) => {
          const val = stageData[code] !== undefined ? stageData[code] : stageData[fields[idx]];
          return (Number(val || 0) * 100).toFixed(2);
        }) : [0,0,0,0,0,0];
        
        return {
          name: `${stageDef.id}${stageDef.name}`,
          type: 'bar',
          barGap: 0,
          barCategoryGap: '45%',
          itemStyle: { color: stageDef.color },
          label: { show: false },
          data: data
        };
      });

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          valueFormatter: value => value + '%'
        },
        legend: {
          data: this.stageDefinitions.map(s => `${s.id}${s.name}`),
          bottom: 0
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '15%', containLabel: true },
        xAxis: [
          {
            type: 'category',
            axisTick: { show: false },
            axisLabel: { interval: 0, rotate: 15, fontSize: 11, fontWeight: 'bold', color: '#303133', margin: 15, align: 'center' },
            data: sectors
          }
        ],
        yAxis: [
          {
            type: 'value',
            axisLabel: { formatter: '{value} %' }
          }
        ],
        series: series
      };
      chart.setOption(option);
    },
    /**
     * 绘制圆角矩形辅助方法
     */
    drawCanvasRoundedRect(ctx, x, y, width, height, radius, fill, stroke) {
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + width - radius, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
      ctx.lineTo(x + width, y + height - radius);
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      if (fill) {
        ctx.fillStyle = fill;
        ctx.fill();
      }
      if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.stroke();
      }
    },
    /**
     * 导出包含顶部标题与右上角日期范围的统计图表卡片图片
     * @param {string} chartRef - ECharts 实例引用的 ref 名称
     * @param {string} title - 图表标题（如 '宏观环境与三因子 - 综合周期阶段'）
     * @param {Object} [options] - 可选配置，如 includeStageLegend 是否包含六周期图例、fileName 自定义文件名
     */
    exportStatsChart(chartRef, title, options = {}) {
      const chart = this.charts[chartRef];
      if (!chart) {
        this.$message.warning('图表正在加载中，请稍候');
        return;
      }

      // 获取当前图表高清 Base64 (排除 toolbox 工具按钮)
      const chartImgUri = chart.getDataURL({
        pixelRatio: 2,
        backgroundColor: '#ffffff',
        excludeComponents: ['toolbox']
      });

      const cleanDate = this.dateRangeText ? '_' + this.dateRangeText.replace(/\s+/g, '') : '';
      let baseName = options.fileName || title;
      baseName = baseName.replace(/\s+/g, '').replace(/[()（）]/g, '_').replace(/[·-]/g, '_').replace(/_+/g, '_').replace(/_+$/, '');
      const fileName = `${baseName}${cleanDate}.png`;

      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const scale = 2;

        const chartWidth = (this.$refs[chartRef] && this.$refs[chartRef].clientWidth) || chart.getWidth() || 800;
        const chartHeight = (this.$refs[chartRef] && this.$refs[chartRef].clientHeight) || chart.getHeight() || 350;

        const hasLegend = options.includeStageLegend;
        const legendHeight = hasLegend ? 32 : 0;
        const headerHeight = 56;
        const totalHeaderHeight = headerHeight + legendHeight;
        const totalWidth = chartWidth;
        const totalHeight = chartHeight + totalHeaderHeight;

        canvas.width = totalWidth * scale;
        canvas.height = totalHeight * scale;
        ctx.scale(scale, scale);

        // 1. 绘制卡片背景与细边框
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, totalWidth, totalHeight);
        this.drawCanvasRoundedRect(ctx, 1, 1, totalWidth - 2, totalHeight - 2, 8, '#ffffff', '#e4e7ed');

        // 2. 绘制卡片左侧标题
        ctx.fillStyle = '#303133';
        ctx.font = 'bold 15px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif';
        ctx.fillText(title, 20, 34);

        // 3. 绘制右上角日期范围标签 (样式对齐界面 el-tag)
        if (this.dateRangeText) {
          const dateText = this.dateRangeText;
          ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif';
          const textW = ctx.measureText(dateText).width;
          const tagPaddingH = 8;
          const tagH = 24;
          const iconW = 12;
          const tagW = textW + tagPaddingH * 2 + iconW + 6;
          const tagX = totalWidth - tagW - 20;
          const tagY = 16;

          // 绘制浅灰标签背景与描边
          this.drawCanvasRoundedRect(ctx, tagX, tagY, tagW, tagH, 4, '#f4f4f5', '#e9e9eb');

          // 绘制日历小图标
          const iconX = tagX + tagPaddingH;
          const iconY = tagY + 6;
          ctx.strokeStyle = '#909399';
          ctx.lineWidth = 1.2;
          ctx.strokeRect(iconX, iconY + 2, 11, 9);
          ctx.beginPath();
          ctx.moveTo(iconX, iconY + 5);
          ctx.lineTo(iconX + 11, iconY + 5);
          ctx.moveTo(iconX + 3, iconY);
          ctx.lineTo(iconX + 3, iconY + 2);
          ctx.moveTo(iconX + 8, iconY);
          ctx.lineTo(iconX + 8, iconY + 2);
          ctx.stroke();

          // 绘制日期文字
          ctx.fillStyle = '#909399';
          ctx.textBaseline = 'middle';
          ctx.fillText(dateText, iconX + 15, tagY + tagH / 2);
          ctx.textBaseline = 'alphabetic';
        }

        // 4. 绘制顶部分割线
        ctx.strokeStyle = '#ebeef5';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(1, headerHeight);
        ctx.lineTo(totalWidth - 1, headerHeight);
        ctx.stroke();

        // 4.1 如果需要六周期图例 (综合周期阶段)，在头部下方绘制六个阶段彩色指示框
        if (hasLegend && this.stageDefinitions && this.stageDefinitions.length) {
          ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
          const pillPaddingH = 8;
          const pillHeight = 22;
          const pillGap = 8;
          const pillItems = this.stageDefinitions.map(s => {
            const label = `${s.id}: ${s.name}`;
            const textWidth = ctx.measureText(label).width;
            const w = textWidth + 12 + 6 + pillPaddingH * 2;
            return { stage: s, label, width: w };
          });
          const totalLegendWidth = pillItems.reduce((sum, item) => sum + item.width, 0) + (pillItems.length - 1) * pillGap;
          let curX = Math.max(20, (totalWidth - totalLegendWidth) / 2);
          const legendY = headerHeight + 5;

          pillItems.forEach(item => {
            this.drawCanvasRoundedRect(ctx, curX, legendY, item.width, pillHeight, 4, '#fafafa', '#e4e7ed');
            this.drawCanvasRoundedRect(ctx, curX + pillPaddingH, legendY + 5, 12, 12, 3, item.stage.color);
            ctx.fillStyle = '#303133';
            ctx.textBaseline = 'middle';
            ctx.fillText(item.label, curX + pillPaddingH + 18, legendY + pillHeight / 2);
            ctx.textBaseline = 'alphabetic';
            curX += item.width + pillGap;
          });
        }

        // 5. 绘制图表主体
        ctx.drawImage(img, 0, totalHeaderHeight, chartWidth, chartHeight);

        // 6. 下载合成后的完整图片
        const link = document.createElement('a');
        link.download = fileName;
        link.href = canvas.toDataURL('image/png');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        this.$message.success(`已成功导出【${title}】图片`);
      };

      img.onerror = () => {
        // 降级使用普通图片导出
        const link = document.createElement('a');
        link.download = fileName;
        link.href = chartImgUri;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      };

      img.src = chartImgUri;
    }
  }
}
</script>

<style scoped>
.recommendations-panel {
  background: linear-gradient(135deg, #f0f7ff 0%, #e1eaf7 100%);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 12px 0 rgba(0,0,0,0.05);
}
.rec-header {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.rec-title-group {
  display: flex;
  align-items: center;
}
.rec-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-right: 10px;
}
.header-date-filter {
  display: flex;
  align-items: center;
}
.header-date-filter .date-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  margin-right: 8px;
  display: flex;
  align-items: center;
  white-space: nowrap;
}
.header-date-filter .date-label i {
  margin-right: 4px;
  color: #409EFF;
}
.global-date-picker {
  max-width: 240px;
}
.global-date-picker.el-range-editor--mini.el-input__inner {
  height: 28px;
  line-height: 28px;
  border-radius: 4px;
  border-color: #dcdfe6;
  background-color: #ffffff;
}
.global-date-picker.el-range-editor--mini.el-input__inner:hover {
  border-color: #409EFF;
}
.rec-card {
  border: none;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
}
.rec-card /deep/ .el-card__header {
  padding: 12px 15px;
  font-weight: bold;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px 8px 0 0;
}
.asset-rec-card /deep/ .el-card__header {
  color: #409EFF;
}
.sector-rec-card /deep/ .el-card__header {
  color: #67C23A;
}
.rec-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rec-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  background: #fff;
  border-radius: 6px;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.rec-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.rec-rank {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 50%;
  color: white;
  font-weight: bold;
  font-size: 12px;
  margin-right: 12px;
}
.rank-1 { background: #F56C6C; box-shadow: 0 2px 6px rgba(245, 108, 108, 0.4); }
.rank-2 { background: #E6A23C; box-shadow: 0 2px 6px rgba(230, 162, 60, 0.4); }
.rank-3 { background: #409EFF; box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4); }
.rec-name {
  flex: 1;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
.rec-val {
  font-weight: bold;
  font-size: 15px;
}
.text-danger { color: #F56C6C; }
.text-success { color: #67C23A; }
.text-muted { color: #909399; }
.factor-badge {
  display: inline-block;
  background: #409EFF;
  color: #fff;
  width: 16px;
  height: 16px;
  text-align: center;
  border-radius: 2px;
  line-height: 16px;
  margin-right: 5px;
  font-size: 11px;
}

.stage-legend-container {
  /* 标准块级布局，兼容内网固定容器高度场景 */
  width: 100%;
  box-sizing: border-box;
}
.app-header-bar {
  background-color: #409EFF;
  color: white;
  height: 60px;
  line-height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}
.header-title-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}
.app-title-text {
  margin: 0;
  font-size: 20px;
  letter-spacing: 1px;
  color: #ffffff;
  font-weight: 600;
}
.header-help-icon {
  margin-left: 8px;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
}
.header-help-icon:hover {
  color: #ffffff;
  transform: scale(1.1);
}
.stage-content-body {
  padding: 20px;
  box-sizing: border-box;
}
.legend-boxes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}
.legend-item {
  display: flex;
  align-items: center;
  width: auto;
  padding: 5px 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  margin-right: 8px;
}
.stage-info {
  display: flex;
  flex-direction: column;
}
.stage-info strong {
  font-size: 13px;
  color: #303133;
}
.stage-info .condition {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.text-success {
  color: #67C23A;
  font-weight: bold;
}
.text-danger {
  color: #F56C6C;
  font-weight: bold;
}
/* 确保标签页不重叠 */
.el-tabs__content {
  overflow: visible;
}

/* 穿透覆盖 el-card__body 默认样式，防止内网版本大山截断图表内容 */
/deep/ .el-card__body {
  overflow: visible !important;
}
.box-card /deep/ .el-card__body {
  overflow: visible;
}

/* 提取的通用样式 */
.mb-20 {
  margin-bottom: 20px;
}
.mb-15 {
  margin-bottom: 15px;
}
.h-100 {
  height: 100%;
  min-height: 250px;
}
.rec-panel-wrapper {
  height: 100%;
  min-height: 320px;
  box-sizing: border-box;
  margin-bottom: 0;
}
.stage-tag {
  border: none;
  font-size: 14px;
}
.card-title-lg {
  font-size: 16px;
  font-weight: bold;
}
.card-title {
  font-weight: bold;
}
.chart-container {
  width: 100%;
  height: 350px;
}

/* 第一层级卡片流式布局样式 */
.flex-col-container {
  display: flex;
  flex-direction: column;
  min-height: 350px;
}
.flex-1-col {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
.flex-1-row {
  flex: 1;
  min-height: 250px;
}
.help-icon {
  margin-left: 8px;
  color: #909399;
  cursor: pointer;
}
.macro-inner-box {
  display: flex;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  box-sizing: border-box;
  min-height: 100px;
}
.macro-ai-summary-box {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  padding: 14px 16px;
  box-sizing: border-box;
}
.ai-summary-stage {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}
.ai-summary-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-summary-item {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  display: flex;
  align-items: flex-start;
  text-align: justify;
}
.ai-summary-item .factor-badge {
  margin-top: 3px;
  flex-shrink: 0;
}
.factor-name {
  color: #303133;
  flex-shrink: 0;
  margin-right: 2px;
}
.ai-summary-divider {
  border-top: 1px dashed #DCDFE6;
  margin: 10px 0 8px 0;
}
.ai-summary-disclaimer {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
}
.disclaimer-icon {
  margin-right: 5px;
  font-size: 13px;
  color: #E6A23C;
}
.macro-text-part {
  flex: 1.4;
  padding-right: 10px;
  border-right: 1px dashed #DCDFE6;
  font-size: 13px;
  color: #606266;
  line-height: 1;
  display: flex;
  flex-direction: column;
}
.macro-stage-section {
  margin-bottom: 0;
}
.macro-stage-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
  line-height: 20px;
  display: flex;
  align-items: center;
}
.macro-cycles-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-start;
}
.stage-cycles-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px 1px;
  width: 100%;
}
.cycle-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 6px;
  height: 28px;
  box-sizing: border-box;
  border-radius: 4px;
  font-size: 12px;
  background: #F4F6F9;
  border: 1px solid #E4E7ED;
  color: #909399;
  cursor: default;
  transition: all 0.25s ease;
  user-select: none;
}
.cycle-pill:hover {
  border-color: #C0C4CC;
  color: #606266;
}
.cycle-pill-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  font-size: 10px;
  background: rgba(0, 0, 0, 0.08);
  margin-right: 3px;
  flex-shrink: 0;
}
.cycle-pill-name {
  white-space: nowrap;
}
.cycle-pill.is-active {
  font-weight: bold;
  transform: translateY(-1px);
  cursor: default;
}
.cycle-pill.is-active .cycle-pill-num {
  background: rgba(255, 255, 255, 0.35);
  color: #fff;
}
.active-check-icon {
  margin-left: 3px;
  font-size: 11px;
  color: #fff;
}
.macro-stage-text {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
}
.macro-date-text {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
.macro-gauges-part {
  flex: 1.1;
  display: flex;
  flex-direction: column;
  padding-left: 14px;
}
.macro-gauges-row {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
  flex: 1;
}
.gauge-wrapper {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
}
.gauge-chart {
  width: 70px;
  height: 70px;
}
.gauge-title {
  font-size: 12px;
  font-weight: bold;
  margin-top: -5px;
  white-space: nowrap;
}
.gauge-date {
  font-size: 11px;
  color: #909399;
  transform: scale(0.9);
}

/* 图表导出按钮统一视觉样式 (对齐资产仓位建议) */
.chart-wrapper {
  position: relative;
  width: 100%;
}

.dashboard-download-btn {
  position: absolute;
  right: 12px;
  top: 0px;
  z-index: 10;
  cursor: pointer;
  font-size: 17px;
  color: #6366f1;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.dashboard-download-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #4338ca;
  transform: scale(1.1);
}

.sector-download-btn {
  color: #10b981;
}

.sector-download-btn:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
}
</style>
