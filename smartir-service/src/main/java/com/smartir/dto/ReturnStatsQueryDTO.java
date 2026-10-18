package com.smartir.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel(value = "ReturnStatsQueryDTO", description = "收益率统计查询条件")
public class ReturnStatsQueryDTO {
    
    @ApiModelProperty("开始日期 (YYYY-MM-DD)")
    private String startDate;

    @ApiModelProperty("结束日期 (YYYY-MM-DD)")
    private String endDate;
}
