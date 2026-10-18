<template>
  <div class="dynamic-risk-budget-container">
    <el-row :gutter="20" type="flex" align="top" class="budget-row">
      <!-- 卡片 1: 动态大类资产风险预算 -->
      <el-col :span="12" class="budget-col">
        <el-card class="risk-budget-card" shadow="hover">
          <div slot="header" class="card-header">
            <div class="header-left">
              <div class="title-icon major-icon">
                <i class="el-icon-pie-chart"></i>
              </div>
              <div class="title-text">
                <span class="title">
                  资产仓位建议
                  <el-tooltip effect="dark" content="基于自定义资产池与各宏观阶段的风险预算配额，通过风险预算算法求解大类资产建议仓位" placement="top-start">
                    <i class="el-icon-question help-icon"></i>
                  </el-tooltip>
                </span>
                <div class="tags-row">
                  <el-tag v-if="major.cycle" size="mini" effect="plain" class="cycle-tag">{{ major.cycle }}</el-tag>
                  <el-tag v-if="major.endDate" size="mini" type="info" effect="plain" class="date-tag">
                    <i class="el-icon-date"></i> 截止日期: {{ major.endDate }}
                  </el-tag>
                </div>
              </div>
            </div>

            <div class="header-right">
              <el-radio-group v-model="major.viewMode" size="mini">
                <el-radio-button label="chart">
                  <i class="el-icon-data-line"></i> 建议仓位
                </el-radio-button>
                <el-radio-button label="config">
                  <i class="el-icon-setting"></i> 参数配置
                  <span v-if="!major.isValid" class="badge-dot"></span>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>

          <div class="content-wrapper" v-loading="major.loading" element-loading-text="动态模型计算中...">
            <!-- 视图 1: 仓位建议图表 -->
            <div v-show="major.viewMode === 'chart'">
              <div v-if="major.error" class="error-container">
                <i class="el-icon-warning-outline"></i>
                <p>{{ major.error }}</p>
                <el-button size="small" type="primary" @click="fetchMajorData" round>重新加载</el-button>
              </div>

              <template v-if="!major.error">
                <div class="dual-dashboard">
                  <!-- 左侧：左移聚焦的 ECharts 饼图 -->
                  <div class="chart-area">
                    <div ref="majorChart" class="echarts-chart"></div>
                  </div>

                  <!-- 右侧：风险预算设定 vs 实际建议仓位鲜明对比面板 -->
                  <div class="comparison-panel">
                    <div class="comp-panel-header">
                      <div class="comp-panel-title">
                        <i class="el-icon-s-operation comp-icon"></i>
                        <span class="comp-title-text">
                          当前<strong>【{{ major.cycle || '最新周期' }}】</strong>风险预算 vs 建议仓位对比
                          <span v-if="major.endDate" class="comp-date-tip">（截至 {{ major.endDate }}）</span>
                        </span>
                      </div>
                      <div class="comp-header-actions">
                        <el-button
                          size="mini"
                          type="text"
                          icon="el-icon-edit"
                          class="comp-edit-btn"
                          @click="major.viewMode = 'config'"
                        >
                          修改配额
                        </el-button>
                        <el-tooltip effect="dark" content="导出完整对比图表与配额设定图片" placement="top">
                          <span class="comp-download-icon" @click="exportComprehensiveImage('major')">
                            <i class="el-icon-download"></i>
                          </span>
                        </el-tooltip>
                      </div>
                    </div>

                    <div class="comp-table-container">
                      <table class="comp-table">
                        <thead>
                          <tr>
                            <th class="th-asset">标的资产</th>
                            <th class="th-quota">
                              <span>风险预算</span>
                              <el-tooltip effect="dark" content="当前宏观周期设定的目标风险预算配额" placement="top">
                                <i class="el-icon-info comp-tip-icon"></i>
                              </el-tooltip>
                            </th>
                            <th class="th-weight">
                              <span>建议仓位</span>
                              <el-tooltip effect="dark" content="基于模型优化求解计算出的最终建议持仓比例" placement="top">
                                <i class="el-icon-info comp-tip-icon"></i>
                              </el-tooltip>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(item, index) in majorComparisonList"
                            :key="item.id"
                            class="comp-row"
                            :style="{ animationDelay: (index * 0.08) + 's' }"
                          >
                            <td class="td-asset">
                              <div class="comp-asset-cell">
                                <span class="comp-color-dot" :style="{ background: majorPalette[index % majorPalette.length] }"></span>
                                <span class="comp-asset-name" :title="item.name">{{ item.name }}</span>
                              </div>
                            </td>
                            <td class="td-quota">
                              <div class="comp-metric-inline" :title="`【${item.name}】目标风险预算: ${item.quotaText}`">
                                <span class="quota-pill">{{ item.quotaText }}</span>
                                <div class="metric-bar-track">
                                  <div class="metric-bar-fill bar-quota" :style="{ width: Math.min(100, item.quotaPct) + '%' }"></div>
                                </div>
                              </div>
                            </td>
                            <td class="td-weight">
                              <div class="comp-metric-inline" :title="`【${item.name}】实际建议仓位: ${item.weightText}`">
                                <span class="weight-bold" :style="{ color: majorPalette[index % majorPalette.length] }">
                                  {{ item.weightText }}
                                </span>
                                <div class="metric-bar-track">
                                  <div
                                    class="metric-bar-fill bar-weight"
                                    :style="{
                                      width: Math.min(100, item.weightPct) + '%',
                                      background: 'linear-gradient(90deg, ' + majorPalette[index % majorPalette.length] + ', ' + majorPaletteLight[index % majorPaletteLight.length] + ')'
                                    }"
                                  ></div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 视图 2: 资产池与各周期风险预算配额配置 -->
            <div v-show="major.viewMode === 'config'" class="config-panel">
              <!-- 资产池定义 -->
              <div class="config-section">
                <div class="section-header">
                  <span class="section-title"><i class="el-icon-coin"></i> 资产池参数定义</span>
                  <el-tooltip
                    effect="dark"
                    content="基础大类资产已固定，不支持添加新参数"
                    placement="top"
                  >
                    <span>
                      <el-button size="mini" type="text" icon="el-icon-plus" disabled>添加资产</el-button>
                    </span>
                  </el-tooltip>
                </div>
                <div class="table-responsive">
                  <table class="custom-table asset-pool-table">
                    <thead>
                      <tr>
                        <th width="95">标识</th>
                        <th>标的资产 (代码：名称)</th>
                        <th width="70">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(info, key) in major.assetPool" :key="key">
                        <td><span class="param-tag">{{ formatMajorKey(key) }}</span></td>
                        <td>
                          <el-select
                            size="mini"
                            v-model="info.code"
                            placeholder="请选择资产"
                            filterable
                            style="width: 100%;"
                            @change="val => onMajorAssetChange(key, val)"
                          >
                            <el-option
                              v-for="opt in getAvailableMajorOptions(key)"
                              :key="opt.code"
                              :label="`${opt.code}：${opt.name}`"
                              :value="opt.code"
                            >
                              <span style="font-family: monospace; font-weight: 600; color: #6366f1;">{{ opt.code }}</span>
                              <span style="color: #94a3b8; margin: 0 4px;">：</span>
                              <span style="color: #334155; font-weight: 500;">{{ opt.name }}</span>
                            </el-option>
                          </el-select>
                        </td>
                        <td align="center">
                          <el-button
                            size="mini"
                            type="text"
                            icon="el-icon-delete"
                            class="delete-btn"
                            disabled
                          ></el-button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 周期阶段风险预算配额矩阵 -->
              <div class="config-section">
                <div class="section-header">
                  <span class="section-title">
                    <i class="el-icon-s-operation"></i> 宏观周期风险预算配额
                    <el-tooltip effect="dark" content="强制校验：每个阶段各项资产配额之和必须严格等于 1.0 (100%)" placement="top">
                      <i class="el-icon-warning-outline warning-icon"></i>
                    </el-tooltip>
                  </span>
                  <span class="quota-tip">各阶段总和须严格为 100%</span>
                </div>

                <div class="table-responsive">
                  <table class="custom-table quota-matrix-table">
                    <thead>
                      <tr>
                        <th width="120">周期阶段</th>
                        <th v-for="(info, key) in major.assetPool" :key="key" class="text-center" align="center">
                          {{ info.name || key }}
                        </th>
                        <th width="110" class="text-center" align="center">阶段配额总和</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="stage in stages" :key="stage">
                        <td class="stage-col">
                          <span class="stage-name">{{ stage }}</span>
                        </td>
                        <td v-for="(info, key) in major.assetPool" :key="key" class="number-cell text-center" align="center">
                          <el-input-number
                            size="mini"
                            v-model="major.cycleRbRules[stage][key]"
                            :min="0"
                            :max="1"
                            :step="0.05"
                            :precision="2"
                            :controls="false"
                            class="compact-input-number"
                          ></el-input-number>
                        </td>
                        <td align="center">
                          <el-tag
                            size="mini"
                            :type="isMajorStageValid(stage) ? 'success' : 'danger'"
                            effect="plain"
                            class="sum-tag"
                          >
                            {{ (getMajorStageSum(stage) * 100).toFixed(0) }}%
                            <i :class="isMajorStageValid(stage) ? 'el-icon-check' : 'el-icon-close'"></i>
                          </el-tag>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 强制校验告警与保存栏 -->
              <div class="config-footer">
                <div class="validation-msg">
                  <div v-if="major.isValid" class="valid-alert">
                    <i class="el-icon-circle-check"></i> 全部6个周期的风险预算配额总和均为 100%，符合要求
                  </div>
                  <div v-else class="invalid-alert">
                    <i class="el-icon-circle-close"></i>
                    <span>存在配额总和不等于 100% 的阶段：{{ getMajorInvalidStages().join('、') }}</span>
                  </div>
                </div>

                <div class="action-buttons">
                  <el-button size="small" @click="resetMajorDefaults">恢复默认</el-button>
                  <el-button
                    size="small"
                    type="primary"
                    icon="el-icon-refresh"
                    :disabled="!major.isValid"
                    :loading="major.loading"
                    @click="applyAndFetchMajor"
                  >
                    保存并重新计算
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 卡片 2: 动态板块超额风险预算 -->
      <el-col :span="12" class="budget-col">
        <el-card class="risk-budget-card" shadow="hover">
          <div slot="header" class="card-header">
            <div class="header-left">
              <div class="title-icon sector-icon">
                <i class="el-icon-data-analysis"></i>
              </div>
              <div class="title-text">
                <span class="title">
                  板块仓位建议
                  <el-tooltip effect="dark" content="基于自定义行业板块资产池与各宏观阶段的风险预算配额，通过动态风险预算优化求解各板块建议仓位" placement="top-start">
                    <i class="el-icon-question help-icon"></i>
                  </el-tooltip>
                </span>
                <div class="tags-row">
                  <el-tag v-if="sector.cycle" size="mini" effect="plain" class="cycle-tag sector-cycle-tag">{{ sector.cycle }}</el-tag>
                  <el-tag v-if="sector.endDate" size="mini" type="info" effect="plain" class="date-tag">
                    <i class="el-icon-date"></i> 截止日期: {{ sector.endDate }}
                  </el-tag>
                </div>
              </div>
            </div>

            <div class="header-right">
              <el-radio-group v-model="sector.viewMode" size="mini">
                <el-radio-button label="chart">
                  <i class="el-icon-data-line"></i> 建议仓位
                </el-radio-button>
                <el-radio-button label="config">
                  <i class="el-icon-setting"></i> 参数配置
                  <span v-if="!sector.isValid" class="badge-dot"></span>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>

          <div class="content-wrapper" v-loading="sector.loading" element-loading-text="动态模型计算中...">
            <!-- 视图 1: 仓位建议图表 -->
            <div v-show="sector.viewMode === 'chart'">
              <div v-if="sector.error" class="error-container">
                <i class="el-icon-warning-outline"></i>
                <p>{{ sector.error }}</p>
                <el-button size="small" type="primary" @click="fetchSectorData" round>重新加载</el-button>
              </div>

              <template v-if="!sector.error">
                <div class="dual-dashboard">
                  <!-- 左侧：左移聚焦的 ECharts 饼图 -->
                  <div class="chart-area">
                    <div ref="sectorChart" class="echarts-chart"></div>
                  </div>

                  <!-- 右侧：风险预算设定 vs 实际建议仓位鲜明对比面板 -->
                  <div class="comparison-panel">
                    <div class="comp-panel-header">
                      <div class="comp-panel-title">
                        <i class="el-icon-data-analysis comp-icon sector-comp-icon"></i>
                        <span class="comp-title-text">
                          当前<strong>【{{ sector.cycle || '最新周期' }}】</strong>风险预算 vs 建议仓位对比
                          <span v-if="sector.endDate" class="comp-date-tip">（截至 {{ sector.endDate }}）</span>
                        </span>
                      </div>
                      <div class="comp-header-actions">
                        <el-button
                          size="mini"
                          type="text"
                          icon="el-icon-edit"
                          class="comp-edit-btn sector-comp-edit-btn"
                          @click="sector.viewMode = 'config'"
                        >
                          修改配额
                        </el-button>
                        <el-tooltip effect="dark" content="导出完整对比图表与配额设定图片" placement="top">
                          <span class="comp-download-icon sector-comp-download-icon" @click="exportComprehensiveImage('sector')">
                            <i class="el-icon-download"></i>
                          </span>
                        </el-tooltip>
                      </div>
                    </div>

                    <div class="comp-table-container">
                      <table class="comp-table">
                        <thead>
                          <tr>
                            <th class="th-asset">标的板块</th>
                            <th class="th-quota">
                              <span>风险预算</span>
                              <el-tooltip effect="dark" content="当前宏观周期设定的目标风险预算配额" placement="top">
                                <i class="el-icon-info comp-tip-icon"></i>
                              </el-tooltip>
                            </th>
                            <th class="th-weight">
                              <span>建议仓位</span>
                              <el-tooltip effect="dark" content="基于模型优化求解计算出的最终建议超额持仓比例" placement="top">
                                <i class="el-icon-info comp-tip-icon"></i>
                              </el-tooltip>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(item, index) in sectorComparisonList"
                            :key="item.id"
                            class="comp-row"
                            :style="{ animationDelay: (index * 0.08) + 's' }"
                          >
                            <td class="td-asset">
                              <div class="comp-asset-cell">
                                <span class="comp-color-dot" :style="{ background: sectorPalette[index % sectorPalette.length] }"></span>
                                <span class="comp-asset-name" :title="item.name">{{ item.name }}</span>
                              </div>
                            </td>
                            <td class="td-quota">
                              <div class="comp-metric-inline" :title="`【${item.name}】目标风险预算: ${item.quotaText}`">
                                <span class="quota-pill">{{ item.quotaText }}</span>
                                <div class="metric-bar-track">
                                  <div class="metric-bar-fill bar-quota" :style="{ width: Math.min(100, item.quotaPct) + '%' }"></div>
                                </div>
                              </div>
                            </td>
                            <td class="td-weight">
                              <div class="comp-metric-inline" :title="`【${item.name}】实际建议仓位: ${item.weightText}`">
                                <span class="weight-bold" :style="{ color: sectorPalette[index % sectorPalette.length] }">
                                  {{ item.weightText }}
                                </span>
                                <div class="metric-bar-track">
                                  <div
                                    class="metric-bar-fill bar-weight"
                                    :style="{
                                      width: Math.min(100, item.weightPct) + '%',
                                      background: 'linear-gradient(90deg, ' + sectorPalette[index % sectorPalette.length] + ', ' + sectorPaletteLight[index % sectorPaletteLight.length] + ')'
                                    }"
                                  ></div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 视图 2: 资产池与各周期风险预算配额配置 -->
            <div v-show="sector.viewMode === 'config'" class="config-panel">
              <!-- 资产池定义 -->
              <div class="config-section">
                <div class="section-header">
                  <span class="section-title"><i class="el-icon-coin"></i> 板块资产池定义</span>
                  <el-tooltip
                    v-if="isSectorPoolFull"
                    effect="dark"
                    content="所有候选板块已全部添加至板块池"
                    placement="top"
                  >
                    <span>
                      <el-button size="mini" type="text" icon="el-icon-plus" disabled>添加板块</el-button>
                    </span>
                  </el-tooltip>
                  <el-button
                    v-else
                    size="mini"
                    type="text"
                    icon="el-icon-plus"
                    @click="addSectorAsset"
                  >添加板块</el-button>
                </div>
                <div class="table-responsive">
                  <table class="custom-table asset-pool-table">
                    <thead>
                      <tr>
                        <th width="80">标识</th>
                        <th>标的板块 (代码：名称)</th>
                        <th width="70">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(info, key) in sector.assetPool" :key="key">
                        <td><span class="param-tag sector-param-tag">{{ formatSectorKey(key) }}</span></td>
                        <td>
                          <el-select
                            size="mini"
                            v-model="info.code"
                            placeholder="请选择板块"
                            filterable
                            style="width: 100%;"
                            @change="val => onSectorAssetChange(key, val)"
                          >
                            <el-option
                              v-for="opt in getAvailableSectorOptions(key)"
                              :key="opt.code"
                              :label="`${opt.code}：${opt.name}`"
                              :value="opt.code"
                            >
                              <span style="font-family: monospace; font-weight: 600; color: #10b981;">{{ opt.code }}</span>
                              <span style="color: #94a3b8; margin: 0 4px;">：</span>
                              <span style="color: #334155; font-weight: 500;">{{ opt.name }}</span>
                            </el-option>
                          </el-select>
                        </td>
                        <td align="center">
                          <el-button
                            size="mini"
                            type="text"
                            icon="el-icon-delete"
                            class="delete-btn"
                            :disabled="Object.keys(sector.assetPool).length <= 2"
                            @click="removeSectorAsset(key)"
                          ></el-button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 周期阶段风险预算配额矩阵 -->
              <div class="config-section">
                <div class="section-header">
                  <span class="section-title">
                    <i class="el-icon-s-operation"></i> 宏观周期风险预算配额
                    <el-tooltip effect="dark" content="强制校验：每个阶段各板块配额之和必须严格等于 1.0 (100%)" placement="top">
                      <i class="el-icon-warning-outline warning-icon"></i>
                    </el-tooltip>
                  </span>
                  <span class="quota-tip">各阶段总和须严格为 100%</span>
                </div>

                <div class="table-responsive">
                  <table class="custom-table quota-matrix-table">
                    <thead>
                      <tr>
                        <th width="120">周期阶段</th>
                        <th v-for="(info, key) in sector.assetPool" :key="key" class="text-center" align="center">
                          {{ info.name || key }}
                        </th>
                        <th width="110" class="text-center" align="center">阶段配额总和</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="stage in stages" :key="stage">
                        <td class="stage-col">
                          <span class="stage-name">{{ stage }}</span>
                        </td>
                        <td v-for="(info, key) in sector.assetPool" :key="key" class="number-cell text-center" align="center">
                          <el-input-number
                            size="mini"
                            v-model="sector.cycleRbRules[stage][key]"
                            :min="0"
                            :max="1"
                            :step="0.05"
                            :precision="2"
                            :controls="false"
                            class="compact-input-number"
                          ></el-input-number>
                        </td>
                        <td align="center">
                          <el-tag
                            size="mini"
                            :type="isSectorStageValid(stage) ? 'success' : 'danger'"
                            effect="plain"
                            class="sum-tag"
                          >
                            {{ (getSectorStageSum(stage) * 100).toFixed(0) }}%
                            <i :class="isSectorStageValid(stage) ? 'el-icon-check' : 'el-icon-close'"></i>
                          </el-tag>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 强制校验告警与保存栏 -->
              <div class="config-footer">
                <div class="validation-msg">
                  <div v-if="sector.isValid" class="valid-alert">
                    <i class="el-icon-circle-check"></i> 全部6个周期的风险预算配额总和均为 100%，符合要求
                  </div>
                  <div v-else class="invalid-alert">
                    <i class="el-icon-circle-close"></i>
                    <span>存在配额总和不等于 100% 的阶段：{{ getSectorInvalidStages().join('、') }}</span>
                  </div>
                </div>

                <div class="action-buttons">
                  <el-button size="small" @click="resetSectorDefaults">恢复默认</el-button>
                  <el-button
                    size="small"
                    type="primary"
                    icon="el-icon-refresh"
                    :disabled="!sector.isValid"
                    :loading="sector.loading"
                    @click="applyAndFetchSector"
                  >
                    保存并重新计算
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
/**
 * @file DynamicRiskBudget.vue
 * @description 自定义动态风险预算模型（资产配置与板块超额配置总控）
 * 
 * 【设计定位与业务背景】：
 * 本组件基于宏观经济六周期（Pring 三因子划分模型），针对“大类资产配置”与“行业板块超额配置”两大投资维度，
 * 允许投研人员实时调整资产池定义以及 6 个宏观周期下的风险预算配额 (Risk Budget Rules)，
 * 并结合底层资产协方差矩阵与目标风险预算，通过 SLSQP 二次规划求解出各资产的最优配置建议仓位。
 * 
 * 【核心特性】：
 * 1. 双卡片协同：左侧为【资产仓位建议】（股票/债券/黄金/商品四大固定基石），右侧为【板块仓位建议】（中信一级行业动态增减）；
 * 2. 强校验与智能配平：强制校验全部 6 个周期的配额和必须等于 100%（容差 0.1%），并提供一键等比归一化配平算法；
 * 3. 约束注入：向底层求解器注入硬性边界约束（例如股票类资产权重上限限制在 20% 以内）；
 * 4. 交互式防溢出：悬浮提示框 (Tooltip) 搭载全智能视口边界感知反转算法，彻底杜绝屏幕边缘截断；
 * 5. 跨组件联动：通过 EventBus 将当前资产池与配额规则无缝同步至下方回测系统 (RiskBudgetBacktest.vue)；
 * 6. 高清导出：内置 2x Retina 双倍离屏 Canvas 渲染引擎，一键导出包含卡片全景、环形饼图与对比表格的精美 PNG 图片。
 */
