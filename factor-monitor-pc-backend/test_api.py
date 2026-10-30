# -*- coding: utf-8 -*-
"""
smartir-quant 量化服务接口测试用例
测试目标:
  - POST /dynamic-risk-budget       单日动态风险预算求解
  - POST /dynamic-risk-budget/backtest  全景历史回测

用法:
  python test_api.py                  # 运行所有测试
  python test_api.py budget           # 只测试单日风险预算
  python test_api.py backtest         # 只测试历史回测
"""

import sys
import json
import time
import requests

# ── 配置 ─────────────────────────────────────────────────────────────────────
# 直连 Python 后端（不经过 Java）
BASE_URL = "http://127.0.0.1:8000"

# 若走 Java smartir-service 转发（Nacos 已注册时推荐）
# BASE_URL = "http://127.0.0.1:8080/api/returns"

TIMEOUT_BUDGET  = 60    # 单日求解超时(秒)
TIMEOUT_BACKTEST = 300  # 回测超时(秒)，历史较长时计算量大

# ── 公共测试数据 ───────────────────────────────────────────────────────────────

# 大类资产池（6 种资产）
ASSET_POOL_MAJOR = {
    "param1": {"code": "H00852.SH",   "name": "中证1000全收益"},
    "param2": {"code": "H00300.CSI",  "name": "300收益"},
    "param3": {"code": "CBA00651.CS", "name": "中债-国债总财富(7-10年)"},
    "param4": {"code": "CBA00621.CS", "name": "中债-国债总财富(1-3年)"},
    "param5": {"code": "AU9999.SGE",  "name": "SGE黄金9999"},
    "param6": {"code": "000832.CSI",  "name": "中证转债"},
}

# 普林格宏观 6 周期风险预算配额（每个周期各资产的目标风险占比，行加总≤1）
CYCLE_RB_RULES = {
    "cycle1": {"param1": 0.50, "param2": 0.30, "param3": 0.05, "param4": 0.05, "param5": 0.05, "param6": 0.05},
    "cycle2": {"param1": 0.40, "param2": 0.35, "param3": 0.05, "param4": 0.05, "param5": 0.05, "param6": 0.10},
    "cycle3": {"param1": 0.10, "param2": 0.10, "param3": 0.30, "param4": 0.30, "param5": 0.15, "param6": 0.05},
    "cycle4": {"param1": 0.05, "param2": 0.05, "param3": 0.35, "param4": 0.35, "param5": 0.15, "param6": 0.05},
    "cycle5": {"param1": 0.10, "param2": 0.10, "param3": 0.25, "param4": 0.25, "param5": 0.25, "param6": 0.05},
    "cycle6": {"param1": 0.20, "param2": 0.15, "param3": 0.20, "param4": 0.20, "param5": 0.20, "param6": 0.05},
}

