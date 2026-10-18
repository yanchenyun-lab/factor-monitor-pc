package com.smartir.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

@Data
@ApiModel(value = "RiskDataQueryDTO", description = "动态风险预算与回测数据查询入参")
public class RiskDataQueryDTO {

    @ApiModelProperty("需要查询的资产代码列表，如 [H00852.SH, CBA00651.CS]")
    private List<String> assetCodes;

    @ApiModelProperty("起始日期 (YYYY-MM-DD)，可选")
    private String startDate;

    @ApiModelProperty("截止日期 (YYYY-MM-DD)，可选")
    private String endDate;

    @ApiModelProperty("滚动回溯交易日天数窗口 (如 720)，若未传 startDate 则取最近 N 个交易日")
    private Integer historyWindow;
}
