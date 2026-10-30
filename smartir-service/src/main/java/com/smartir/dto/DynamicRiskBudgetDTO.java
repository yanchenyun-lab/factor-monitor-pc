package com.smartir.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import java.util.Map;

/**
 * 动态风险预算测算请求 DTO (Controller 层使用)
 */
@Data
@ApiModel(description = "动态风险预算测算请求 DTO")
public class DynamicRiskBudgetDTO {

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

    @JsonProperty("end_date")
    @ApiModelProperty("测算截止日期 (YYYY-MM-DD)")
    private String endDate;

    @JsonProperty("history_window")
    @ApiModelProperty("滚动协方差估计窗口天数")
    private Integer historyWindow = 720;

    @JsonProperty("custom_bounds")
    @ApiModelProperty("资产持仓权重硬约束边界")
    private Map<String, Object> customBounds;
}
