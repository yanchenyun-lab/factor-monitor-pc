package com.smartir.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.smartir.entity.StockRiskBudgetMoneyFactorsDO;
import com.smartir.mapper.MoneyFactorMapper;
import com.smartir.service.MoneyFactorService;
import org.springframework.stereotype.Service;

@Service
public class MoneyFactorServiceImpl extends ServiceImpl<MoneyFactorMapper, StockRiskBudgetMoneyFactorsDO> implements MoneyFactorService {
}
