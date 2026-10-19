# -*- coding: utf-8 -*-
"""
================================================================================
量化风险预算与时序回测服务 API 路由定义
技术栈: FastAPI + Uvicorn + Starlette + Pydantic
100% 对齐内网云桌面 smartir-quant 微服务架构
================================================================================
"""

import sys
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

# 统一路径配置
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# 导入统一响应封装与核心量化算法
try:
    from api.response import ResponseModel
    from api.dynamic_risk_budget import run_dynamic_risk_budget
    from api.backtest_dynamic_risk_budget import run_backtest_api
except ImportError:
    from response import ResponseModel
    from dynamic_risk_budget import run_dynamic_risk_budget
    from backtest_dynamic_risk_budget import run_backtest_api

logger = logging.getLogger("smartir-quant.routes")

router = APIRouter()


# ==============================================================================
# Pydantic 请求模型定义 (100% 对齐前端与内网云桌面 routes.py 规范)
# ==============================================================================

class DynamicRiskBudgetRequest(BaseModel):
    """单日动态风险预算求解请求入参"""
    asset_pool: Optional[Dict[str, Any]] = Field(default=None, description="资产定义字典")
    asset_pool_major: Optional[Dict[str, Any]] = Field(default=None, description="大类资产池别名")
    asset_pool_sector: Optional[Dict[str, Any]] = Field(default=None, description="行业板块资产池别名")

    cycle_rb_rules: Optional[Dict[str, Any]] = Field(default=None, description="宏观6周期目标风险预算配额字典")
    cycle_rb_rules_major: Optional[Dict[str, Any]] = Field(default=None, description="大类资产规则别名")
    cycle_rb_rules_sector: Optional[Dict[str, Any]] = Field(default=None, description="行业板块规则别名")

    data_table: Optional[str] = Field(default="stock_returns", description="行情收益率数据源标识")
    end_date: Optional[str] = Field(default=None, description="测算截止日期 (YYYY-MM-DD)，默认为最新交易日")
    custom_bounds: Optional[Dict[str, Any]] = Field(default=None, description="单资产持仓权重硬约束")
    api_base_url: Optional[str] = Field(default=None, description="smartIR Java 后端 HTTP 基础地址，默认读取 SMARTIR_API_BASE 或 http://127.0.0.1:8080")


class BacktestRiskBudgetRequest(BaseModel):
    """历史时序推演与全景回测请求入参"""
    asset_pool: Optional[Dict[str, Any]] = Field(default=None, description="资产定义字典")
    asset_pool_major: Optional[Dict[str, Any]] = Field(default=None, description="大类资产池别名")
    asset_pool_sector: Optional[Dict[str, Any]] = Field(default=None, description="行业板块资产池别名")

    cycle_rb_rules: Optional[Dict[str, Any]] = Field(default=None, description="宏观6周期目标风险预算配额字典")
    cycle_rb_rules_major: Optional[Dict[str, Any]] = Field(default=None, description="大类资产规则别名")
    cycle_rb_rules_sector: Optional[Dict[str, Any]] = Field(default=None, description="行业板块规则别名")

    data_table: Optional[str] = Field(default="stock_returns", description="行情收益率数据源标识")
    start_date: Optional[str] = Field(default=None, description="回测起始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="回测截止日期 (YYYY-MM-DD)")
    rebalance_freq: Optional[str] = Field(default="M_or_stage_change", description="调仓频率: M, stage_change, M_or_stage_change")
    custom_bounds: Optional[Dict[str, Any]] = Field(default=None, description="权重硬边界约束")
    history_window: Optional[int] = Field(default=720, description="滚动协方差估计窗口交易日天数")
    transaction_cost: Optional[float] = Field(default=0.0003, description="单边调仓摩擦损耗率 (默认万三)")
    rf: Optional[float] = Field(default=0.02, description="无风险年化利率 (默认 2%)")
    api_base_url: Optional[str] = Field(default=None, description="smartIR Java 后端 HTTP 基础地址，默认读取 SMARTIR_API_BASE 或 http://127.0.0.1:8080")


# ==============================================================================
# 基础探测接口
# ==============================================================================

@router.get("/")
def root():
    return ResponseModel.success({"service": "smartir-quant", "status": "running"})


@router.get("/demo")
@router.get("/api/demo")
def demo():
    return ResponseModel.success("ok")


@router.post("/test")
@router.post("/api/test")
def test():
    return ResponseModel.success()


# ==============================================================================
# 1. 动态风险预算单日测算接口
# ==============================================================================

@router.post("/risk/dynamic-budget")
@router.post("/dynamic-risk-budget")
@router.post("/api/dynamic-risk-budget")
@router.post("/api/risk/dynamic-budget")
def dynamic_risk_budget(req: DynamicRiskBudgetRequest):
    """
    求解指定交易日的宏观经济周期与最优资产配置建议仓位
    """
    try:
        payload = req.model_dump(exclude_unset=True)

        asset_pool = payload.get("asset_pool") or payload.get("asset_pool_major") or payload.get("asset_pool_sector")
        cycle_rb_rules = payload.get("cycle_rb_rules") or payload.get("cycle_rb_rules_major") or payload.get("cycle_rb_rules_sector")
        data_table = payload.get("data_table") or "stock_returns"
        end_date = payload.get("end_date")
        custom_bounds = payload.get("custom_bounds")
        api_base_url = payload.get("api_base_url")

        if not asset_pool:
            return ResponseModel.error("缺少必填参数: asset_pool (或 asset_pool_major / asset_pool_sector)")
        if not cycle_rb_rules:
            return ResponseModel.error("缺少必填参数: cycle_rb_rules (或 cycle_rb_rules_major / cycle_rb_rules_sector)")

        cycle, positions, calc_date = run_dynamic_risk_budget(
            asset_pool=asset_pool,
            cycle_rb_rules=cycle_rb_rules,
            data_table=data_table,
            end_date=end_date,
            custom_bounds=custom_bounds,
            api_base_url=api_base_url
        )

        return ResponseModel.success({
            "current_cycle": cycle,
            "calc_date": calc_date,
            "positions": positions
        })
    except Exception as e:
        logger.exception("动态风险预算计算异常")
        return ResponseModel.error(f"动态风险预算计算异常: {str(e)}")


# ==============================================================================
# 2. 动态风险预算全景历史回测接口
# ==============================================================================

@router.post("/risk/backtest")
@router.post("/dynamic-risk-budget/backtest")
@router.post("/api/dynamic-risk-budget/backtest")
@router.post("/api/risk/backtest")
def dynamic_risk_budget_backtest(req: BacktestRiskBudgetRequest):
    """
    执行历史时序全景回测，输出逐日净值、权重时序、宏观阶段色块以及量化绩效看板指标
    """
    try:
        payload = req.model_dump(exclude_unset=True)
        res = run_backtest_api(payload)
        return ResponseModel.success(res)
    except Exception as e:
        logger.exception("动态风险预算回测异常")
        return ResponseModel.error(f"动态风险预算回测异常: {str(e)}")
