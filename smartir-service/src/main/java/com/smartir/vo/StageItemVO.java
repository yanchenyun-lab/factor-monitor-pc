package com.smartir.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@ApiModel(value = "StageItemVO", description = "历史宏观周期阶段明细")
public class StageItemVO {

    @ApiModelProperty("交易日期 (YYYY-MM-DD)")
    private String tradeDate;

    @ApiModelProperty("宏观周期阶段代码 (1-6)")
    private Integer stage;

    @ApiModelProperty("宏观周期阶段中文名称")
    private String cycleName;
}
