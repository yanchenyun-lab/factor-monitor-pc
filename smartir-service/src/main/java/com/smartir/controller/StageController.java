package com.smartir.controller;

import com.baomidou.mybatisplus.core.toolkit.StringUtils;
import com.smartir.service.StageService;
import com.smartir.vo.StageResultVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import com.smartir.dto.ReturnStatsQueryDTO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/factors/stage")
@Api(tags = "周期阶段计算接口")
public class StageController {

    @Autowired
    private StageService stageService;

    @Autowired
    private com.smartir.service.HistoricalStageService historicalStageService;

    @PostMapping("/list")
    @ApiOperation("获取完整的周期阶段推导数据")
    public List<StageResultVO> getStageList(@RequestBody(required = false) ReturnStatsQueryDTO queryDTO) {
        String startDate = queryDTO != null ? queryDTO.getStartDate() : null;
        String endDate = queryDTO != null ? queryDTO.getEndDate() : null;
        return stageService.getStageList(startDate, endDate);
    }

    @PostMapping("/sync-table")
    @ApiOperation("同步历史阶段数据到中间表")
    public String syncHistoricalStage() {
        historicalStageService.syncHistoricalStage();
        return "Sync successful";
    }

    @PostMapping("/sync-table-day")
    @ApiOperation("同步历史阶段数据到中间表(每日)")
    public String syncHistoricalStageDay(@RequestParam String date) {
        if (StringUtils.isBlank(date)) {
            return "日期不能为空";
        }
        historicalStageService.syncHistoricalStageDay(date);
        return "同步" + date + "成功";
    }
}
