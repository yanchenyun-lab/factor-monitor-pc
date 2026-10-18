package com.smartir.controller;

import com.smartir.dto.ReturnStatsQueryDTO;
import com.smartir.service.StockReturnsService;
import com.smartir.util.AssetCodeHelper;
import com.smartir.vo.StockDailyReturnsVO;
import com.smartir.vo.StageReturnStatsVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/returns")
@Api(tags = "资产及行业收益率数据接口")
public class ReturnsController {

    @Autowired
    private StockReturnsService stockReturnsService;

    @PostMapping("/list")
    @ApiOperation("获取所有资产及板块的历史日频收益率序列")
    public List<StockDailyReturnsVO> getAllReturnsList(@RequestBody(required = false) List<String> assetCodes) {
        return stockReturnsService.getDailyReturns(assetCodes);
    }

    @PostMapping("/stats")
    @ApiOperation("按经济周期分组统计所有资产及板块的年化收益率")
    public List<StageReturnStatsVO> getAllStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return stockReturnsService.getStageStats(null, queryDTO);
    }

    @PostMapping("/asset/list")
    @ApiOperation("获取大类资产的历史收益率序列")
    public List<StockDailyReturnsVO> getAssetReturnsList() {
        return stockReturnsService.getDailyReturns(AssetCodeHelper.MAJOR_ASSET_CODES);
    }

    @PostMapping("/sector-excess/list")
    @ApiOperation("获取行业板块的历史超额收益率序列")
    public List<StockDailyReturnsVO> getSectorExcessReturnsList() {
        return stockReturnsService.getDailyReturns(AssetCodeHelper.SECTOR_ASSET_CODES);
    }

    @PostMapping("/asset/stats")
    @ApiOperation("按经济周期分组统计大类资产的年化收益率")
    public List<StageReturnStatsVO> getAssetStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return stockReturnsService.getStageStats(AssetCodeHelper.MAJOR_ASSET_CODES, queryDTO);
    }

    @PostMapping("/sector-excess/stats")
    @ApiOperation("按经济周期分组统计行业板块的超额收益率")
    public List<StageReturnStatsVO> getSectorStats(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        return stockReturnsService.getStageStats(AssetCodeHelper.SECTOR_ASSET_CODES, queryDTO);
    }

    @PostMapping("/candidates")
    @ApiOperation("获取候选大类资产与候选行业板块清单")
    public Map<String, Object> getCandidates() {
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

        return response;
    }

    private Map<String, String> createCandidate(String code, String name) {
        Map<String, String> map = new HashMap<>();
        map.put("code", code);
        map.put("name", name);
        return map;
    }

    @PostMapping("/risk-data")
    @ApiOperation("供量化风险预算与回测模型获取宏观阶段与资产收益率时序包")
    public com.smartir.vo.RiskDataBundleVO getRiskDataBundle(@RequestBody(required = false) com.smartir.dto.RiskDataQueryDTO queryDTO) {
        return stockReturnsService.getRiskDataBundle(queryDTO);
    }
}

