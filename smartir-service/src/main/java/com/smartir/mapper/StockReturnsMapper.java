package com.smartir.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartir.entity.StockReturnsDO;
import com.smartir.vo.StockReturnsRawVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface StockReturnsMapper extends BaseMapper<StockReturnsDO> {

    /**
     * 查询带宏观经济周期的收益率数据
     * @param assetCodes 资产代码列表 (为 null 或空时查询全部)
     * @param startDate 开始日期
     * @param endDate 截止日期
     * @return 收益率行列表
     */
    List<StockReturnsRawVO> selectReturnsWithStage(
            @Param("assetCodes") List<String> assetCodes,
            @Param("startDate") String startDate,
            @Param("endDate") String endDate
    );
}
