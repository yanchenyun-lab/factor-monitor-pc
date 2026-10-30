package com.smartir.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.smartir.common.JsonResult;
import com.smartir.entity.StockRiskBudgetCreditGrowthFactorsDO;
import com.smartir.service.CreditGrowthFactorService;
import com.smartir.dto.ReturnStatsQueryDTO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/factors/credit-growth")
public class CreditGrowthFactorController {

    @Autowired
    private CreditGrowthFactorService creditGrowthFactorService;

    @PostMapping("/list")
    public JsonResult<List<StockRiskBudgetCreditGrowthFactorsDO>> getList(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        String startDate = queryDTO != null ? queryDTO.getStartDate() : null;
        String endDate = queryDTO != null ? queryDTO.getEndDate() : null;
        QueryWrapper<StockRiskBudgetCreditGrowthFactorsDO> wrapper = new QueryWrapper<>();
        if (startDate != null && !startDate.isEmpty()) {
            wrapper.ge("trade_date", startDate);
        }
        if (endDate != null && !endDate.isEmpty()) {
            wrapper.le("trade_date", endDate);
        }
        wrapper.orderByDesc("trade_date");
        return JsonResult.success(creditGrowthFactorService.list(wrapper));
    }
}