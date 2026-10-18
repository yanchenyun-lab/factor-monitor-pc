package com.smartir.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@NoArgsConstructor
@AllArgsConstructor
@ApiModel(value = "ReturnItemVO", description = "资产日频收益率明细")
public class ReturnItemVO {

    @ApiModelProperty("交易日期 (YYYY-MM-DD)")
    private String tradeDate;

    @ApiModelProperty("资产/板块代码")
    private String assetCode;

    @ApiModelProperty("收益率/倍数因子(1+r)")
    private BigDecimal returnRate;
}
