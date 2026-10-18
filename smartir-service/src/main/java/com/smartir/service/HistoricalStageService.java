package com.smartir.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.smartir.entity.HistoricalStageDO;

public interface HistoricalStageService extends IService<HistoricalStageDO> {
    void syncHistoricalStage();

    void syncHistoricalStageDay(String date);
}
