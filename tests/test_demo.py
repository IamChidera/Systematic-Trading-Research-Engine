from pathlib import Path

import pytest

from trading_research.demo import run_demo
from trading_research.execution_ledger import ExecutionLedger


def test_demo_completes_sell_then_buy_and_hits_target(tmp_path: Path):
    report = run_demo(tmp_path)

    assert report["broker_contacted"] is False
    assert report["orders_submitted"] is False
    assert report["sell_phase"]["execution_phase"] == "sell"
    assert report["buy_phase"]["execution_phase"] == "buy"
    assert report["final_simulated_account"]["asset_weights"]["BTCUSDT"] == pytest.approx(0.60)
    assert report["final_simulated_account"]["asset_weights"]["SOLUSDT"] == pytest.approx(0.15)
    assert report["final_simulated_account"]["cash_weight"] == pytest.approx(0.25)
    assert (tmp_path / "portfolio_demo_report.json").exists()

    ledger = ExecutionLedger(tmp_path / "execution_ledger.db")
    assert len(ledger.recent_cycles()) == 2
