package com.smartir.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.smartir.vo.RiskDataBundleVO;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import java.util.Map;

/**
 * 动态风险预算全景回测请求实体
 */
@Data
@ApiModel(description = "动态风险预算全景回测请求实体")
public class QuantBacktestRequest {

    @JsonProperty("asset_pool")
    @ApiModelProperty("通用资产定义字典")
    private Map<String, Object> assetPool;

    @JsonProperty("asset_pool_major")
    @ApiModelProperty("大类资产池定义")
    private Map<String, Object> assetPoolMajor;

    @JsonProperty("asset_pool_sector")
    @ApiModelProperty("行业板块资产池定义")
    private Map<String, Object> assetPoolSector;

    @JsonProperty("cycle_rb_rules")
    @ApiModelProperty("通用宏观6周期目标风险预算配额")
    private Map<String, Object> cycleRbRules;

    @JsonProperty("cycle_rb_rules_major")
    @ApiModelProperty("大类资产宏观周期规则")
    private Map<String, Object> cycleRbRulesMajor;

    @JsonProperty("cycle_rb_rules_sector")
    @ApiModelProperty("行业板块宏观周期规则")
    private Map<String, Object> cycleRbRulesSector;

    @JsonProperty("data_table")
    @ApiModelProperty("行情收益率数据源表名")
    private String dataTable = "stock_returns";

    @JsonProperty("start_date")
    @ApiModelProperty("回测起始日期 (YYYY-MM-DD)")
    private String startDate;

    @JsonProperty("end_date")
    @ApiModelProperty("回测截止日期 (YYYY-MM-DD)")
    private String endDate;

    @JsonProperty("rebalance_freq")
    @ApiModelProperty("调仓频率 (M, stage_change, M_or_stage_change)")
    private String rebalanceFreq = "M_or_stage_change";

    @JsonProperty("custom_bounds")
    @ApiModelProperty("权重硬边界约束")
    private Map<String, Object> customBounds;

    @JsonProperty("history_window")
    @ApiModelProperty("滚动协方差估计窗口天数")
    private Integer historyWindow = 720;

    @JsonProperty("transaction_cost")
    @ApiModelProperty("单边调仓摩擦损耗率")
    private Double transactionCost = 0.0003;

    @JsonProperty("rf")
    @ApiModelProperty("无风险年化利率")
    private Double rf = 0.02;

    @JsonProperty("risk_data")
    @ApiModelProperty("注入的预拉取风险基础数据包")
    private RiskDataBundleVO riskData;
}
