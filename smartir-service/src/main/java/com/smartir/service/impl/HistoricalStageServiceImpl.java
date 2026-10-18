package com.smartir.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.smartir.entity.HistoricalStageDO;
import com.smartir.mapper.HistoricalStageMapper;
import com.smartir.service.HistoricalStageService;
import com.smartir.service.StageService;
import com.smartir.vo.StageResultVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class HistoricalStageServiceImpl extends ServiceImpl<HistoricalStageMapper, HistoricalStageDO> implements HistoricalStageService {

    @Autowired
    private StageService stageService;


    @Override
    public void syncHistoricalStage() {
        // 1. Get the computed stages
        List<StageResultVO> list = stageService.getStageList(null, null);

        // 2. Clear old data
        this.remove(null);

        // 3. Prepare new data
        List<HistoricalStageDO> insertList = new ArrayList<>();
        for (StageResultVO vo : list) {
            HistoricalStageDO stageDO = new HistoricalStageDO();
            stageDO.setId(UUID.randomUUID().toString().replace("-", ""));
            stageDO.setTradeDate(vo.getTradeDate());
            stageDO.setStage(vo.getStage());
            insertList.add(stageDO);
        }

        // 4. Batch insert
        this.saveBatch(insertList, 500);
    }

    @Override

    public void syncHistoricalStageDay(String date) {
        List<StageResultVO> list = stageService.setStageDay(date);

        QueryWrapper<HistoricalStageDO> objectQueryWrapper = new QueryWrapper<>();
        objectQueryWrapper.eq("trade_date", date);
        this.remove(objectQueryWrapper);

        // 3. Prepare new data
        List<HistoricalStageDO> insertList = new ArrayList<>();
        for (StageResultVO vo : list) {
            HistoricalStageDO stageDO = new HistoricalStageDO();
            stageDO.setId(UUID.randomUUID().toString().replace("-", ""));
            stageDO.setTradeDate(vo.getTradeDate());
            stageDO.setStage(vo.getStage());
            insertList.add(stageDO);
        }
        this.saveBatch(insertList, 1);

    }
}