import * as echarts from 'echarts'
import axios from 'axios'

/**
 * 六个宏观周期标准枚举名称（三因子符号组合：货币/信用/增长）
 */
const STAGES = [
  "阶段1-信用扩张", // 宽货币 + 宽信用 + 弱增长
  "阶段2-经济复苏", // 宽货币 + 宽信用 + 强增长
  "阶段3-货币退潮", // 紧货币 + 宽信用 + 强增长
  "阶段4-信用退潮", // 紧货币 + 紧信用 + 强增长
  "阶段5-经济放缓", // 紧货币 + 紧信用 + 弱增长
  "阶段6-货币扩张"  // 宽货币 + 紧信用 + 弱增长
]

/**
 * 默认大类资产池定义（四大固定底层基石）
 * stock: 权益类、bond: 固收类、gold: 贵金属类、commodity: 衍生转债类
 */
const DEFAULT_MAJOR_ASSET_POOL = {
  "stock": { "code": "H00852.SH", "name": "中证1000全收益" },
  "bond": { "code": "CBA00651.CS", "name": "中债-国债总财富(7-10年)指数" },
  "gold": { "code": "AU9999.SGE", "name": "SGE黄金9999" },
  "commodity": { "code": "000832.CSI", "name": "中证转债" }
}

/**
 * 默认大类资产在 6 个宏观周期下的目标风险预算配额 (Risk Budget Quotas)
 * 每一行代表一个周期的目标风险贡献比例，总和必须精确等于 1.0 (100%)
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
 * 默认行业板块资产池定义（基于中信一级产业风格指数）
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
 * 每一行各板块配额相加等于 1.0 (100%)
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
  name: 'DynamicRiskBudget',
  props: ['globalDateRange'],
  data() {
    return {
      /** @property {Array<Object>} candidateMajorAssets - 大类资产可选候选池列表（股票、国债、黄金、转债标的） */
      candidateMajorAssets: [],
      /** @property {Array<Object>} candidateSectorAssets - 行业板块可选候选池列表（中信消费、科技、周期、金融、稳定等） */
      candidateSectorAssets: [],
      /** @property {Array<string>} stages - 6个宏观周期标准名称数组常量 */
      stages: STAGES,
      
      /**
       * 大类资产配置模型状态机
       */
      major: {
        viewMode: 'chart', // 视图模式：'chart'（可视化图表与对比面板） | 'config'（资产池与周期配额编辑面板）
        loading: false,    // 模型异步求解中遮罩
        error: null,       // 接口错误提示信息
        cycle: '',         // 当前交易日所处的最新宏观周期阶段（如“阶段4-信用退潮”）
        positions: [],     // 风险预算模型求解出的各资产建议持仓权重数组 [{ id, code, name, weight }]
        chart: null,       // ECharts 饼图实例引用
        assetPool: JSON.parse(JSON.stringify(DEFAULT_MAJOR_ASSET_POOL)),       // 当前编辑/生效的大类资产池
        cycleRbRules: JSON.parse(JSON.stringify(DEFAULT_MAJOR_CYCLE_RB_RULES)), // 当前编辑/生效的各周期风险配额字典
        isValid: true,     // 6 个周期配额是否全部配平至 100%（true 才允许保存计算或同步回测）
        endDate: ''        // 资产建议仓位计算对应的截止日期（如 '2026-08-31'）
      },
      // 大类资产专属调色盘（渐变起始色与浅色终止色，保证色泽饱满且视觉温润）
      majorPalette: ['#5CA1FC', '#2BBCCF', '#F7DE54', '#4EE0B3', '#86CE46', '#FCA56E'],
      majorPaletteLight: ['#A9CDFE', '#9CE5ED', '#FDF0A8', '#A6F4DC', '#C6EEA0', '#FED9C0'],

      /**
       * 行业板块超额配置模型状态机
       */
      sector: {
        viewMode: 'chart', // 视图模式：'chart'（可视化图表与对比面板） | 'config'（资产池与周期配额编辑面板）
        loading: false,    // 模型异步求解中遮罩
        error: null,       // 接口错误提示信息
        cycle: '',         // 当前交易日所处的最新宏观周期阶段
        positions: [],     // 风险预算模型求解出的各行业板块建议持仓权重数组
        chart: null,       // ECharts 饼图实例引用
        assetPool: JSON.parse(JSON.stringify(DEFAULT_SECTOR_ASSET_POOL)),       // 当前编辑/生效的行业板块池
        cycleRbRules: JSON.parse(JSON.stringify(DEFAULT_SECTOR_CYCLE_RB_RULES)), // 当前编辑/生效的各周期风险配额字典
        isValid: true,     // 6 个周期配额是否全部配平至 100%
        endDate: ''        // 板块建议仓位计算对应的截止日期（如 '2026-08-31'）
      },
      // 行业板块专属调色盘（清新明快，与大类资产具有明确的视觉区分）
      sectorPalette: ['#5CA1FC', '#2BBCCF', '#4EE0B3', '#86CE46', '#F7DE54', '#FCA56E'],
      sectorPaletteLight: ['#A9CDFE', '#9CE5ED', '#A6F4DC', '#C6EEA0', '#FDF0A8', '#FED9C0']
    }
  },
  computed: {
    /**
     * 判断当前行业板块池是否已经占满了所有候选板块
     * 用于控制“添加板块”按钮的禁用状态与提示
     * @returns {boolean} 若所有候选板块均已加入板块池则返回 true，否则返回 false
     */
    isSectorPoolFull() {
      if (!this.sector || !this.sector.assetPool || !this.candidateSectorAssets.length) return false
      const currentCodes = Object.values(this.sector.assetPool).map(item => item && item.code).filter(Boolean)
      return this.candidateSectorAssets.every(item => currentCodes.includes(item.code))
    },

    /**
     * 大类资产风险预算与建议仓位对比列表
     * 整合当前宏观周期下的目标风险预算配额与优化求解出的实际建议仓位及偏离度
     */
    /**
     * 大类资产风险预算与建议仓位对比列表
     * 整合当前宏观周期下的目标风险预算配额与优化求解出的实际建议仓位及偏离度
     */
    majorComparisonList() {
      const cycle = this.major.cycle
      const rules = this.getMatchingCycleRules(cycle, this.major.cycleRbRules)
      const pool = this.major.assetPool || {}
      return (this.major.positions || []).map((item, index) => {
        let quota = 0
        if (rules) {
          if (rules[item.id] !== undefined) {
            quota = parseFloat(rules[item.id])
          } else {
            // 通过 assetPool 编码与名称进行容错回退匹配
            for (const k in pool) {
              if (pool[k] && (pool[k].code === item.code || pool[k].name === item.name || k === item.id)) {
                if (rules[k] !== undefined) {
                  quota = parseFloat(rules[k])
                  break
                }
              }
            }
          }
        }
        const weight = parseFloat(item.weight || 0)
        const quotaPct = parseFloat((quota * 100).toFixed(1))
        const weightPct = parseFloat((weight * 100).toFixed(2))
        const diff = parseFloat((weightPct - quotaPct).toFixed(2))
        return {
          ...item,
          index,
          quota,
          weight,
          quotaPct,
          weightPct,
          diff,
          quotaText: (quota * 100).toFixed(0) + '%',
          weightText: (weight * 100).toFixed(2) + '%'
        }
      })
    },

    /**
     * 行业板块风险预算与建议仓位对比列表
     * 整合当前宏观周期下的目标风险预算配额与优化求解出的实际建议仓位及偏离度
     */
    sectorComparisonList() {
      const cycle = this.sector.cycle
      const rules = this.getMatchingCycleRules(cycle, this.sector.cycleRbRules)
      const pool = this.sector.assetPool || {}
      return (this.sector.positions || []).map((item, index) => {
        let quota = 0
        if (rules) {
          if (rules[item.id] !== undefined) {
            quota = parseFloat(rules[item.id])
          } else {
            // 通过 assetPool 编码与名称进行容错回退匹配
            for (const k in pool) {
              if (pool[k] && (pool[k].code === item.code || pool[k].name === item.name || k === item.id)) {
                if (rules[k] !== undefined) {
                  quota = parseFloat(rules[k])
                  break
                }
              }
            }
          }
        }
        const weight = parseFloat(item.weight || 0)
        const quotaPct = parseFloat((quota * 100).toFixed(1))
        const weightPct = parseFloat((weight * 100).toFixed(2))
        const diff = parseFloat((weightPct - quotaPct).toFixed(2))
        return {
          ...item,
          index,
          quota,
          weight,
          quotaPct,
          weightPct,
          diff,
          quotaText: (quota * 100).toFixed(0) + '%',
          weightText: (weight * 100).toFixed(2) + '%'
        }
      })
    }
  },
  watch: {
    /**
     * 监听全局日期范围变化，当用户在顶部时间控件调整区间时，自动重新请求大类资产与行业板块数据
     * immediate: true 确保组件挂载时若已有日期即立即加载，无需再在 mounted 中重复调用
     */
    globalDateRange: {
      handler(newVal) {
        if (newVal && newVal.length === 2) {
          this.fetchMajorData()
          this.fetchSectorData()
        }
      },
      immediate: true
    },
    /**
     * 深度监听大类资产各周期风险预算配额变动，实时触发配额 100% 规则校验
     */
    'major.cycleRbRules': {
      handler() {
        this.validateMajorRules()
      },
      deep: true
    },
    /**
     * 深度监听行业板块各周期风险预算配额变动，实时触发配额 100% 规则校验
     */
    'sector.cycleRbRules': {
      handler() {
        this.validateSectorRules()
      },
      deep: true
    },
    /**
     * 监听大类资产视图模式切换（图表 / 参数配置）
     * 当切换回 'chart' 图表视图时，在 nextTick 中重新初始化并渲染 ECharts 实例
     */
    'major.viewMode'(newVal) {
      if (newVal === 'chart') {
        this.$nextTick(() => {
          this.initMajorChart()
          this.updateMajorChart()
        })
      }
    },
    /**
     * 监听行业板块视图模式切换（图表 / 参数配置）
     * 当切换回 'chart' 图表视图时，在 nextTick 中重新初始化并渲染 ECharts 实例
     */
    'sector.viewMode'(newVal) {
      if (newVal === 'chart') {
        this.$nextTick(() => {
          this.initSectorChart()
          this.updateSectorChart()
        })
      }
    }
  },
  mounted() {
    // 页面挂载时初始化候选资产清单、执行默认规则校验并绑定窗口缩放事件
    // fetchMajorData/fetchSectorData 由 watch globalDateRange (immediate:true) 负责触发，避免双重请求
    this.fetchCandidates()
    this.validateMajorRules()
    this.validateSectorRules()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    // 页面销毁前解绑窗口缩放监听并销毁 ECharts 实例以释放内存
    window.removeEventListener('resize', this.handleResize)
    if (this.major.chart) {
      this.major.chart.dispose()
      this.major.chart = null
    }
    if (this.sector.chart) {
      this.sector.chart.dispose()
      this.sector.chart = null
    }
  },
  methods: {
    /**
     * 响应窗口尺寸变化，动态对大类资产和行业板块的 ECharts 图表进行重绘适配
     */
    handleResize() {
      if (this.major.chart) this.major.chart.resize()
      if (this.sector.chart) this.sector.chart.resize()
    },

    /**
     * 智能匹配宏观周期阶段名称与风险预算配额字典
     * 兼容全称（如 "阶段4-信用退潮"）、简称（如 "信用退潮"）及模糊匹配，兜底返回有效规则
     */
    getMatchingCycleRules(cycle, rulesDict) {
      if (!rulesDict) return null
      if (cycle && rulesDict[cycle]) return rulesDict[cycle]
      if (cycle) {
        for (const k in rulesDict) {
          if (k.includes(cycle) || cycle.includes(k) || k.replace(/阶段\d-?/, '') === cycle.replace(/阶段\d-?/, '')) {
            return rulesDict[k]
          }
        }
      }
      // 容错降级：优先匹配 "信用退潮" 或首个有效阶段
      const fallbackKey = Object.keys(rulesDict).find(k => k.includes('信用退潮')) || Object.keys(rulesDict)[0]
      return fallbackKey ? rulesDict[fallbackKey] : null
    },

    /**
     * 从后端 Java 接口异步获取候选大类资产与行业板块清单
     * 请求失败时自动采用预置的默认候选清单兜底，保证前端下拉切换功能始终可用
     */
    fetchCandidates() {
      // 假设使用同一端口或通过代理，您可以根据实际情况修改
      axios.post('/api/returns/candidates').then(res => {
         if (res.data) {
           this.candidateMajorAssets = res.data.candidateMajorAssets || [];
           this.candidateSectorAssets = res.data.candidateSectorAssets || [];
         }
      }).catch(e => {
         console.error('Failed to fetch candidates from java api', e);
         // 兜底逻辑
         this.candidateMajorAssets = [
           { code: "H00852.SH", name: "中证1000全收益" },
           { code: "H00300.CSI", name: "300收益" },
           { code: "CBA00651.CS", name: "中债-国债总财富(7-10年)指数" },
           { code: "CBA00621.CS", name: "中债-国债总财富(1-3年)指数" },
           { code: "AU9999.SGE", name: "SGE黄金9999" },
           { code: "000832.CSI", name: "中证转债" }
         ];
         this.candidateSectorAssets = [
           { code: "CI005919.WI", name: "消费(风格.中信)" },
           { code: "CI005929.WI", name: "科技产业(中信)" },
           { code: "CI005925.WI", name: "周期产业(中信)" },
           { code: "CI005931.WI", name: "金融产业(中信)" },
           { code: "CI005921.WI", name: "稳定(风格.中信)" },
           { code: "881001.WI", name: "万得全A" }
         ];
      })
    },

    // ================= 大类资产逻辑 (stock_returns) =================
    /**
     * 格式化大类资产标识为中文名称
     * @param {string} key - 大类资产槽位标识（'stock' | 'bond' | 'gold' | 'commodity'）
     * @returns {string} 对应的中文分类名称
     */
    formatMajorKey(key) {
      const map = {
        'stock': '权益类',
        'bond': '固收类',
        'gold': '贵金属类',
        'commodity': '衍生转债类'
      }
      return map[key] || key
    },

    /**
     * 计算大类资产在指定宏观周期阶段下的所有资产风险预算配额之和
     * @param {string} stage - 宏观周期阶段名称（如 "阶段1-信用扩张"）
     * @returns {number} 配额总和（保留4位小数以消除浮点数累加误差）
     */
    getMajorStageSum(stage) {
      const rules = this.major.cycleRbRules[stage] || {}
      let total = 0
      Object.keys(this.major.assetPool).forEach(key => {
        total += parseFloat(rules[key] || 0)
      })
      return parseFloat(total.toFixed(4))
    },

    /**
     * 校验大类资产在指定宏观周期阶段下的配额总和是否等于 100% (1.0)
     * @param {string} stage - 宏观周期阶段名称
     * @returns {boolean} 若总和在 [0.999, 1.001] 浮点误差容差范围内返回 true，否则返回 false
     */
    isMajorStageValid(stage) {
      const sum = this.getMajorStageSum(stage)
      return Math.abs(sum - 1.0) <= 0.001
    },

    /**
     * 筛选出大类资产中所有配额之和不等于 100% 的未配平宏观周期阶段列表
     * @returns {Array<string>} 未配平的宏观周期阶段名称数组（用于在页面中高亮标红并告警提示）
     */
    getMajorInvalidStages() {
      return this.stages.filter(s => !this.isMajorStageValid(s))
    },

    /**
     * 整体校验大类资产 6 个周期的配额规则合法性
     * 更新 major.isValid 状态（当所有阶段配额之和均为 100% 时为 true，允许保存计算）
     */
    validateMajorRules() {
      this.major.isValid = this.getMajorInvalidStages().length === 0
    },

    /**
     * 对指定宏观周期阶段的大类资产风险预算配额进行等比归一化自动配平至 100%
     * 处理尾数凑整以保证各资产权重之和精确等于 1.0
     * @param {string} stage - 需要自动配平的宏观周期阶段名称
     */
    normalizeMajorStage(stage) {
      const rules = this.major.cycleRbRules[stage]
      const keys = Object.keys(this.major.assetPool)
      let sum = 0
      keys.forEach(k => { sum += parseFloat(rules[k] || 0) })
      if (sum <= 0) {
        const equalVal = parseFloat((1.0 / keys.length).toFixed(2))
        keys.forEach(k => { this.$set(rules, k, equalVal) })
      } else {
        let runningSum = 0
        keys.forEach((k, idx) => {
          if (idx === keys.length - 1) {
            const finalVal = parseFloat((1.0 - runningSum).toFixed(2))
            this.$set(rules, k, Math.max(0, finalVal))
          } else {
            const normalized = parseFloat(((parseFloat(rules[k] || 0) / sum)).toFixed(2))
            runningSum += normalized
            this.$set(rules, k, normalized)
          }
        })
      }
      this.validateMajorRules()
      this.$message.success(`已为【${stage}】自动按比例配平至 100%`)
    },

    /**
     * 获取指定大类资产槽位允许选择的候选标的列表
     * 业务分类限制规则：
     * - stock（股票类）：仅允许选择中证1000全收益或300收益
     * - bond（债券类）：仅允许选择中债7-10年或中债1-3年
     * - gold（黄金类）：仅允许选择SGE黄金9999
     * - commodity（商品类）：仅允许选择中证转债
     * @param {string} currentKey - 资产槽位标识 ('stock' | 'bond' | 'gold' | 'commodity')
     * @returns {Array<Object>} 过滤后的该类别可用候选标的数组
     */
    getAvailableMajorOptions(currentKey) {
      let list = []
      const matchCode = (item, ...targets) => targets.some(t => item.code && (item.code.toUpperCase() === t.toUpperCase() || item.code.toLowerCase() === t.toLowerCase()))
      if (currentKey === 'stock') {
        list = this.candidateMajorAssets.filter(item => matchCode(item, 'H00852.SH', 'H00300.CSI', 'h00852_sh', 'h00300_csi'))
      } else if (currentKey === 'bond') {
        list = this.candidateMajorAssets.filter(item => matchCode(item, 'CBA00651.CS', 'CBA00621.CS', 'cba00651_cs', 'cba00621_cs'))
      } else if (currentKey === 'gold') {
        list = this.candidateMajorAssets.filter(item => matchCode(item, 'AU9999.SGE', 'au9999_sge'))
      } else if (currentKey === 'commodity') {
        list = this.candidateMajorAssets.filter(item => matchCode(item, '000832.CSI', 'idx_000832_csi'))
      } else {
        list = [...this.candidateMajorAssets]
      }
      return list
    },

    /**
     * 响应大类资产下拉框切换标的选择，同步更新资产池对应槽位的代码与中文名称
     * @param {string} key - 大类资产槽位标识（'stock' | 'bond' | 'gold' | 'commodity'）
     * @param {string} newCode - 用户选中的新资产标的代码
     */
    onMajorAssetChange(key, newCode) {
      const candidate = this.candidateMajorAssets.find(item => item.code === newCode)
      const name = candidate ? candidate.name : (this.major.assetPool[key] ? this.major.assetPool[key].name : newCode)
      this.$set(this.major.assetPool, key, {
        code: newCode,
        name: name
      })
    },

    /**
     * 添加大类资产槽位响应方法（大类资产四大底层架构固定，提示不支持动态增减）
     */
    addMajorAsset() {
      this.$message.warning('大类资产参数配置已固定，不支持添加新资产')
    },

    /**
     * 删除大类资产槽位响应方法（大类资产四大底层架构固定，提示不支持动态增减）
     * @param {string} key - 待删除的资产槽位标识
     */
    removeMajorAsset(key) {
      this.$message.warning('大类资产参数配置已固定，不支持删除资产')
    },

    /**
     * 重置大类资产配置，恢复资产池定义和 6 个宏观周期的风险预算配额为系统初始默认值
     */
    resetMajorDefaults() {
      this.major.assetPool = JSON.parse(JSON.stringify(DEFAULT_MAJOR_ASSET_POOL))
      this.major.cycleRbRules = JSON.parse(JSON.stringify(DEFAULT_MAJOR_CYCLE_RB_RULES))
      this.validateMajorRules()
      this.$message.info('大类资产配置参数已恢复为默认值')
    },

    /**
     * 校验并应用大类资产自定义配置，自动切换至图表视图并向后端同时发起仓位建议与策略回测计算
     * 校验逻辑：
     * 1. 检查全部 6 个周期的配额和是否均等于 100%；
     * 2. 检查各资产槽位是否均有效绑定了标的代码。
     */
    applyAndFetchMajor() {
      this.validateMajorRules()
      if (!this.major.isValid) {
        this.$message.error('存在配额之和不等于 100% 的周期阶段，无法计算')
        return
      }
      const hasEmpty = Object.values(this.major.assetPool).some(item => !item || !item.code)
      if (hasEmpty) {
        this.$message.error('存在未选择标的代码的资产参数，请选择后再计算')
        return
      }
      // 1. 切换至图表模式并触发仓位建议求解接口
      this.major.viewMode = 'chart'
      this.fetchMajorData()

      // 2. 同步触发大类资产回测测算接口
      this.syncAndRunBacktest('major')
    },

    /**
     * 请求后端动态风险预算算法接口（大类资产：统一使用纵表 stock_returns）
     * 提交参数包含：
     * - asset_pool: 资产定义（stock, bond, gold, commodity）
     * - cycle_rb_rules: 6 个宏观周期的风险预算配额
     * - data_table: 'stock_returns'
     * - end_date: 全局截止日期
     * - custom_bounds: 硬性约束（例如股票资产仓位上限约束在 20% 以内：[0.0, 0.2]）
     * 请求成功后更新当前周期与建议仓位权重列表，并重新渲染 ECharts 饼图
     */
    fetchMajorData() {
      const self = this
      self.major.loading = true
      self.major.error = null

      const endDate = self.globalDateRange ? self.globalDateRange[1] : null
      const payload = {
        asset_pool: self.major.assetPool,
        cycle_rb_rules: self.major.cycleRbRules,
        data_table: 'stock_returns',
        end_date: endDate,
        custom_bounds: { "stock": [0.0, 0.2] }
      }

      const apiHost = window.location.hostname || 'localhost'
      axios.post(`http://${apiHost}:8000/api/dynamic-risk-budget`, payload)
        .then(res => {
          self.major.loading = false
          if (res.data && res.data.success) {
            const dataObj = res.data.data || {}
            self.major.cycle = dataObj.current_cycle || dataObj.cycle || ''
            self.major.positions = dataObj.positions || []
            self.major.endDate = dataObj.calc_date || dataObj.end_date || endDate || ''
            self.$nextTick(() => {
              self.initMajorChart()
              self.updateMajorChart()
            })
          } else {
            self.major.error = '数据加载失败: ' + (res.data ? res.data.message : '未知错误')
          }
        })
        .catch(err => {
          self.major.loading = false
          self.major.error = '无法连接到动态风险预算服务，请确认 API 服务 (api.py) 已启动'
          console.error('Major Dynamic Risk Budget Error:', err)
        })
    },

    /**
     * 初始化大类资产建议仓位 ECharts 饼图实例（若 DOM 已就绪且尚未初始化）
     */
    initMajorChart() {
      if (!this.$refs.majorChart) return
      if (!this.major.chart) {
        this.major.chart = echarts.init(this.$refs.majorChart)
      }
    },

    /**
     * 组装配置项并渲染大类资产建议仓位 ECharts 饼图
     * 配置包含：线性渐变色彩、圆角边框、自定义 Tooltip 悬浮框、百分比引导线标签及弹性动效
     */
    updateMajorChart() {
      if (!this.major.chart || this.major.positions.length === 0) return

      const self = this
      const chartData = this.major.positions.map((item, i) => {
        return {
          name: item.name,
          value: parseFloat((item.weight * 100).toFixed(2)),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: self.majorPalette[i % self.majorPalette.length] },
              { offset: 1, color: self.majorPaletteLight[i % self.majorPaletteLight.length] }
            ])
          }
        }
      })

      const option = {
        tooltip: {
          trigger: 'item',
          confine: false,
          appendToBody: true,
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          borderColor: '#eee',
          borderWidth: 1,
          padding: [12, 16],
          textStyle: { color: '#333', fontSize: 13 },
          extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 8px; pointer-events: none; z-index: 9999;',
          position: (point, params, dom, rect, size) => {
            const boxW = (size && size.contentSize) ? size.contentSize[0] : 180;
            const boxH = (size && size.contentSize) ? size.contentSize[1] : 80;

            // 优先置于鼠标右侧 16px，垂直居中
            let posX = point[0] + 16;
            let posY = point[1] - boxH / 2;

            const chartEl = self.$refs.majorChart;
            if (chartEl && chartEl.getBoundingClientRect) {
              const cRect = chartEl.getBoundingClientRect();
              // 若向右展示超出屏幕视口右边界，则翻转至鼠标左侧
              if (cRect.left + posX + boxW > window.innerWidth - 10) {
                posX = point[0] - boxW - 16;
              }
              // 若向左展示超出屏幕视口左边界（如左侧切边），强制推入视口内（保留 12px 安全边距）
              if (cRect.left + posX < 12) {
                posX = 12 - cRect.left;
              }
              // 垂直方向防溢出视口顶部与底部
              if (cRect.top + posY < 12) {
                posY = 12 - cRect.top;
              } else if (cRect.top + posY + boxH > window.innerHeight - 12) {
                posY = window.innerHeight - 12 - boxH - cRect.top;
              }
            }
            return [posX, posY];
          },
          formatter: params => {
            const color = self.majorPalette[params.dataIndex % self.majorPalette.length]
            const item = self.major.positions[params.dataIndex]
            const cycle = self.major.cycle
            const rules = (cycle && self.major.cycleRbRules) ? self.major.cycleRbRules[cycle] : null
            const quota = (rules && item && rules[item.id] !== undefined) ? ((rules[item.id] || 0) * 100).toFixed(0) + '%' : '-'
            return `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:${color}"></span>` +
              `<strong>${params.name}</strong><br/>` +
              `<div style="margin-top:6px;display:flex;flex-direction:column;gap:3px;font-size:12px;">` +
              `<span>实际建议仓位：<strong style="color:${color};font-size:16px;">${params.value}%</strong></span>` +
              `<span>目标风险预算：<strong style="color:#64748b;">${quota}</strong></span>` +
              `</div>`
          }
        },
        series: [
          {
            name: '大类资产仓位',
            type: 'pie',
            radius: '46%',
            center: ['50%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: {
              borderRadius: 6,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: true,
              position: 'outside',
              formatter: params => {
                const name = params.name.length > 8 ? (params.name.slice(0, 7) + '..') : params.name
                return `${name}\n${params.percent}%`
              },
              color: '#475569',
              fontSize: 11,
              fontWeight: 500
            },
            labelLine: {
              show: true,
              smooth: true,
              length: 4,
              length2: 5
            },
            emphasis: {
              scale: true,
              scaleSize: 8,
              itemStyle: {
                shadowBlur: 20,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)'
              }
            },
            animationType: 'scale',
            animationEasing: 'elasticOut',
            data: chartData
          }
        ]
      }
      this.major.chart.setOption(option, true)
    },

    // ================= 板块超额逻辑 (stock_returns) =================
    /**
     * 格式化行业板块标识为中文名称
     * @param {string} key - 板块参数键名（如 'param1'）
     * @returns {string} 对应的中文参数名称（如 '参数1'）
     */
    formatSectorKey(key) {
      if (!key) return ''
      return key.replace(/^param(\d+)$/i, '参数$1')
    },

    /**
     * 计算行业板块在指定宏观周期阶段下的所有板块风险预算配额之和
     * @param {string} stage - 宏观周期阶段名称（如 "阶段1-信用扩张"）
     * @returns {number} 配额总和（保留4位小数以消除浮点数累加误差）
     */
    getSectorStageSum(stage) {
      const rules = this.sector.cycleRbRules[stage] || {}
      let total = 0
      Object.keys(this.sector.assetPool).forEach(key => {
        total += parseFloat(rules[key] || 0)
      })
      return parseFloat(total.toFixed(4))
    },

    /**
     * 校验行业板块在指定宏观周期阶段下的配额总和是否等于 100% (1.0)
     * @param {string} stage - 宏观周期阶段名称
     * @returns {boolean} 若总和在 [0.999, 1.001] 浮点误差容差范围内返回 true，否则返回 false
     */
    isSectorStageValid(stage) {
      const sum = this.getSectorStageSum(stage)
      return Math.abs(sum - 1.0) <= 0.001
    },

    /**
     * 筛选出行业板块中所有配额之和不等于 100% 的未配平宏观周期阶段列表
     * @returns {Array<string>} 未配平的宏观周期阶段名称数组（用于在页面中高亮标红并告警提示）
     */
    getSectorInvalidStages() {
      return this.stages.filter(s => !this.isSectorStageValid(s))
    },

    /**
     * 整体校验行业板块 6 个周期的配额规则合法性
     * 更新 sector.isValid 状态（当所有阶段配额之和均为 100% 时为 true，允许保存计算）
     */
    validateSectorRules() {
      this.sector.isValid = this.getSectorInvalidStages().length === 0
    },

    /**
     * 对指定宏观周期阶段的行业板块风险预算配额进行等比归一化自动配平至 100%
     * 处理尾数凑整以保证各板块权重之和精确等于 1.0
     * @param {string} stage - 需要自动配平的宏观周期阶段名称
     */
    normalizeSectorStage(stage) {
      const rules = this.sector.cycleRbRules[stage]
      const keys = Object.keys(this.sector.assetPool)
      let sum = 0
      keys.forEach(k => { sum += parseFloat(rules[k] || 0) })
      if (sum <= 0) {
        const equalVal = parseFloat((1.0 / keys.length).toFixed(2))
        keys.forEach(k => { this.$set(rules, k, equalVal) })
      } else {
        let runningSum = 0
        keys.forEach((k, idx) => {
          if (idx === keys.length - 1) {
            const finalVal = parseFloat((1.0 - runningSum).toFixed(2))
            this.$set(rules, k, Math.max(0, finalVal))
          } else {
            const normalized = parseFloat(((parseFloat(rules[k] || 0) / sum)).toFixed(2))
            runningSum += normalized
            this.$set(rules, k, normalized)
          }
        })
      }
      this.validateSectorRules()
      this.$message.success(`已为【${stage}】自动按比例配平至 100%`)
    },

    /**
     * 获取指定行业板块槽位允许选择的候选标的列表
     * 互斥过滤规则：动态排除已被其他板块槽位占用的标的，防止不同槽位重复选同一板块；同时保留当前槽位已选标的
     * @param {string} currentKey - 当前板块槽位标识（如 'param1'）
     * @returns {Array<Object>} 过滤后的可用行业板块候选标的数组
     */
    getAvailableSectorOptions(currentKey) {
      const selectedCodesByOthers = Object.keys(this.sector.assetPool)
        .filter(k => k !== currentKey)
        .map(k => this.sector.assetPool[k] && this.sector.assetPool[k].code)
        .filter(Boolean)
      const list = this.candidateSectorAssets.filter(item => !selectedCodesByOthers.includes(item.code))
      const currentItem = this.sector.assetPool[currentKey]
      if (currentItem && currentItem.code) {
        const exists = list.some(item => item.code === currentItem.code)
        if (!exists) {
          list.unshift({
            code: currentItem.code,
            name: currentItem.name || currentItem.code
          })
        }
      }
      return list
    },

    /**
     * 响应行业板块下拉框切换标的选择，同步更新板块池对应槽位的代码与中文名称
     * @param {string} key - 板块槽位标识（如 'param1'）
     * @param {string} newCode - 用户选中的新板块标的代码
     */
    onSectorAssetChange(key, newCode) {
      const candidate = this.candidateSectorAssets.find(item => item.code === newCode)
      const name = candidate ? candidate.name : (this.sector.assetPool[key] ? this.sector.assetPool[key].name : newCode)
      this.$set(this.sector.assetPool, key, {
        code: newCode,
        name: name
      })
    },

    /**
     * 向行业板块池中添加新板块槽位
     * 业务逻辑：
     * 1. 查找尚未加入板块池的空闲候选标的；
     * 2. 自动生成自增参数标识符（如 'param6'）；
     * 3. 在所有 6 个宏观周期规则中将该新板块配额初始化为 0.0；
     * 4. 重新触发配额合法性校验。
     */
    addSectorAsset() {
      const currentCodes = Object.values(this.sector.assetPool).map(item => item && item.code).filter(Boolean)
      const unused = this.candidateSectorAssets.find(item => !currentCodes.includes(item.code))
      if (!unused) {
        this.$message.warning('所有候选板块均已添加到板块池中')
        return
      }
      let newIndex = 1
      while (this.sector.assetPool[`param${newIndex}`]) {
        newIndex++
      }
      const newKey = `param${newIndex}`
      this.$set(this.sector.assetPool, newKey, { code: unused.code, name: unused.name })
      this.stages.forEach(stage => {
        this.$set(this.sector.cycleRbRules[stage], newKey, 0.0)
      })
      this.validateSectorRules()
    },

    /**
     * 从行业板块池中移除指定的板块槽位
     * 业务约束：至少保留 2 个板块以构成多资产组合；
     * 移除后同步从 6 个宏观周期规则中清理对应字段，并重新执行合法性校验
     * @param {string} key - 待移除的板块槽位标识（如 'param1'）
     */
    removeSectorAsset(key) {
      if (Object.keys(this.sector.assetPool).length <= 2) {
        this.$message.warning('至少需要保留 2 个板块以构成组合')
        return
      }
      this.$delete(this.sector.assetPool, key)
      this.stages.forEach(stage => {
        this.$delete(this.sector.cycleRbRules[stage], key)
      })
      this.validateSectorRules()
    },

    /**
     * 重置行业板块配置，恢复板块池定义和 6 个宏观周期的风险预算配额为系统初始默认值
     */
    resetSectorDefaults() {
      this.sector.assetPool = JSON.parse(JSON.stringify(DEFAULT_SECTOR_ASSET_POOL))
      this.sector.cycleRbRules = JSON.parse(JSON.stringify(DEFAULT_SECTOR_CYCLE_RB_RULES))
      this.validateSectorRules()
      this.$message.info('板块超额配置参数已恢复为默认值')
    },

    /**
     * 校验并应用行业板块自定义配置，自动切换至图表视图并向后端发起重新计算
     * 校验逻辑：
     * 1. 检查全部 6 个周期的配额和是否均等于 100%；
     * 2. 检查各板块槽位是否均有效绑定了标的代码。
     */
    applyAndFetchSector() {
      this.validateSectorRules()
      if (!this.sector.isValid) {
        this.$message.error('存在配额之和不等于 100% 的周期阶段，无法计算')
        return
      }
      const hasEmpty = Object.values(this.sector.assetPool).some(item => !item || !item.code)
      if (hasEmpty) {
        this.$message.error('存在未选择标的代码的板块参数，请选择后再计算')
        return
      }
      // 1. 切换至图表模式并触发板块仓位建议求解接口
      this.sector.viewMode = 'chart'
      this.fetchSectorData()

      // 2. 同步触发行业板块回测测算接口
      this.syncAndRunBacktest('sector')
    },

    /**
     * 请求后端动态风险预算算法接口（行业板块超额：统一使用纵表 stock_returns）
     * 提交板块池定义与各周期配额，计算最新宏观周期建议仓位并刷新饼图
     */
    fetchSectorData() {
      const self = this
      self.sector.loading = true
      self.sector.error = null

      const endDate = self.globalDateRange ? self.globalDateRange[1] : null
      const payload = {
        asset_pool: self.sector.assetPool,
        cycle_rb_rules: self.sector.cycleRbRules,
        data_table: 'stock_returns',
        end_date: endDate
      }

      const apiHost = window.location.hostname || 'localhost'
      axios.post(`http://${apiHost}:8000/api/dynamic-risk-budget`, payload)
        .then(res => {
          self.sector.loading = false
          if (res.data && res.data.success) {
            const dataObj = res.data.data || {}
            self.sector.cycle = dataObj.current_cycle || dataObj.cycle || ''
            self.sector.positions = dataObj.positions || []
            self.sector.endDate = dataObj.calc_date || dataObj.end_date || endDate || ''
            self.$nextTick(() => {
              self.initSectorChart()
              self.updateSectorChart()
            })
          } else {
            self.sector.error = '数据加载失败: ' + (res.data ? res.data.message : '未知错误')
          }
        })
        .catch(err => {
          self.sector.loading = false
          self.sector.error = '无法连接到动态风险预算服务，请确认 API 服务 (api.py) 已启动'
          console.error('Sector Dynamic Risk Budget Error:', err)
        })
    },

    /**
     * 初始化行业板块建议仓位 ECharts 饼图实例（若 DOM 已就绪且尚未初始化）
     */
    initSectorChart() {
      if (!this.$refs.sectorChart) return
      if (!this.sector.chart) {
        this.sector.chart = echarts.init(this.$refs.sectorChart)
      }
    },

    /**
     * 组装配置项并渲染行业板块建议仓位 ECharts 饼图
     * 配置包含：清新绿色系渐变色彩、圆角边框、自定义 Tooltip 悬浮框、百分比引导线标签及弹性动效
     */
    updateSectorChart() {
      if (!this.sector.chart || this.sector.positions.length === 0) return

      const self = this
      const chartData = this.sector.positions.map((item, i) => {
        return {
          name: item.name,
          value: parseFloat((item.weight * 100).toFixed(2)),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: self.sectorPalette[i % self.sectorPalette.length] },
              { offset: 1, color: self.sectorPaletteLight[i % self.sectorPaletteLight.length] }
            ])
          }
        }
      })

      const option = {
        tooltip: {
          trigger: 'item',
          confine: false,
          appendToBody: true,
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          borderColor: '#eee',
          borderWidth: 1,
          padding: [12, 16],
          textStyle: { color: '#333', fontSize: 13 },
          extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 8px; pointer-events: none; z-index: 9999;',
          position: (point, params, dom, rect, size) => {
            const boxW = (size && size.contentSize) ? size.contentSize[0] : 180;
            const boxH = (size && size.contentSize) ? size.contentSize[1] : 80;

            // 优先置于鼠标右侧 16px，垂直居中
            let posX = point[0] + 16;
            let posY = point[1] - boxH / 2;

            const chartEl = self.$refs.sectorChart;
            if (chartEl && chartEl.getBoundingClientRect) {
              const cRect = chartEl.getBoundingClientRect();
              // 若向右展示超出屏幕视口右边界，则翻转至鼠标左侧
              if (cRect.left + posX + boxW > window.innerWidth - 10) {
                posX = point[0] - boxW - 16;
              }
              // 若向左展示超出屏幕视口左边界（如左侧切边），强制推入视口内（保留 12px 安全边距）
              if (cRect.left + posX < 12) {
                posX = 12 - cRect.left;
              }
              // 垂直方向防溢出视口顶部与底部
              if (cRect.top + posY < 12) {
                posY = 12 - cRect.top;
              } else if (cRect.top + posY + boxH > window.innerHeight - 12) {
                posY = window.innerHeight - 12 - boxH - cRect.top;
              }
            }
            return [posX, posY];
          },
          formatter: params => {
            const color = self.sectorPalette[params.dataIndex % self.sectorPalette.length]
            const item = self.sector.positions[params.dataIndex]
            const cycle = self.sector.cycle
            const rules = (cycle && self.sector.cycleRbRules) ? self.sector.cycleRbRules[cycle] : null
            const quota = (rules && item && rules[item.id] !== undefined) ? ((rules[item.id] || 0) * 100).toFixed(0) + '%' : '-'
            return `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:${color}"></span>` +
              `<strong>${params.name}</strong><br/>` +
              `<div style="margin-top:6px;display:flex;flex-direction:column;gap:3px;font-size:12px;">` +
              `<span>实际建议仓位：<strong style="color:${color};font-size:16px;">${params.value}%</strong></span>` +
              `<span>目标风险预算：<strong style="color:#64748b;">${quota}</strong></span>` +
              `</div>`
          }
        },
        series: [
          {
            name: '板块配置仓位',
            type: 'pie',
            radius: '46%',
            center: ['50%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: {
              borderRadius: 6,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: true,
              position: 'outside',
              formatter: params => {
                const name = params.name.length > 8 ? (params.name.slice(0, 7) + '..') : params.name
                return `${name}\n${params.percent}%`
              },
              color: '#475569',
              fontSize: 11,
              fontWeight: 500
            },
            labelLine: {
              show: true,
              smooth: true,
              length: 4,
              length2: 5
            },
            emphasis: {
              scale: true,
              scaleSize: 8,
              itemStyle: {
                shadowBlur: 20,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)'
              }
            },
            animationType: 'scale',
            animationEasing: 'elasticOut',
            data: chartData
          }
        ]
      }
      this.sector.chart.setOption(option, true)
    },

    // ================= 完整卡片高分辨率 Canvas 图片导出 =================
    /**
     * Canvas 绘制圆角矩形通用辅助方法
     * @param {CanvasRenderingContext2D} ctx - HTML5 Canvas 2D 绘图上下文
     * @param {number} x - 矩形左上角 X 轴像素坐标
     * @param {number} y - 矩形左上角 Y 轴像素坐标
     * @param {number} width - 矩形总宽度
     * @param {number} height - 矩形总高度
     * @param {number} radius - 圆角半径大小
     * @param {string|CanvasGradient} [fill] - 填充颜色或渐变对象（可选）
     * @param {string} [stroke] - 边框描边颜色（可选）
     */
    drawRoundedRect(ctx, x, y, width, height, radius, fill, stroke) {
      ctx.beginPath()
      ctx.moveTo(x + radius, y)
      ctx.lineTo(x + width - radius, y)
      ctx.arcTo(x + width, y, x + width, y + height, radius)
      ctx.arcTo(x + width, y + height, x, y + height, radius)
      ctx.arcTo(x, y + height, x, y, radius)
      ctx.arcTo(x, y, x + width, y, radius)
      ctx.closePath()
      if (fill) {
        ctx.fillStyle = fill
        ctx.fill()
      }
      if (stroke) {
        ctx.strokeStyle = stroke
        ctx.stroke()
      }
    },

    /**
     * 合成并导出高清晰度（2x Retina）卡片全景 PNG 截图
     * 绘制流程包括：
     * 1. 创建双倍分辨率离屏 Canvas 消除高清屏模糊；
     * 2. 绘制白色圆角卡片背景与精美阴影外框；
     * 3. 绘制顶部专属品牌 Header、模块标题与当前周期阶段胶囊标签；
     * 4. 提取当前 ECharts 饼图的高清 Base64 并绘制于左侧；
     * 5. 在右侧按序绘制资产色标、名称、数值占比与渐变横向进度条；
     * 6. 在底部绘制当前宏观周期下的各资产风险预算配额明细条；
     * 7. 生成 PNG 格式 DataURL 并触发客户端下载。
     * @param {string} type - 导出类型：'major'（大类资产建议仓位）或 'sector'（板块建议超额仓位）
     */
    exportComprehensiveImage(type) {
      const isMajor = type === 'major'
      const state = isMajor ? this.major : this.sector
      const title = isMajor ? '资产仓位建议' : '板块仓位建议'
      const palette = isMajor ? this.majorPalette : this.sectorPalette
      const paletteLight = isMajor ? this.majorPaletteLight : this.sectorPaletteLight

      if (!state.chart) {
        this.$message.warning('图表正在加载中，请稍候')
        return
      }

      // 获取当前 ECharts 饼图的高清 Base64 (设置 pixelRatio: 3 保证高清不失真)
      const chartImgUri = state.chart.getDataURL({
        pixelRatio: 3,
        backgroundColor: '#ffffff'
      })

      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        const scale = 2
        const width = 960
        const height = 480

        canvas.width = width * scale
        canvas.height = height * scale
        ctx.scale(scale, scale)

        // 1. 绘制卡片背景与外边框
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, width, height)
        this.drawRoundedRect(ctx, 1, 1, width - 2, height - 2, 12, '#ffffff', '#e2e8f0')

        // 2. 绘制卡片顶部标题栏
        const iconGrad = ctx.createLinearGradient(24, 20, 56, 52)
        if (isMajor) {
          iconGrad.addColorStop(0, '#6366f1')
          iconGrad.addColorStop(1, '#8b5cf6')
        } else {
          iconGrad.addColorStop(0, '#10b981')
          iconGrad.addColorStop(1, '#34d399')
        }
        this.drawRoundedRect(ctx, 24, 20, 32, 32, 8, iconGrad)
        // 简笔图形
        ctx.fillStyle = '#ffffff'
        ctx.beginPath()
        ctx.arc(40, 36, 6, 0, Math.PI * 2)
        ctx.fill()

        // 标题文字 (先在 16px 粗体状态下准确测量宽度，严防与右侧阶段标签重叠)
        ctx.fillStyle = '#0f172a'
        const titleFont = 'bold 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif'
        ctx.font = titleFont
        ctx.fillText(title, 68, 42)
        const titleW = ctx.measureText(title).width

        // 周期阶段标签 Tag (紧随标题之后，基于准确的 titleW 计算起点 X)
        let nextX = 68 + titleW + 12
        if (state.cycle) {
          const tagText = state.cycle
          ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          const tagW = ctx.measureText(tagText).width + 16
          const tagX = nextX
          const tagFill = isMajor ? 'rgba(99, 102, 241, 0.08)' : 'rgba(16, 185, 129, 0.08)'
          const tagBorder = isMajor ? '#6366f1' : '#10b981'
          this.drawRoundedRect(ctx, tagX, 26, tagW, 20, 10, tagFill, tagBorder)
          ctx.fillStyle = tagBorder
          ctx.fillText(tagText, tagX + 8, 40)
          nextX = tagX + tagW + 8
        }

        // 截止日期 Tag
        if (state.endDate) {
          const dateText = `截止日期: ${state.endDate}`
          ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          const dateW = ctx.measureText(dateText).width + 16
          this.drawRoundedRect(ctx, nextX, 26, dateW, 20, 10, '#f8fafc', '#cbd5e1')
          ctx.fillStyle = '#64748b'
          ctx.fillText(dateText, nextX + 8, 40)
        }

        // 右上角系统标识
        ctx.fillStyle = '#94a3b8'
        ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        ctx.textAlign = 'right'
        ctx.fillText('三因子宏观经济周期划分的风险预算资产配置模型', width - 24, 40)
        ctx.textAlign = 'left'

        // 顶部分割线
        ctx.strokeStyle = '#f1f5f9'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(24, 62)
        ctx.lineTo(width - 24, 62)
        ctx.stroke()

        // 3. 绘制左侧饼图 (ECharts) - 等比例居中自适应绘制，严防非等比拉伸导致圆形失真变形
        const maxChartW = 390
        const maxChartH = 375
        const imgAspect = img.width / img.height
        let drawW = maxChartW
        let drawH = drawW / imgAspect
        if (drawH > maxChartH) {
          drawH = maxChartH
          drawW = drawH * imgAspect
        }
        const drawX = 20 + (maxChartW - drawW) / 2
        const drawY = 75 + (maxChartH - drawH) / 2
        ctx.drawImage(img, drawX, drawY, drawW, drawH)

        // 4. 绘制右侧对比面板卡片
        const startX = 430
        const cardW = 505
        const cardH = 375
        this.drawRoundedRect(ctx, startX, 75, cardW, cardH, 10, '#f8fafc', '#e2e8f0')

        // 对比面板标题
        ctx.fillStyle = '#0f172a'
        ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        const compTitle = state.endDate 
          ? `当前【${state.cycle || '最新周期'}】风险预算 vs 建议仓位对比（截至 ${state.endDate}）`
          : `当前【${state.cycle || '最新周期'}】风险预算 vs 建议仓位对比`
        ctx.fillText(compTitle, startX + 16, 102)

        // 分割线
        ctx.strokeStyle = '#e2e8f0'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(startX + 16, 114)
        ctx.lineTo(startX + cardW - 16, 114)
        ctx.stroke()

        // 对比表头 - 3列居中对齐
        ctx.fillStyle = '#64748b'
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(isMajor ? '标的资产' : '标的板块', startX + 90, 130)
        ctx.fillText('风险预算', startX + 245, 130)
        ctx.fillText('建议仓位', startX + 410, 130)

        // 对比列表行
        const list = isMajor ? this.majorComparisonList : this.sectorComparisonList
        const totalAreaH = 260
        const stepY = list.length > 0 ? (totalAreaH / list.length) : 48
        const startY = 150 + (totalAreaH - stepY * list.length) / 2

        list.forEach((item, idx) => {
          const curY = startY + idx * stepY
          const color = palette[idx % palette.length]
          const colorLight = paletteLight[idx % paletteLight.length]

          // 1. 标的资产/板块色标与名称（宽幅展示，支持长名称）
          this.drawRoundedRect(ctx, startX + 18, curY + 3, 8, 8, 4, color)
          ctx.fillStyle = '#1e293b'
          ctx.font = 'bold 11px sans-serif'
          ctx.textAlign = 'left'
          let nameText = item.name || ''
          if (nameText.length > 13) nameText = nameText.slice(0, 12) + '...'
          ctx.fillText(nameText, startX + 32, curY + 10)

          // 2. 风险预算数值胶囊 + 独立进度条
          this.drawRoundedRect(ctx, startX + 195, curY - 2, 38, 16, 8, '#ffffff', '#cbd5e1')
          ctx.fillStyle = '#475569'
          ctx.font = 'bold 10px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(item.quotaText, startX + 214, curY + 10)

          const quotaBarX = startX + 242
          const quotaBarMaxW = 60
          this.drawRoundedRect(ctx, quotaBarX, curY + 4, quotaBarMaxW, 5, 2, '#e2e8f0')
          const quotaBarW = Math.max(0, Math.min(quotaBarMaxW, (item.quotaPct / 100) * quotaBarMaxW))
          if (quotaBarW > 0) {
            this.drawRoundedRect(ctx, quotaBarX, curY + 4, quotaBarW, 5, 2, '#94a3b8')
          }

          // 3. 实际建议仓位数值 + 独立渐变进度条
          ctx.fillStyle = color
          ctx.font = 'bold 12px sans-serif'
          ctx.textAlign = 'right'
          ctx.fillText(item.weightText, startX + 395, curY + 10)

          const weightBarX = startX + 405
          const weightBarMaxW = 60
          this.drawRoundedRect(ctx, weightBarX, curY + 4, weightBarMaxW, 5, 2, '#e2e8f0')
          const weightBarW = Math.max(0, Math.min(weightBarMaxW, (item.weightPct / 100) * weightBarMaxW))
          if (weightBarW > 0) {
            const barGrad = ctx.createLinearGradient(weightBarX, curY + 4, weightBarX + weightBarW, curY + 4)
            barGrad.addColorStop(0, color)
            barGrad.addColorStop(1, colorLight)
            this.drawRoundedRect(ctx, weightBarX, curY + 4, weightBarW, 5, 2, barGrad)
          }
        })

        // 5. 导出并触发浏览器下载
        const fullDataUrl = canvas.toDataURL('image/png')
        const downloadLink = document.createElement('a')
        downloadLink.download = `${title}_${state.cycle || ''}_风险预算与建议仓位对比.png`
        downloadLink.href = fullDataUrl
        document.body.appendChild(downloadLink)
        downloadLink.click()
        document.body.removeChild(downloadLink)
        this.$message.success(`已成功导出包含【${title}】的完整对比图表图片`)
      }
      img.src = chartImgUri
    },

    /**
     * 发送全局事件，同步当前配置至回测系统并触发运行
     */
    syncAndRunBacktest(type, options = {}) {
      const state = type === 'major' ? this.major : this.sector
      if (!state.isValid) {
        this.$message.warning('请先配平宏观周期配额至 100% 后再执行回测')
        return
      }
      this.$bus.$emit('sync-backtest', {
        type: type,
        asset_pool: JSON.parse(JSON.stringify(state.assetPool)),
        cycle_rb_rules: JSON.parse(JSON.stringify(state.cycleRbRules))
      })
      this.$message.success('已保存配置，并同步计算仓位建议与策略回测')
      
      if (options.scroll) {
        const container = document.querySelector('.risk-budget-backtest-container')
        if (container) {
          container.scrollIntoView({ behavior: 'smooth', block: 'start' })
        } else {
          window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
          })
        }
      }
    }
  }
}
</script>

