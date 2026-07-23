from pathlib import Path

import pytest

from trading_research.contracts import SleeveTarget, combine_sleeve_targets
from trading_research.execution import (
    ExecutionPolicy,
    MarketRule,
    Position,
    reconcile_portfolio,
)
from trading_research.execution_ledger import ExecutionLedger


RULES = {
    "BTCUSDT": MarketRule(min_quantity=0.0001, quantity_step=0.00000001),
    "SOLUSDT": MarketRule(min_quantity=0.01, quantity_step=0.001),
}
PRICES = {"BTCUSDT": 50_000.0, "SOLUSDT": 100.0}


def test_reconciliation_executes_sells_before_buys():
    target = combine_sleeve_targets(
        [
            SleeveTarget("core", 0.50, {"BTCUSDT": 1.0}, "core active"),
            SleeveTarget("growth", 0.40, {"SOLUSDT": 1.0}, "SOL ranks first"),
        ]
    )
    result = reconcile_portfolio(
        cash=10.0,
        positions={"BTCUSDT": Position("BTCUSDT", 0.002, 50_000.0)},
        target=target,
        market_rules=RULES,
        reference_prices=PRICES,
    )

    assert result.execution_phase == "sell"
    assert [ticket.side for ticket in result.executable_tickets] == ["sell"]
    assert any(item["reason"] == "buy_waits_for_post_sale_reconciliation" for item in result.deferred)


def test_reconciliation_has_no_fixed_account_or_ticket_value_cap():
    target = combine_sleeve_targets(
        [SleeveTarget("core", 0.99, {"BTCUSDT": 1.0}, "core active")]
    )
    result = reconcile_portfolio(
        cash=1_000_000.0,
        positions={},
        target=target,
        market_rules=RULES,
        reference_prices=PRICES,
        policy=ExecutionPolicy(buy_cash_buffer_fraction=0.0),
    )

    assert result.execution_phase == "buy"
    assert result.executable_tickets[0].notional == pytest.approx(990_000.0)


def test_reconciliation_defers_below_exchange_minimum():
    target = combine_sleeve_targets(
        [SleeveTarget("core", 0.10, {"BTCUSDT": 1.0}, "starter")]
    )
    result = reconcile_portfolio(
        cash=20.0,
        positions={},
        target=target,
        market_rules=RULES,
        reference_prices=PRICES,
    )

    assert result.executable_tickets == ()
    assert result.deferred[0]["reason"] == "below_market_minimum"


def test_execution_ledger_records_decision_and_reason(tmp_path: Path):
    target = combine_sleeve_targets(
        [SleeveTarget("core", 0.50, {"BTCUSDT": 1.0}, "core active")]
    )
    result = reconcile_portfolio(
        cash=1_000.0,
        positions={},
        target=target,
        market_rules=RULES,
        reference_prices=PRICES,
    )
    ledger = ExecutionLedger(tmp_path / "execution.db")

    cycle_id = ledger.record(result)

    cycle = ledger.recent_cycles(limit=1)[0]
    ticket = ledger.tickets_for_cycle(cycle_id)[0]
    assert cycle["policy_id"] == "professional_spot_v1"
    assert cycle["target_payload"] == {"BTCUSDT": 0.5}
    assert "core active" in ticket["reason"]
