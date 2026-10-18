package com.smartir.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;

@Data
@ApiModel(value = "StageResultVO", description = "周期阶段结果")
public class StageResultVO {

    @ApiModelProperty("交易日期")
    private String tradeDate;

    @ApiModelProperty("货币方向因子")
    private BigDecimal money;

    @ApiModelProperty("信用方向因子")
    private Integer credit;

    @ApiModelProperty("增长方向因子")
    private Integer growth;

    @ApiModelProperty("所处周期阶段")
    private Integer stage;
}
