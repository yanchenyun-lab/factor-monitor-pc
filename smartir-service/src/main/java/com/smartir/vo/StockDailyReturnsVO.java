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
 * 按交易日聚合的收益率时序对象
 * 既包含基础时序属性 (tradeDate, stage)，也通过 JsonAnyGetter 将各资产收益率展开为顶级字段
 */
@Data
@ApiModel(value = "StockDailyReturnsVO", description = "日频资产收益率聚合对象")
public class StockDailyReturnsVO {

    @ApiModelProperty("交易日期")
    private String tradeDate;

    @ApiModelProperty("宏观经济周期阶段(1-6)")
    private Integer stage;

    @ApiModelProperty("资产收益率映射表 (以 assetCode 为 key)")
    private Map<String, BigDecimal> returns = new HashMap<>();

    @ApiModelProperty("兼容与动态扩展字段")
    private Map<String, Object> extraFields = new HashMap<>();

    public void addReturn(String assetCode, BigDecimal rate) {
        if (assetCode != null) {
            returns.put(assetCode, rate);
            extraFields.put(assetCode, rate);
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
