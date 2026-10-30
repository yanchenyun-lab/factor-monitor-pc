package com.smartir.feign;

import com.smartir.common.JsonResult;
import com.smartir.dto.QuantBacktestRequest;
import com.smartir.dto.QuantRiskBudgetRequest;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.Map;

/**
 * smartir-quant 量化微服务 Feign 客户端
 * 基于 Nacos 服务注册与发现中心，服务名默认为 "smartir-quant"
 * 亦可通过配置项 quant.service.url 指定固定直连地址进行离线/单机调试
 */
@FeignClient(name = "${quant.service.name:smartir-quant}", url = "${quant.service.url:}")
public interface QuantFeignClient {

    /**
     * 求解指定交易日的宏观经济周期与最优资产配置建议仓位
     *
     * @param req 包含资产池、宏观周期规则、截止日期以及注入的 risk_data
     * @return 统一响应实体（包含 current_cycle, positions, calc_date）
     */
    @PostMapping("/dynamic-risk-budget")
    JsonResult<Map<String, Object>> dynamicRiskBudget(@RequestBody QuantRiskBudgetRequest req);

    /**
     * 执行历史时序全景回测，输出逐日净值、权重时序、宏观阶段色块以及量化绩效看板指标
     *
     * @param req 包含资产池、宏观周期规则、起止日期以及注入的 risk_data
     * @return 统一响应实体（包含 metrics_summary, raw_metrics, nav_series, allocation_series, annual_table 等）
     */
    @PostMapping("/dynamic-risk-budget/backtest")
    JsonResult<Map<String, Object>> dynamicRiskBudgetBacktest(@RequestBody QuantBacktestRequest req);
}

