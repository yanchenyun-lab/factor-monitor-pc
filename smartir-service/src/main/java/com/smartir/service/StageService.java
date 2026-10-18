package com.smartir.service;

import com.smartir.vo.StageResultVO;

import java.util.List;

public interface StageService {
    List<StageResultVO> getStageList(String startDate, String endDate);

    List<StageResultVO> setStageDay(String date);
}
