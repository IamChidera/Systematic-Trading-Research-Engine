"""Deterministic end-to-end demonstration of the portfolio operating core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import SleeveTarget, combine_sleeve_targets
from .execution import MarketRule, Position, reconcile_portfolio
from .execution_ledger import ExecutionLedger


def run_demo(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = ExecutionLedger(output_dir / "execution_ledger.db")
    prices = {"BTCUSDT": 50_000.0, "SOLUSDT": 100.0}
    rules = {
        "BTCUSDT": MarketRule(min_quantity=0.0001, quantity_step=0.00000001),
        "SOLUSDT": MarketRule(min_quantity=0.01, quantity_step=0.001),
    }
    target = combine_sleeve_targets(
        [
            SleeveTarget("defensive_core", 0.60, {"BTCUSDT": 1.0}, "core regime remains valid"),
            SleeveTarget("growth_sleeve", 0.30, {"SOLUSDT": 0.50}, "SOL is the eligible liquid leader"),
        ]
    )

    cash = 2_500.0
    positions = {"BTCUSDT": Position("BTCUSDT", 0.15, prices["BTCUSDT"])}
    sell_result = reconcile_portfolio(
        cash=cash,
        positions=positions,
        target=target,
        market_rules=rules,
        reference_prices=prices,
    )
    sell_cycle_id = ledger.record(sell_result)

    for ticket in sell_result.executable_tickets:
        if ticket.side != "sell":
            continue
        position = positions[ticket.symbol]
        positions[ticket.symbol] = Position(
            ticket.symbol,
            position.quantity - ticket.quantity,
            position.price,
        )
        cash += ticket.notional

    buy_result = reconcile_portfolio(
        cash=cash,
        positions=positions,
        target=target,
        market_rules=rules,
        reference_prices=prices,
    )
    buy_cycle_id = ledger.record(buy_result)

    for ticket in buy_result.executable_tickets:
        if ticket.side != "buy":
            continue
        prior = positions.get(ticket.symbol, Position(ticket.symbol, 0.0, ticket.reference_price))
        positions[ticket.symbol] = Position(
            ticket.symbol,
            prior.quantity + ticket.quantity,
            ticket.reference_price,
        )
        cash -= ticket.notional

    final_equity = cash + sum(position.notional for position in positions.values())
    final_weights = {
        symbol: position.notional / final_equity
        for symbol, position in positions.items()
        if position.notional > 0
    }
    report = {
        "status": "demo_complete",
        "mode": "deterministic_local_only",
        "broker_contacted": False,
        "orders_submitted": False,
        "portfolio_target": {
            "asset_weights": dict(target.asset_weights),
            "cash_weight": target.cash_weight,
            "weight_sum": target.weight_sum,
            "sleeve_contributions": {
                sleeve: dict(contribution)
                for sleeve, contribution in target.sleeve_contributions.items()
            },
        },
        "sell_phase": sell_result.as_dict(),
        "buy_phase": buy_result.as_dict(),
        "ledger_cycle_ids": [sell_cycle_id, buy_cycle_id],
        "final_simulated_account": {
            "cash": cash,
            "equity": final_equity,
            "asset_weights": final_weights,
            "cash_weight": cash / final_equity,
        },
    }
    report_path = output_dir / "portfolio_demo_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local portfolio operating-core demo.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "portfolio_demo")
    args = parser.parse_args()
    report = run_demo(args.output_dir)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
