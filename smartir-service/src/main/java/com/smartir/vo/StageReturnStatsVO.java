package com.smartir.vo;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

/**
 * 宏观阶段年化收益率统计对象
 */
@Data
@ApiModel(value = "StageReturnStatsVO", description = "宏观阶段资产年化收益统计")
public class StageReturnStatsVO {

    @ApiModelProperty("经济周期阶段(1-6)")
    private Integer stage;

    @ApiModelProperty("各资产年化收益率映射表")
    private Map<String, BigDecimal> returns = new HashMap<>();

    @ApiModelProperty("兼容与动态扩展字段")
    private Map<String, Object> extraFields = new HashMap<>();

    public void addStat(String assetCode, BigDecimal annualReturn) {
        if (assetCode != null) {
            returns.put(assetCode, annualReturn);
            extraFields.put(assetCode, annualReturn);
        }
    }

    public void addExtra(String key, Object value) {
        extraFields.put(key, value);
    }

    @JsonAnyGetter
    public Map<String, Object> getExtraFields() {
        return extraFields;
    }

    @JsonAnySetter
    public void setExtraField(String key, Object value) {
        extraFields.put(key, value);
    }
}
