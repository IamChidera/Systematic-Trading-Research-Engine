from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PerformanceSummary:
    final_equity: float
    return_pct: float
    cagr_pct: float | None
    sharpe: float | None
    max_drawdown_pct: float
    trades: int
    win_rate_pct: float | None
    profit_factor: float | None


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    drawdown = (peak - equity) / peak
    return float(drawdown.max()) if not drawdown.empty else 0.0


def sharpe_ratio(equity: pd.Series, periods_per_year: int = 365) -> float | None:
    returns = equity.pct_change().dropna()
    if len(returns) < 2 or returns.std() == 0:
        return None
    return float(returns.mean() / returns.std() * math.sqrt(periods_per_year))


def cagr(equity: pd.Series, dates: pd.Series | pd.Index) -> float | None:
    if equity.empty:
        return None
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    if start <= 0 or end <= 0:
        return None
    first = pd.Timestamp(dates[0])
    last = pd.Timestamp(dates[-1])
    years = (last - first).days / 365.25
    if years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def profit_factor(pnls: list[float]) -> float | None:
    gross_profit = sum(value for value in pnls if value > 0)
    gross_loss = abs(sum(value for value in pnls if value <= 0))
    if gross_loss == 0:
        return None if gross_profit == 0 else float("inf")
    return gross_profit / gross_loss


def summarize(equity_curve: pd.DataFrame, trade_pnls: list[float], starting_cash: float) -> PerformanceSummary:
    equity = equity_curve["equity"]
    final_equity = float(equity.iloc[-1])
    winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
    annual_growth = cagr(equity, equity_curve["timestamp"])
    return PerformanceSummary(
        final_equity=round(final_equity, 2),
        return_pct=round((final_equity / starting_cash - 1) * 100, 2),
        cagr_pct=round(annual_growth * 100, 2) if annual_growth is not None else None,
        sharpe=round(sharpe_ratio(equity), 4) if sharpe_ratio(equity) is not None else None,
        max_drawdown_pct=round(max_drawdown(equity) * 100, 2),
        trades=len(trade_pnls),
        win_rate_pct=round(len(winning_trades) / len(trade_pnls) * 100, 2) if trade_pnls else None,
        profit_factor=round(profit_factor(trade_pnls), 4) if profit_factor(trade_pnls) is not None else None,
    )
