package com.smartir.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.Date;

/**
 * <p>
 * 历史经济周期表
 * </p>
 *
 * @author xuyunfei
 * @since 2026-09-02 09:33:52
 */
@Data
@TableName("stock_historical_stage")
@ApiModel(value = "HistoricalStageDO", description = "历史经济周期表")
public class HistoricalStageDO {

    @TableId("id")
    @ApiModelProperty("唯一标识")
    private String id;

    @TableField("trade_date")
    @ApiModelProperty("交易日期")
    private String tradeDate;

    @TableField("stage")
    @ApiModelProperty("经济周期阶段")
    private Integer stage;

    @TableField("create_time")
    @ApiModelProperty("创建时间")
    private Date createTime;

    @TableField("update_time")
    @ApiModelProperty("更新时间")
    private Date updateTime;
}