<style scoped>
.dynamic-risk-budget-container {
  width: 100%;
}

.budget-col {
  min-height: 400px;
}

.risk-budget-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.3s ease;
  min-height: 400px;
  height: auto;
  box-sizing: border-box;
}
.risk-budget-card:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}
.major-icon {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}
.sector-icon {
  background: linear-gradient(135deg, #10b981, #34d399);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  font-weight: 700;
  font-size: 15px;
  color: #1e293b;
  letter-spacing: 0.5px;
}

.tags-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cycle-tag {
  border-radius: 20px;
  font-size: 11px;
  padding: 0 8px;
  height: 20px;
  line-height: 18px;
  border-color: #6366f1;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}
.sector-cycle-tag {
  border-color: #10b981;
  color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.date-tag {
  border-radius: 20px;
  font-size: 11px;
  padding: 0 8px;
  height: 20px;
  line-height: 18px;
  background: #f8fafc;
  color: #64748b;
  border-color: #cbd5e1;
}
.date-tag i {
  margin-right: 2px;
}

.table-tag {
  border-radius: 4px;
  font-size: 10px;
  padding: 0 5px;
  height: 18px;
  line-height: 16px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.header-export-btn {
  font-size: 12px;
  color: #6366f1;
  padding: 0 4px;
}
.header-export-btn:hover {
  color: #4f46e5;
}
.sector-export-btn {
  color: #10b981;
}
.sector-export-btn:hover {
  color: #059669;
}

.badge-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #ef4444;
  border-radius: 50%;
  margin-left: 2px;
  vertical-align: top;
}

.content-wrapper {
  min-height: 320px;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 280px;
  color: #94a3b8;
}
.error-container i {
  font-size: 48px;
  margin-bottom: 12px;
  color: #cbd5e1;
}
.error-container p {
  margin-bottom: 16px;
  font-size: 13px;
}

/* 图表与对比展示面板样式 - 饼图左移，右侧对比展示 */
.dual-dashboard {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
}

.chart-area {
  flex: 0 0 235px;
  height: 270px;
  position: relative;
  min-width: 220px;
  max-width: 250px;
}

.echarts-chart {
  width: 100%;
  height: 100%;
}

/* 风险预算设定 vs 实际建议仓位 鲜明对比展示面板 */
.comparison-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 380px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 14px 12px;
  box-sizing: border-box;
}

.comp-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 6px;
}

.comp-panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #334155;
}

