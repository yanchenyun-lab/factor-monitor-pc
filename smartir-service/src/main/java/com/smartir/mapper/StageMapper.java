package com.smartir.mapper;

import com.smartir.vo.StageResultVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface StageMapper {

    List<StageResultVO> selectJoinedFactors(@Param("startDate") String startDate, @Param("endDate") String endDate);
    
    List<StageResultVO> selectJoinedFactorsWithStage(@Param("startDate") String startDate, @Param("endDate") String endDate);
}
