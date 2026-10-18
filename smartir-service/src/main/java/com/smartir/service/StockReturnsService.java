package com.smartir.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.smartir.dto.ReturnStatsQueryDTO;
import com.smartir.entity.StockReturnsDO;
import com.smartir.vo.StockDailyReturnsVO;
import com.smartir.vo.StageReturnStatsVO;

import java.util.List;

public interface StockReturnsService extends IService<StockReturnsDO> {

    /**
     * 获取指定资产的时序日频收益率列表 (按交易日升序聚合)
     * @param assetCodes 资产代码列表，传 null 则获取全部
     * @return 逐日聚合对象列表
     */
    List<StockDailyReturnsVO> getDailyReturns(List<String> assetCodes);

    /**
     * 分宏观周期 (阶段1-6) 统计资产的年化几何收益率
     * @param assetCodes 待统计资产代码列表
     * @param queryDTO 查询条件 (包含 startDate, endDate)
     * @return 6个宏观阶段的收益率统计列表
     */
    List<StageReturnStatsVO> getStageStats(List<String> assetCodes, ReturnStatsQueryDTO queryDTO);

    /**
     * 获取供量化风险预算模型与回测引擎专用的数据包
     * @param queryDTO 查询条件 (包含 assetCodes, startDate, endDate, historyWindow)
     * @return RiskDataBundleVO 包含宏观阶段与资产收益率时序
     */
    com.smartir.vo.RiskDataBundleVO getRiskDataBundle(com.smartir.dto.RiskDataQueryDTO queryDTO);
}


