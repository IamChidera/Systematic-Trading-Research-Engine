from datetime import datetime, timezone

import pytest

from trading_research.ops import (
    ExecutionAssumptions,
    age_minutes,
    build_risk_snapshot,
    detect_orders,
    readiness_check,
    simulate_execution,
)


def test_age_minutes_parses_utc_timestamp():
    now = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)

    assert age_minutes("2026-01-01T12:00:00+00:00", now=now) == 30.0


def test_detect_orders_adds_bot_name():
    reports = {"bot_a": {"orders": [{"symbol": "BTCUSDT", "side": "buy"}]}}

    orders = detect_orders(reports)

    assert orders == [{"bot": "bot_a", "symbol": "BTCUSDT", "side": "buy"}]


def test_simulate_execution_estimates_buy_fill_and_fee():
    orders = [{"bot": "bot_a", "symbol": "BTCUSDT", "side": "buy", "price": 100.0, "quantity": 2.0}]
    assumptions = ExecutionAssumptions(fee_pct=0.001, slippage_pct=0.001, spread_pct=0.002)

    ticket = simulate_execution(orders, assumptions)[0]

    assert ticket["estimated_fill_price"] == pytest.approx(100.2)
    assert ticket["estimated_fee"] == pytest.approx(0.2)
    assert ticket["status"] == "dry_run_only"


def test_build_risk_snapshot_aggregates_positions():
    reports = {
        "bot_a": {
            "equity": 10_000.0,
            "positions": {
                "BTCUSDT": {"notional": 1_000.0},
                "SOLUSDT": {"price": 50.0, "quantity": 4.0},
            },
        },
        "bot_b": {"equity": 5_000.0, "positions": {}},
    }

    snapshot = build_risk_snapshot(reports)

    assert snapshot["total_equity_observed"] == 15_000.0
    assert snapshot["total_open_notional"] == 1_200.0
    assert snapshot["open_bots"] == 1
    assert snapshot["open_symbols"] == 2
    assert snapshot["warnings"] == []


def test_readiness_check_blocks_stale_or_alerting_supervisor():
    now = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    heartbeat = {
        "status": "running",
        "last_cycle_finished_at": "2026-01-01T12:00:00+00:00",
        "alerts": ["FAILED:bot"],
    }

    report = readiness_check(heartbeat, {"orders_detected": 0}, {"warnings": []}, now=now)

    assert report["paper_ops_ready"] is False
    assert "STALE_HEARTBEAT" in report["blockers"]
    assert "SUPERVISOR_ALERTS_PRESENT" in report["blockers"]
