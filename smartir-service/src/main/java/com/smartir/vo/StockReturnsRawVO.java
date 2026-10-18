package com.smartir.vo;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 纵表原始查询行 (含宏观周期)
 */
@Data
public class StockReturnsRawVO {
    private String tradeDate;
    private String assetCode;
    private BigDecimal returnRate;
    private Integer stage;
}