# 可选：权重硬约束（单资产最低/最高占比）
CUSTOM_BOUNDS = {
    "param1": [0.05, 0.60],
    "param2": [0.05, 0.60],
    "param3": [0.00, 0.50],
    "param4": [0.00, 0.50],
    "param5": [0.00, 0.20],
    "param6": [0.00, 0.20],
}


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def print_sep(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_json(data, indent=2, max_keys=10):
    """打印 JSON，若结果很大则只展示顶层键"""
    if isinstance(data, dict):
        keys = list(data.keys())
        if len(keys) > max_keys:
            print(f"  [返回 {len(keys)} 个顶层字段]: {keys}")
            for k in keys[:max_keys]:
                v = data[k]
                preview = str(v)[:120] + "..." if len(str(v)) > 120 else v
                print(f"    {k}: {preview}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=indent, default=str))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=indent, default=str))


def check_health():
    """健康检查"""
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"  ✅ 服务健康检查: {r.status_code} → {r.json()}")
        return True
    except Exception as e:
        print(f"  ❌ 服务不可达: {e}")
        print(f"     请确认 factor-monitor-pc-backend 已在 {BASE_URL} 运行")
        return False


# ── 测试用例 1：单日动态风险预算 ───────────────────────────────────────────────

def test_dynamic_risk_budget_basic():
    """基础测试：使用最新交易日，不指定 end_date"""
    print_sep("测试 1-A: /dynamic-risk-budget  【最新交易日，无日期约束】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget", json=payload, timeout=TIMEOUT_BUDGET)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()
    print_json(data)

    assert r.status_code == 200, f"期望 200，实际 {r.status_code}"
    assert data.get("code") == 200 or "current_cycle" in str(data), "响应体异常"
    print("  ✅ PASS")
    return data


def test_dynamic_risk_budget_with_date():
    """指定截止日期测试"""
    print_sep("测试 1-B: /dynamic-risk-budget  【指定 end_date = 2024-12-31】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
        "end_date": "2024-12-31",
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget", json=payload, timeout=TIMEOUT_BUDGET)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()
    print_json(data)

    assert r.status_code == 200
    print("  ✅ PASS")


def test_dynamic_risk_budget_with_bounds():
    """含权重硬约束的测试"""
    print_sep("测试 1-C: /dynamic-risk-budget  【含 custom_bounds 权重约束】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
        "end_date": "2025-06-30",
        "custom_bounds": CUSTOM_BOUNDS,
        "history_window": 500,
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget", json=payload, timeout=TIMEOUT_BUDGET)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()
    print_json(data)

    assert r.status_code == 200
    print("  ✅ PASS")


def test_dynamic_risk_budget_missing_param():
    """缺少必填参数测试（期望返回错误）"""
    print_sep("测试 1-D: /dynamic-risk-budget  【缺少 cycle_rb_rules → 应返回错误】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        # 故意缺少 cycle_rb_rules
    }

    r = requests.post(f"{BASE_URL}/dynamic-risk-budget", json=payload, timeout=TIMEOUT_BUDGET)
    print(f"  HTTP {r.status_code}")
    data = r.json()
    print_json(data)

    # 期望返回错误响应（code != 200 或含 error/message 字段）
    is_error = (
        r.status_code != 200
        or data.get("code", 200) != 200
        or "error" in str(data).lower()
        or "缺少" in str(data)
    )
    assert is_error, "缺少必填参数时应返回错误响应"
    print("  ✅ PASS（正确返回了错误）")


# ── 测试用例 2：历史回测 ───────────────────────────────────────────────────────

def test_backtest_1year():
    """1 年期历史回测（近 1 年，计算量适中）"""
    print_sep("测试 2-A: /dynamic-risk-budget/backtest  【2024 全年回测】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "rebalance_freq": "M_or_stage_change",
        "transaction_cost": 0.0003,
        "rf": 0.02,
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget/backtest", json=payload, timeout=TIMEOUT_BACKTEST)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()

    # 只打印顶层结构，避免刷屏
    if isinstance(data, dict):
        top = data.get("data") or data
        if isinstance(top, dict):
            print(f"  返回字段: {list(top.keys())}")
            # 打印关键指标
            metrics = top.get("metrics_summary") or top.get("raw_metrics") or {}
            if metrics:
                print("  绩效指标摘要:")
                for k, v in list(metrics.items())[:8]:
                    print(f"    {k}: {v}")
            nav = top.get("nav_series") or []
            print(f"  净值序列长度: {len(nav)} 条")
        else:
            print_json(data)
    else:
        print_json(data)

    assert r.status_code == 200
    print("  ✅ PASS")


def test_backtest_3year():
    """3 年期历史回测"""
    print_sep("测试 2-B: /dynamic-risk-budget/backtest  【近 3 年（2022-2024）】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
        "start_date": "2022-01-01",
        "end_date": "2024-12-31",
        "rebalance_freq": "M",             # 每月调仓
        "custom_bounds": CUSTOM_BOUNDS,
        "history_window": 720,
        "transaction_cost": 0.0005,        # 万五摩擦
        "rf": 0.025,
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget/backtest", json=payload, timeout=TIMEOUT_BACKTEST)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()

    top = (data.get("data") or data) if isinstance(data, dict) else {}
    if isinstance(top, dict):
        print(f"  返回字段: {list(top.keys())}")
        metrics = top.get("metrics_summary") or top.get("raw_metrics") or {}
        if metrics:
            print("  绩效指标摘要:")
            for k, v in list(metrics.items())[:8]:
                print(f"    {k}: {v}")

    assert r.status_code == 200
    print("  ✅ PASS")


def test_backtest_stage_change():
    """按周期切换调仓的回测"""
    print_sep("测试 2-C: /dynamic-risk-budget/backtest  【周期切换调仓（stage_change）】")

    payload = {
        "asset_pool": ASSET_POOL_MAJOR,
        "cycle_rb_rules": CYCLE_RB_RULES,
        "start_date": "2023-01-01",
        "end_date": "2025-06-30",
        "rebalance_freq": "stage_change",  # 只在宏观阶段切换时调仓
        "history_window": 480,
        "rf": 0.02,
    }

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dynamic-risk-budget/backtest", json=payload, timeout=TIMEOUT_BACKTEST)
    elapsed = time.time() - t0

    print(f"  HTTP {r.status_code}  耗时: {elapsed:.2f}s")
    data = r.json()

    top = (data.get("data") or data) if isinstance(data, dict) else {}
    if isinstance(top, dict):
        print(f"  返回字段: {list(top.keys())}")
        alloc = top.get("allocation_series") or []
        print(f"  调仓序列长度: {len(alloc)} 条")

    assert r.status_code == 200
    print("  ✅ PASS")


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_all():
    print_sep("smartir-quant API 测试套件")
    print(f"  目标地址: {BASE_URL}")

    if not check_health():
        sys.exit(1)

    results = []

    test_cases_budget = [
        ("1-A 单日基础", test_dynamic_risk_budget_basic),
        ("1-B 指定日期", test_dynamic_risk_budget_with_date),
        ("1-C 含权重约束", test_dynamic_risk_budget_with_bounds),
        ("1-D 缺少参数", test_dynamic_risk_budget_missing_param),
    ]
    test_cases_backtest = [
        ("2-A 1年回测", test_backtest_1year),
        ("2-B 3年回测", test_backtest_3year),
        ("2-C 周期调仓", test_backtest_stage_change),
    ]

    arg = sys.argv[1] if len(sys.argv) > 1 else "all"

    if arg in ("all", "budget"):
        for name, fn in test_cases_budget:
            try:
                fn()
                results.append((name, "PASS"))
            except Exception as e:
                results.append((name, f"FAIL: {e}"))

    if arg in ("all", "backtest"):
        for name, fn in test_cases_backtest:
            try:
                fn()
                results.append((name, "PASS"))
            except Exception as e:
                results.append((name, f"FAIL: {e}"))

    # 汇总
    print_sep("测试结果汇总")
    passed = sum(1 for _, r in results if r == "PASS")
    for name, result in results:
        icon = "✅" if result == "PASS" else "❌"
        print(f"  {icon} {name}: {result}")
    print(f"\n  总计: {passed}/{len(results)} 通过")


if __name__ == "__main__":
    run_all()

