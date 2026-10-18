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
 * 风险预算货币因子
 * </p>
 *
 * @author xuyunfei
 * @since 2026-09-02 09:47:47
 */
@Data
@TableName("stock_risk_budget_money_factors")
@ApiModel(value = "StockRiskBudgetMoneyFactorsDO对象", description = "风险预算货币因子")
public class StockRiskBudgetMoneyFactorsDO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty("唯一标识")
    @TableId("id")
    private String id;

    @ApiModelProperty("交易日期")
    @TableField("trade_date")
    private String tradeDate;

    @ApiModelProperty("历史最近:中国:贷款市场报价利率(LPR):1年")
    @TableField("latest_lpr_1y")
    private BigDecimal latestLpr1y;

    @ApiModelProperty("历史最近:中国:贷款市场报价利率(LPR):5年")
    @TableField("latest_lpr_5y")
    private BigDecimal latestLpr5y;

    @ApiModelProperty("历史最近:中国工商银行:定期存款利率:1年(整存整取)")
    @TableField("latest_icbc_time_deposit_1y")
    private BigDecimal latestIcbcTimeDeposit1y;

    @ApiModelProperty("历史最近:中国工商银行:定期存款利率:5年(整存整取)")
    @TableField("latest_icbc_time_deposit_5y")
    private BigDecimal latestIcbcTimeDeposit5y;

    @ApiModelProperty("历史最近:中国:常备借贷便利(SLF)利率:7天")
    @TableField("latest_slf_rate_7d")
    private BigDecimal latestSlfRate7d;

    @ApiModelProperty("历史最近:中国:中期借贷便利(MLF):利率:1年")
    @TableField("latest_mlf_rate_1y")
    private BigDecimal latestMlfRate1y;

    @ApiModelProperty("历史最近:逆回购利率:7天")
    @TableField("latest_reverse_repo_rate_7d")
    private BigDecimal latestReverseRepoRate7d;

    @ApiModelProperty("历史最近:逆回购利率:14天")
    @TableField("latest_reverse_repo_rate_14d")
    private BigDecimal latestReverseRepoRate14d;

    @ApiModelProperty("历史最近:中国:人民银行对金融机构存款利率:法定准备金")
    @TableField("latest_fin_inst_deposit_rate_stat_res")
    private BigDecimal latestFinInstDepositRateStatRes;

    @ApiModelProperty("历史最近:中国:人民银行对金融机构存款利率:超额准备金")
    @TableField("latest_fin_inst_deposit_rate_exc_res")
    private BigDecimal latestFinInstDepositRateExcRes;

    @ApiModelProperty("历史最近:中国:人民币存款准备金率:大型存款类金融机构(变动公告日期)")
    @TableField("latest_reserve_ratio_large_fin_inst")
    private BigDecimal latestReserveRatioLargeFinInst;

    @ApiModelProperty("历史最近:中国:人民币存款准备金率:中小型存款类金融机构(变动公告日期)")
    @TableField("latest_reserve_ratio_sml_fin_inst")
    private BigDecimal latestReserveRatioSmlFinInst;

    @ApiModelProperty("历史最近:存款类金融机构质押式回购利率:7天")
    @TableField("latest_dep_inst_pledge_repo_rate_7d")
    private BigDecimal latestDepInstPledgeRepoRate7d;

    @ApiModelProperty("DR007:120日移动平均:指数加权")
    @TableField("dr007_120d_ewma")
    private BigDecimal dr007120dEwma;

    @ApiModelProperty("符号函数:LPR")
    @TableField("sign_lpr")
    private Integer signLpr;

    @ApiModelProperty("符号函数:存款")
    @TableField("sign_deposit")
    private Integer signDeposit;

    @ApiModelProperty("符号函数:SLF")
    @TableField("sign_slf")
    private Integer signSlf;

    @ApiModelProperty("符号函数:MLF")
    @TableField("sign_mlf")
    private Integer signMlf;

    @ApiModelProperty("符号函数:逆回购")
    @TableField("sign_reverse_repo")
    private Integer signReverseRepo;

    @ApiModelProperty("符号函数:准备金率")
    @TableField("sign_reserve_rate")
    private Integer signReserveRate;

    @ApiModelProperty("符号函数:准备金")
    @TableField("sign_reserve_ratio")
    private Integer signReserveRatio;

    @ApiModelProperty("符号函数:DR007")
    @TableField("sign_dr007")
    private Integer signDr007;

    @ApiModelProperty("货币方向因子")
    @TableField("money_direction_factor")
    private BigDecimal moneyDirectionFactor;

    @ApiModelProperty("创建时间")
    @TableField("create_time")
    private Date createTime;

    @ApiModelProperty("更新时间")
    @TableField("update_time")
    private Date updateTime;
}
