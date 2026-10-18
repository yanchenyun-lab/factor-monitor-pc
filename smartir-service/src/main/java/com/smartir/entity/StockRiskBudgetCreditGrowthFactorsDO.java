package com.smartir.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

/**
 * <p>
 * 风险预算信用增长因子
 * </p>
 *
 * @author xuyunfei
 * @since 2026-09-02 09:47:39
 */
@Data
@TableName("stock_risk_budget_credit_growth_factors")
@ApiModel(value = "StockRiskBudgetCreditGrowthFactorsDO对象", description = "风险预算信用增长因子")
public class StockRiskBudgetCreditGrowthFactorsDO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty("唯一标识")
    @TableId("id")
    private String id;

    @ApiModelProperty("数据月份 (格式：YYYY-MM)")
    @TableField("data_month")
    private String dataMonth;

    @ApiModelProperty("交易日期")
    @TableField("trade_date")
    private String tradeDate;

    @ApiModelProperty("金融机构新增中长期贷款当月值")
    @TableField("fin_loan_mid_long")
    private BigDecimal finLoanMidLong;

    @ApiModelProperty("中长期贷款脉冲")
    @TableField("fin_loan_mid_long_pulse")
    private BigDecimal finLoanMidLongPulse;

    @ApiModelProperty("信用方向因子")
    @TableField("credit_direction_factor")
    private Integer creditDirectionFactor;

    @ApiModelProperty("制造业PMI当月值")
    @TableField("manufacture_pmi")
    private BigDecimal manufacturePmi;

    @ApiModelProperty("制造业PMI脉冲")
    @TableField("manufacture_pmi_pulse")
    private BigDecimal manufacturePmiPulse;

    @ApiModelProperty("制造业PMI差分")
    @TableField("manufacture_pmi_diff")
    private Integer manufacturePmiDiff;

    @ApiModelProperty("非制造业PMI当月值")
    @TableField("non_manufacture_pmi")
    private BigDecimal nonManufacturePmi;

    @ApiModelProperty("非制造业PMI脉冲")
    @TableField("non_manufacture_pmi_pulse")
    private BigDecimal nonManufacturePmiPulse;

    @ApiModelProperty("非制造业PMI差分")
    @TableField("non_manufacture_pmi_diff")
    private Integer nonManufacturePmiDiff;

    @ApiModelProperty("非官方PMI当月值")
    @TableField("pmi_unofficial")
    private BigDecimal pmiUnofficial;

    @ApiModelProperty("非官方PMI脉冲")
    @TableField("pmi_unofficial_pulse")
    private BigDecimal pmiUnofficialPulse;

    @ApiModelProperty("非官方PMI差分")
    @TableField("pmi_unofficial_diff")
    private Integer pmiUnofficialDiff;

    @ApiModelProperty("增长方向因子")
    @TableField("growth_direction_factor")
    private Integer growthDirectionFactor;

    @ApiModelProperty("创建时间")
    @TableField("create_time")
    private Date createTime;

    @ApiModelProperty("更新时间")
    @TableField("update_time")
    private Date updateTime;
}
