package com.smartir.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

/**
 * <p>
 * 资产及行业收益率纵表
 * </p>
 */
@Data
@TableName("stock_returns")
@ApiModel(value = "StockReturnsDO", description = "资产及行业收益率纵表")
public class StockReturnsDO {

    @TableId("id")
    @ApiModelProperty("唯一标识")
    private String id;

    @TableField("trade_date")
    @ApiModelProperty("交易日期")
    private String tradeDate;

    @TableField("asset_code")
    @ApiModelProperty("资产/板块代码")
    private String assetCode;

    @TableField("return_rate")
    @ApiModelProperty("收益率/倍数因子(1+r)")
    private BigDecimal returnRate;

    @TableField("create_time")
    @ApiModelProperty("创建时间")
    private Date createTime;

    @TableField("update_time")
    @ApiModelProperty("更新时间")
    private Date updateTime;
}