.comp-icon {
  font-size: 15px;
  color: #6366f1;
}
.sector-comp-icon {
  color: #10b981;
}

.comp-title-text strong {
  color: #0f172a;
  font-weight: 700;
}

.comp-date-tip {
  font-size: 11px;
  font-weight: normal;
  color: #64748b;
  margin-left: 2px;
}

.comp-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comp-download-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  color: #6366f1;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}
.comp-download-icon:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #4338ca;
  transform: scale(1.1);
}
.sector-comp-download-icon {
  color: #10b981;
}
.sector-comp-download-icon:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
}

.comp-edit-btn {
  font-size: 11px;
  color: #6366f1;
  padding: 0 4px;
}
.comp-edit-btn:hover {
  color: #4338ca;
}
.sector-comp-edit-btn {
  color: #10b981;
}
.sector-comp-edit-btn:hover {
  color: #047857;
}

.comp-table-container {
  width: 100%;
  max-height: 230px;
  overflow-y: auto;
}
.comp-table-container::-webkit-scrollbar {
  width: 4px;
}
.comp-table-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.comp-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 11px;
}

.comp-table th {
  padding: 5px 4px 7px;
  color: #64748b;
  font-weight: 600;
  font-size: 11px;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.comp-tip-icon {
  font-size: 11px;
  color: #94a3b8;
  margin-left: 2px;
  cursor: pointer;
}

.comp-table td {
  padding: 7px 4px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
  text-align: center;
}

.comp-row {
  animation: fadeInUp 0.3s ease both;
  transition: background 0.15s ease;
}
.comp-row:hover {
  background: #f1f5f9;
}

/* 标的资产/板块列：宽度调至 38%，文字完整展示，居中对齐 */
.th-asset, .td-asset {
  width: 38%;
  text-align: center;
}

.comp-asset-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  max-width: 100%;
  vertical-align: middle;
}

