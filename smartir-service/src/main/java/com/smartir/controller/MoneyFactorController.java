package com.smartir.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.smartir.entity.StockRiskBudgetMoneyFactorsDO;
import com.smartir.service.MoneyFactorService;
import com.smartir.dto.ReturnStatsQueryDTO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/factors/money")
public class MoneyFactorController {

    @Autowired
    private MoneyFactorService moneyFactorService;

    @PostMapping("/list")
    public List<StockRiskBudgetMoneyFactorsDO> getList(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        String startDate = queryDTO != null ? queryDTO.getStartDate() : null;
        String endDate = queryDTO != null ? queryDTO.getEndDate() : null;
        QueryWrapper<StockRiskBudgetMoneyFactorsDO> wrapper = new QueryWrapper<>();
        if (startDate != null && !startDate.isEmpty()) {
            wrapper.ge("trade_date", startDate);
        }
        if (endDate != null && !endDate.isEmpty()) {
            wrapper.le("trade_date", endDate);
        }
        wrapper.orderByDesc("trade_date");
        return moneyFactorService.list(wrapper);
    }
}
