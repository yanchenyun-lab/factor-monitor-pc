package com.smartir.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.smartir.dto.ReturnStatsQueryDTO;
import com.smartir.entity.StockReturnsDO;
import com.smartir.mapper.StockReturnsMapper;
import com.smartir.service.StockReturnsService;
import com.smartir.util.AssetCodeHelper;
import com.smartir.vo.StockDailyReturnsVO;
import com.smartir.vo.StockReturnsRawVO;
import com.smartir.vo.StageReturnStatsVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class StockReturnsServiceImpl extends ServiceImpl<StockReturnsMapper, StockReturnsDO> implements StockReturnsService {

    @Autowired
    private com.smartir.mapper.HistoricalStageMapper historicalStageMapper;

    @Override
    public List<StockDailyReturnsVO> getDailyReturns(List<String> assetCodes) {
        List<String> queryCodes = (assetCodes != null && !assetCodes.isEmpty()) ? new ArrayList<>(assetCodes) : null;
        List<StockReturnsRawVO> rawList = this.baseMapper.selectReturnsWithStage(queryCodes, null, null);
        Map<String, StockDailyReturnsVO> dateMap = new LinkedHashMap<>();

        for (StockReturnsRawVO raw : rawList) {
            String date = raw.getTradeDate();
            StockDailyReturnsVO daily = dateMap.computeIfAbsent(date, d -> {
                StockDailyReturnsVO vo = new StockDailyReturnsVO();
                vo.setTradeDate(d);
                vo.setStage(raw.getStage());
                return vo;
            });

            if (daily.getStage() == null && raw.getStage() != null) {
                daily.setStage(raw.getStage());
            }

            if (raw.getAssetCode() != null) {
                daily.addReturn(raw.getAssetCode(), raw.getReturnRate());
                String camel = AssetCodeHelper.toCamelCase(raw.getAssetCode());
                if (camel != null && !camel.equals(raw.getAssetCode())) {
                    daily.addExtra(camel, raw.getReturnRate());
                }
            }
        }

        return new ArrayList<>(dateMap.values());
    }

    @Override
    public List<StageReturnStatsVO> getStageStats(List<String> assetCodes, ReturnStatsQueryDTO queryDTO) {
        String startDate = queryDTO != null ? queryDTO.getStartDate() : null;
        String endDate = queryDTO != null ? queryDTO.getEndDate() : null;

        List<String> queryCodes = (assetCodes != null && !assetCodes.isEmpty()) ? new ArrayList<>(assetCodes) : null;
        List<StockReturnsRawVO> rawList = this.baseMapper.selectReturnsWithStage(queryCodes, startDate, endDate);

        // 按宏观周期 (1~6) 分组
        Map<Integer, List<StockReturnsRawVO>> groupedByStage = rawList.stream()
                .filter(vo -> vo.getStage() != null)
                .collect(Collectors.groupingBy(StockReturnsRawVO::getStage));

        // 确定需要计算统计的标的列表
        Set<String> targetCodes = new LinkedHashSet<>();
        if (assetCodes != null && !assetCodes.isEmpty()) {
            targetCodes.addAll(assetCodes);
        } else {
            rawList.stream().map(StockReturnsRawVO::getAssetCode).filter(Objects::nonNull).forEach(targetCodes::add);
        }

        List<StageReturnStatsVO> result = new ArrayList<>();
        for (int i = 1; i <= 6; i++) {
            StageReturnStatsVO statsVO = new StageReturnStatsVO();
            statsVO.setStage(i);

            List<StockReturnsRawVO> stageList = groupedByStage.getOrDefault(i, Collections.emptyList());
            long dayCount = stageList.stream().map(StockReturnsRawVO::getTradeDate).distinct().count();

            Map<String, List<BigDecimal>> ratesByAsset = stageList.stream()
                    .filter(vo -> vo.getAssetCode() != null && vo.getReturnRate() != null)
                    .collect(Collectors.groupingBy(
                            StockReturnsRawVO::getAssetCode,
                            Collectors.mapping(StockReturnsRawVO::getReturnRate, Collectors.toList())
                    ));

            for (String code : targetCodes) {
                List<BigDecimal> rates = ratesByAsset.getOrDefault(code, Collections.emptyList());
                BigDecimal annualReturn = calculateGeometricReturn(rates, (int) dayCount);
                statsVO.addStat(code, annualReturn);

                String camel = AssetCodeHelper.toCamelCase(code);
                if (camel != null && !camel.equals(code)) {
                    statsVO.addExtra(camel, annualReturn);
                }
            }

            result.add(statsVO);
        }

        return result;
    }

    /**
     * 计算几何年化收益率
     * 数据库存储值为价格倍数 (1 + r)，连乘后开 (243 / count) 次方并减 1
     */
    private BigDecimal calculateGeometricReturn(List<BigDecimal> values, int count) {
        if (count == 0 || values.isEmpty()) {
            return BigDecimal.ZERO;
        }

        double product = 1.0;
        int validCount = 0;
        for (BigDecimal val : values) {
            if (val != null) {
                product *= val.doubleValue();
                validCount++;
            }
        }

        if (validCount == 0) {
            return BigDecimal.ZERO;
        }

        double annualized = Math.pow(product, 243.0 / count) - 1.0;
        return new BigDecimal(annualized).setScale(4, RoundingMode.HALF_UP);
    }

    @Override
    public com.smartir.vo.RiskDataBundleVO getRiskDataBundle(com.smartir.dto.RiskDataQueryDTO queryDTO) {
        com.smartir.vo.RiskDataBundleVO bundle = new com.smartir.vo.RiskDataBundleVO();
        String endDate = queryDTO != null ? queryDTO.getEndDate() : null;
        String startDate = queryDTO != null ? queryDTO.getStartDate() : null;
        Integer historyWindow = queryDTO != null ? queryDTO.getHistoryWindow() : null;
        List<String> assetCodes = (queryDTO != null && queryDTO.getAssetCodes() != null && !queryDTO.getAssetCodes().isEmpty())
                ? queryDTO.getAssetCodes() : null;

        // 1. 获取全量宏观周期阶段数据 (stock_historical_stage)
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.smartir.entity.HistoricalStageDO> stageWrapper =
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
        stageWrapper.select(com.smartir.entity.HistoricalStageDO::getTradeDate, com.smartir.entity.HistoricalStageDO::getStage)
                .orderByAsc(com.smartir.entity.HistoricalStageDO::getTradeDate);
        List<com.smartir.entity.HistoricalStageDO> stageDOList = historicalStageMapper.selectList(stageWrapper);

        List<com.smartir.vo.StageItemVO> stageVOList = new ArrayList<>();
        Integer latestStage = null;
        com.smartir.entity.HistoricalStageDO earliestStageDO = stageDOList.isEmpty() ? null : stageDOList.get(0);

        for (com.smartir.entity.HistoricalStageDO stageDO : stageDOList) {
            String td = stageDO.getTradeDate();
            Integer st = stageDO.getStage();
            stageVOList.add(new com.smartir.vo.StageItemVO(td, st, formatCycleName(st)));

            if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isNotBlank(endDate)) {
                if (td.compareTo(endDate) <= 0) {
                    latestStage = st;
                }
            } else {
                latestStage = st;
            }
        }

        // 若查询日期早于库内最早记录，向左顺延最早一条记录
        if (latestStage == null && earliestStageDO != null) {
            latestStage = earliestStageDO.getStage();
        }
        if (latestStage == null) {
            latestStage = 1;
        }

        bundle.setStages(stageVOList);
        bundle.setLatestStage(latestStage);
        bundle.setLatestCycleName(formatCycleName(latestStage));

        // 2. 计算收益率时间窗口 (若指定了 historyWindow 且未传 startDate，则截取最近 N 个交易日)
        String actualStartDate = startDate;
        String actualEndDate = endDate;

        if ((historyWindow != null && historyWindow > 0) && com.baomidou.mybatisplus.core.toolkit.StringUtils.isBlank(actualStartDate)) {
            com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<StockReturnsDO> dateQuery =
                    new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
            dateQuery.select("DISTINCT trade_date").orderByDesc("trade_date");
            if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isNotBlank(actualEndDate)) {
                dateQuery.le("trade_date", actualEndDate);
            }
            dateQuery.last("LIMIT " + historyWindow);
            List<StockReturnsDO> recentDates = this.baseMapper.selectList(dateQuery);
            if (!recentDates.isEmpty()) {
                actualStartDate = recentDates.get(recentDates.size() - 1).getTradeDate();
                if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isBlank(actualEndDate)) {
                    actualEndDate = recentDates.get(0).getTradeDate();
                }
            }
        }

        // 3. 提取资产收益率明细数据 (stock_returns)
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<StockReturnsDO> retWrapper =
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
        retWrapper.select(StockReturnsDO::getTradeDate, StockReturnsDO::getAssetCode, StockReturnsDO::getReturnRate)
                .orderByAsc(StockReturnsDO::getTradeDate)
                .orderByAsc(StockReturnsDO::getAssetCode);

        if (assetCodes != null && !assetCodes.isEmpty()) {
            retWrapper.in(StockReturnsDO::getAssetCode, assetCodes);
        }
        if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isNotBlank(actualStartDate)) {
            retWrapper.ge(StockReturnsDO::getTradeDate, actualStartDate);
        }
        if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isNotBlank(actualEndDate)) {
            retWrapper.le(StockReturnsDO::getTradeDate, actualEndDate);
        }

        List<StockReturnsDO> retDOList = this.baseMapper.selectList(retWrapper);
        List<com.smartir.vo.ReturnItemVO> returnVOList = new ArrayList<>(retDOList.size());
        Set<String> distinctDates = new TreeSet<>();

        for (StockReturnsDO retDO : retDOList) {
            returnVOList.add(new com.smartir.vo.ReturnItemVO(retDO.getTradeDate(), retDO.getAssetCode(), retDO.getReturnRate()));
            distinctDates.add(retDO.getTradeDate());
        }

        bundle.setReturns(returnVOList);
        bundle.setTotalDays(distinctDates.size());
        if (!distinctDates.isEmpty()) {
            bundle.setMinDate(((TreeSet<String>) distinctDates).first());
            bundle.setMaxDate(((TreeSet<String>) distinctDates).last());
        }

        return bundle;
    }

    private String formatCycleName(Integer stage) {
        if (stage == null) return "阶段1-信用扩张";
        switch (stage) {
            case 1: return "阶段1-信用扩张";
            case 2: return "阶段2-经济复苏";
            case 3: return "阶段3-货币退潮";
            case 4: return "阶段4-信用退潮";
            case 5: return "阶段5-经济放缓";
            case 6: return "阶段6-货币扩张";
            default: return "阶段" + stage;
        }
    }
}