.comp-color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.comp-asset-name {
  color: #1e293b;
  font-weight: 600;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 155px;
}

/* 风险预算与建议仓位列：各占 31%，数值与独立自适应进度条并列展示 */
.th-quota, .td-quota,
.th-weight, .td-weight {
  width: 31%;
  text-align: center;
  white-space: nowrap;
}

.comp-metric-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
}

.quota-pill {
  display: inline-block;
  padding: 1px 6px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  color: #475569;
  font-weight: 600;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  min-width: 34px;
  text-align: center;
  flex-shrink: 0;
}

.weight-bold {
  font-weight: 700;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  min-width: 44px;
  text-align: right;
  flex-shrink: 0;
}

.metric-bar-track {
  flex: 1;
  max-width: 62px;
  min-width: 32px;
  height: 5px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.metric-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.bar-quota {
  background: #94a3b8;
}

/* 参数与配额配置面板样式：设置最大高度与柔和滚动条，保障内网环境所有阶段行及操作按钮全部可见 */
.config-panel {
  padding: 4px 0;
  animation: fadeIn 0.3s ease;
  max-height: 580px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
}
.config-panel::-webkit-scrollbar {
  width: 6px;
}
.config-panel::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.config-panel::-webkit-scrollbar-track {
  background: #f8fafc;
}

.config-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.quota-tip {
  font-size: 11px;
  color: #94a3b8;
}

.warning-icon {
  color: #f59e0b;
  margin-left: 4px;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  -webkit-overflow-scrolling: touch;
}
.table-responsive::-webkit-scrollbar {
  height: 6px;
}
.table-responsive::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  text-align: left;
}

