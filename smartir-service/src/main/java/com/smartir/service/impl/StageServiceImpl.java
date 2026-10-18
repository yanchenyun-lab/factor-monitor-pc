package com.smartir.service.impl;

import com.smartir.mapper.StageMapper;
import com.smartir.service.StageService;
import com.smartir.vo.StageResultVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;

@Service
public class StageServiceImpl implements StageService {

    @Autowired
    private StageMapper stageMapper;

    @Override
    public List<StageResultVO> getStageList(String startDate, String endDate) {
        // 如果 startDate 和 endDate 都不为空，说明是前端查询，直接从数据库读取 stage
        if (startDate != null || endDate != null) {
            return stageMapper.selectJoinedFactorsWithStage(startDate, endDate);
        }

        // 如果为空，说明是全量同步历史数据 (syncHistoricalStage) 调用的，需动态计算
        List<StageResultVO> list = stageMapper.selectJoinedFactors(startDate, endDate);

        setStage(list);

        return list;
    }

    private static void setStage(List<StageResultVO> list) {
        Integer lastStage = null;

        for (StageResultVO vo : list) {
            BigDecimal money = vo.getMoney();
            Integer credit = vo.getCredit();
            Integer growth = vo.getGrowth();

            if (money == null || credit == null || growth == null) {
                vo.setStage(lastStage);
                continue;
            }

            double m = money.doubleValue();
            double c = credit.doubleValue();
            double g = growth.doubleValue();

            Integer currentStage;

            if (m > 0 && c > 0 && g < 0) {
                currentStage = 1;
            } else if (m > 0 && c > 0 && g > 0) {
                currentStage = 2;
            } else if (m < 0 && c > 0 && g > 0) {
                currentStage = 3;
            } else if (m < 0 && c < 0 && g > 0) {
                currentStage = 4;
            } else if (m < 0 && c < 0 && g < 0) {
                currentStage = 5;
            } else if (m > 0 && c < 0 && g < 0) {
                currentStage = 6;
            } else {
                currentStage = lastStage;
            }

            vo.setStage(currentStage);
            lastStage = currentStage;
        }
    }

    @Override
    public List<StageResultVO> setStageDay(String date) {
        if (date != null) {
            List<StageResultVO> list = stageMapper.selectJoinedFactors(date, date);
            setStage(list);
            return list;
        }
        return java.util.Collections.emptyList();
    }
}
