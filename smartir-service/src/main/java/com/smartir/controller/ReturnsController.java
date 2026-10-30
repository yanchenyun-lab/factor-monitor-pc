package com.smartir.controller;

import com.smartir.common.JsonResult;
import com.smartir.dto.*;
import com.smartir.feign.QuantFeignClient;
import com.smartir.service.StockReturnsService;
import com.smartir.util.AssetCodeHelper;
import com.smartir.vo.RiskDataBundleVO;
import com.smartir.vo.StockDailyReturnsVO;
import com.smartir.vo.StageReturnStatsVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@CrossOrigin
@RestController
@RequestMapping("/api/returns")
@Api(tags = "资产及行业收益率数据接口")
public class ReturnsController {

    @Autowired
    private StockReturnsService stockReturnsService;

    @Autowired
    private QuantFeignClient quantFeignClient;

    @PostMapping("/list")
    @ApiOperation("获取所有资产及板块的历史日频收益率序列")
    public JsonResult<List<StockDailyReturnsVO>> getAllReturnsList(@RequestBody(required = false) List<String> assetCodes) {
        return JsonResult.success(stockReturnsService.getDailyReturns(assetCodes));
    }

    @PostMapping("/stats")
    @ApiOperation("按经济周期分组统计所有资产及板块的年化收益率")
    public JsonResult<List<StageReturnStatsVO>> getAllStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return JsonResult.success(stockReturnsService.getStageStats(null, queryDTO));
    }

    @PostMapping("/asset/list")
    @ApiOperation("获取大类资产的历史收益率序列")
    public JsonResult<List<StockDailyReturnsVO>> getAssetReturnsList() {
        return JsonResult.success(stockReturnsService.getDailyReturns(AssetCodeHelper.MAJOR_ASSET_CODES));
    }

    @PostMapping("/sector-excess/list")
    @ApiOperation("获取行业板块的历史超额收益率序列")
    public JsonResult<List<StockDailyReturnsVO>> getSectorExcessReturnsList() {
        return JsonResult.success(stockReturnsService.getDailyReturns(AssetCodeHelper.SECTOR_ASSET_CODES));
    }

    @PostMapping("/asset/stats")
    @ApiOperation("按经济周期分组统计大类资产的年化收益率")
    public JsonResult<List<StageReturnStatsVO>> getAssetStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return JsonResult.success(stockReturnsService.getStageStats(AssetCodeHelper.MAJOR_ASSET_CODES, queryDTO));
    }

    @PostMapping("/sector-excess/stats")
    @ApiOperation("按经济周期分组统计行业板块的超额收益率")
    public JsonResult<List<StageReturnStatsVO>> getSectorStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return JsonResult.success(stockReturnsService.getStageStats(AssetCodeHelper.SECTOR_ASSET_CODES, queryDTO));
    }

    @PostMapping("/candidates")
    @ApiOperation("获取候选大类资产与候选行业板块清单")
    public JsonResult<Map<String, Object>> getCandidates() {
        Map<String, Object> response = new HashMap<>();

        // 候选大类资产清单
        List<Map<String, String>> candidateMajorAssets = new ArrayList<>();
        candidateMajorAssets.add(createCandidate("H00852.SH", "中证1000全收益"));
        candidateMajorAssets.add(createCandidate("H00300.CSI", "300收益"));
        candidateMajorAssets.add(createCandidate("CBA00651.CS", "中债-国债总财富(7-10年)指数"));
        candidateMajorAssets.add(createCandidate("CBA00621.CS", "中债-国债总财富(1-3年)指数"));
        candidateMajorAssets.add(createCandidate("AU9999.SGE", "SGE黄金9999"));
        candidateMajorAssets.add(createCandidate("000832.CSI", "中证转债"));
        response.put("candidateMajorAssets", candidateMajorAssets);

        // 候选行业板块清单
        List<Map<String, String>> candidateSectorAssets = new ArrayList<>();
        candidateSectorAssets.add(createCandidate("CI005919.WI", "消费(风格.中信)"));
        candidateSectorAssets.add(createCandidate("CI005929.WI", "科技产业(中信)"));
        candidateSectorAssets.add(createCandidate("CI005925.WI", "周期产业(中信)"));
        candidateSectorAssets.add(createCandidate("CI005931.WI", "金融产业(中信)"));
        candidateSectorAssets.add(createCandidate("CI005921.WI", "稳定(风格.中信)"));
        candidateSectorAssets.add(createCandidate("881001.WI", "万得全A"));
        response.put("candidateSectorAssets", candidateSectorAssets);

        return JsonResult.success(response);
    }

    private Map<String, String> createCandidate(String code, String name) {
        Map<String, String> map = new HashMap<>();
        map.put("code", code);
        map.put("name", name);
        return map;
    }

    @PostMapping("/risk-data")
    @ApiOperation("供量化风险预算与回测模型获取宏观阶段与资产收益率时序包")
    public JsonResult<RiskDataBundleVO> getRiskDataBundle(@RequestBody(required = false) RiskDataQueryDTO queryDTO) {
        return JsonResult.success(stockReturnsService.getRiskDataBundle(queryDTO));
    }

    @PostMapping({"/dynamic-risk-budget", "/dynamic-budget"})
    @ApiOperation("求解动态风险预算最优建议仓位（结合本地风险数据并调度量化服务计算）")
    public JsonResult<Map<String, Object>> dynamicRiskBudget(@RequestBody DynamicRiskBudgetDTO req) {
        try {
            // 1. 提取资产池定义并获取需要查询的资产代码列表
            Object assetPoolObj = req.getAssetPool() != null ? req.getAssetPool() : req.getAssetPoolMajor();
            if (assetPoolObj == null) {
                assetPoolObj = req.getAssetPoolSector();
            }
            List<String> assetCodes = extractAssetCodes(assetPoolObj);

            // 2. 提取参数
            String endDate = req.getEndDate();
            Integer historyWindow = req.getHistoryWindow() != null ? req.getHistoryWindow() : 720;

            // 3. 直接通过本地 Service 查询基础数据包 (宏观阶段与收益率)，注入请求中
            RiskDataQueryDTO queryDTO = new RiskDataQueryDTO();
            queryDTO.setAssetCodes(assetCodes);
            queryDTO.setEndDate(endDate);
            queryDTO.setHistoryWindow(historyWindow);
            RiskDataBundleVO riskData = stockReturnsService.getRiskDataBundle(queryDTO);

            // 3.1 业务校验：检查量化基础数据是否充足
            if (riskData == null || riskData.getReturns() == null || riskData.getReturns().isEmpty()) {
                return JsonResult.error(JsonResult.EXCEPTION_CODE_400, "测算数据不足，请确认所选日期是否有行情数据");
            }

            // 4. 组装 Python 请求实体
            QuantRiskBudgetRequest pythonReq = new QuantRiskBudgetRequest();
            pythonReq.setAssetPool(req.getAssetPool());
            pythonReq.setAssetPoolMajor(req.getAssetPoolMajor());
            pythonReq.setAssetPoolSector(req.getAssetPoolSector());
            pythonReq.setCycleRbRules(req.getCycleRbRules());
            pythonReq.setCycleRbRulesMajor(req.getCycleRbRulesMajor());
            pythonReq.setCycleRbRulesSector(req.getCycleRbRulesSector());
            pythonReq.setDataTable(req.getDataTable());
            pythonReq.setEndDate(endDate);
            pythonReq.setCustomBounds(req.getCustomBounds());
            pythonReq.setRiskData(riskData);

            // 5. 通过 OpenFeign 客户端调度 Python smartir-quant 微服务工具计算建议仓位
            return quantFeignClient.dynamicRiskBudget(pythonReq);
        } catch (Exception e) {
            return JsonResult.error("动态风险预算求解失败 (Feign): " + e.getMessage());
        }
    }

    @PostMapping({"/dynamic-risk-budget/backtest", "/backtest"})
    @ApiOperation("执行动态风险预算全景回测（结合本地风险数据并调度量化服务计算）")
    public JsonResult<Map<String, Object>> dynamicRiskBudgetBacktest(@RequestBody BacktestRiskBudgetDTO req) {
        try {
            // 1. 提取资产代码列表
            Object assetPoolObj = req.getAssetPool() != null ? req.getAssetPool() : req.getAssetPoolMajor();
            if (assetPoolObj == null) {
                assetPoolObj = req.getAssetPoolSector();
            }
            List<String> assetCodes = extractAssetCodes(assetPoolObj);

            // 2. 提取参数
            String startDate = req.getStartDate();
            String endDate = req.getEndDate();

            // 3. 直接通过本地 Service 查询基础数据包，注入请求中
            RiskDataQueryDTO queryDTO = new RiskDataQueryDTO();
            queryDTO.setAssetCodes(assetCodes);
            queryDTO.setStartDate(startDate);
            queryDTO.setEndDate(endDate);
            RiskDataBundleVO riskData = stockReturnsService.getRiskDataBundle(queryDTO);

            // 3.1 业务校验：检查回测数据是否充足
            if (riskData == null || riskData.getReturns() == null || riskData.getReturns().isEmpty() 
                || riskData.getStages() == null || riskData.getStages().isEmpty()) {
                return JsonResult.error(JsonResult.EXCEPTION_CODE_400, "回测数据不足，请选择有回测数据的时间范围");
            }

            // 4. 组装 Python 请求实体
            QuantBacktestRequest pythonReq = new QuantBacktestRequest();
            pythonReq.setAssetPool(req.getAssetPool());
            pythonReq.setAssetPoolMajor(req.getAssetPoolMajor());
            pythonReq.setAssetPoolSector(req.getAssetPoolSector());
            pythonReq.setCycleRbRules(req.getCycleRbRules());
            pythonReq.setCycleRbRulesMajor(req.getCycleRbRulesMajor());
            pythonReq.setCycleRbRulesSector(req.getCycleRbRulesSector());
            pythonReq.setDataTable(req.getDataTable());
            pythonReq.setStartDate(startDate);
            pythonReq.setEndDate(endDate);
            pythonReq.setRebalanceFreq(req.getRebalanceFreq());
            pythonReq.setCustomBounds(req.getCustomBounds());
            pythonReq.setHistoryWindow(req.getHistoryWindow());
            pythonReq.setTransactionCost(req.getTransactionCost());
            pythonReq.setRf(req.getRf());
            pythonReq.setRiskData(riskData);

            // 5. 通过 OpenFeign 客户端调度 Python smartir-quant 微服务工具执行回测
            return quantFeignClient.dynamicRiskBudgetBacktest(pythonReq);
        } catch (Exception e) {
            return JsonResult.error("动态风险预算回测失败 (Feign): " + e.getMessage());
        }
    }

    private List<String> extractAssetCodes(Object assetPoolObj) {
        List<String> assetCodes = new ArrayList<>();
        if (assetPoolObj instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) assetPoolObj;
            for (Object val : map.values()) {
                if (val instanceof Map) {
                    Object codeObj = ((Map<?, ?>) val).get("code");
                    if (codeObj != null) {
                        String code = String.valueOf(codeObj).trim().replace("`", "");
                        if (!code.isEmpty()) {
                            assetCodes.add(code);
                        }
                    }
                } else if (val instanceof String) {
                    String code = String.valueOf(val).trim().replace("`", "");
                    if (!code.isEmpty()) {
                        assetCodes.add(code);
                    }
                }
            }
        }
        return assetCodes;
    }
}

