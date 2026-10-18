package com.smartir.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.smartir.entity.StockRiskBudgetCreditGrowthFactorsDO;
import com.smartir.mapper.CreditGrowthFactorMapper;
import com.smartir.service.CreditGrowthFactorService;
import org.springframework.stereotype.Service;

@Service
public class CreditGrowthFactorServiceImpl extends ServiceImpl<CreditGrowthFactorMapper, StockRiskBudgetCreditGrowthFactorsDO> implements CreditGrowthFactorService {
}
