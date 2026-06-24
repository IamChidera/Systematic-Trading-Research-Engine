import math

import pandas as pd

from trading_research.metrics import cagr, max_drawdown, profit_factor, sharpe_ratio, summarize


def test_max_drawdown_uses_running_peak():
    equity = pd.Series([100.0, 120.0, 90.0, 110.0])

    assert max_drawdown(equity) == 0.25


def test_profit_factor_handles_losses_and_open_ended_wins():
    assert profit_factor([10.0, -5.0, 15.0]) == 5.0
    assert math.isinf(profit_factor([10.0, 5.0]))
    assert profit_factor([]) is None


def test_cagr_returns_none_for_zero_length_period():
    equity = pd.Series([100.0, 110.0])
    dates = pd.to_datetime(["2024-01-01", "2024-01-01"])

    assert cagr(equity, dates) is None


def test_sharpe_returns_none_for_flat_curve():
    equity = pd.Series([100.0, 100.0, 100.0])

    assert sharpe_ratio(equity) is None


def test_summarize_builds_performance_summary():
    curve = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "equity": [10_000.0, 10_500.0, 10_250.0],
        }
    )

    summary = summarize(curve, [100.0, -50.0], starting_cash=10_000.0)

    assert summary.final_equity == 10_250.0
    assert summary.return_pct == 2.5
    assert summary.trades == 2
    assert summary.win_rate_pct == 50.0
    assert summary.profit_factor == 2.0