.custom-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  padding: 6px 6px;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.custom-table td {
  padding: 5px 6px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}

.param-tag {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  white-space: nowrap;
}
.sector-param-tag {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.delete-btn {
  color: #ef4444;
}
.delete-btn:hover {
  color: #dc2626;
}

.stage-col {
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  font-size: 11px;
}

.text-center {
  text-align: center !important;
}

.number-cell {
  padding: 3px 4px;
  text-align: center;
}

.compact-input-number {
  width: 62px !important;
  display: inline-block;
  vertical-align: middle;
}

.compact-input-number >>> .el-input__inner {
  text-align: center;
  padding: 0 2px;
  height: 24px;
  line-height: 24px;
  font-size: 11px;
}

.sum-tag {
  font-weight: 700;
  border-radius: 12px;
  padding: 0 4px;
  font-size: 10px;
}

.config-footer {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.validation-msg {
  font-size: 12px;
}

.valid-alert {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  padding: 8px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.invalid-alert {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  padding: 8px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.help-icon {
  margin-left: 6px;
  color: #94a3b8;
  cursor: pointer;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 穿透覆盖 el-card 及 el-card__body，彻底防止内网版本截断内容与配额表格 */
.risk-budget-card,
.risk-budget-card /deep/ .el-card__body,
.risk-budget-card >>> .el-card__body {
  overflow: visible !important;
  height: auto !important;
}
</style>
