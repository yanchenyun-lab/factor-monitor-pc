package com.smartir.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
@ApiModel(value = "RiskDataBundleVO", description = "动态风险预算与回测专属量化数据包")
public class RiskDataBundleVO {

    @ApiModelProperty("针对截止日识别的最新宏观周期代码 (1-6)")
    private Integer latestStage;

    @ApiModelProperty("针对截止日识别的最新宏观周期中文名 (如 阶段1-信用扩张)")
    private String latestCycleName;

    @ApiModelProperty("有效收益率数据的最早交易日期")
    private String minDate;

    @ApiModelProperty("有效收益率数据的最晚交易日期")
    private String maxDate;

    @ApiModelProperty("有效交易日总天数")
    private Integer totalDays;

    @ApiModelProperty("宏观周期阶段时序列表")
    private List<StageItemVO> stages = new ArrayList<>();

    @ApiModelProperty("资产收益率明细时序列表")
    private List<ReturnItemVO> returns = new ArrayList<>();
}
