# Interview Talking Points

## 30-Second Overview

I built a Python research and operations framework for systematic trading strategies. It includes multi-asset backtesting, metrics, portfolio allocation, walk-forward validation, fee stress testing, paper-state persistence, execution dry-runs, risk monitoring, daily journal generation, and a Streamlit dashboard. The main point was to treat trading strategy research like an engineering problem, not just a charting exercise.

## Problem I Was Solving

A single backtest can be misleading. I wanted to build a workflow that asks stronger questions:

- Does the strategy survive fees and slippage?
- Does it work across different years and regimes?
- Does a portfolio of strategies reduce drawdown?
- Can the system recover state between cycles?
- Can I tell the difference between healthy waiting and silent failure?

## Architecture Decision

I separated the system into reusable modules:

- indicators and regimes
- strategy logic
- backtesting and portfolio analytics
- metrics
- paper-state persistence
- operations helpers
- dashboard and reports

This made it easier to test individual pieces and keep the research layer separate from the operations layer.

## Most Interesting Feature

The signal proximity radar is one of the most useful operational features. If no trade fires, it ranks which bot and asset were closest, what gate was open or closed, and whether any reports are stale. That helps prevent false confidence during quiet periods.

## Testing And Validation

The repo includes pytest coverage for metrics, portfolio logic, and operations helpers. Research results are reviewed using returns, CAGR, Sharpe, drawdown, fee stress, walk-forward testing, yearly breakdowns, and portfolio comparison.

## Tradeoffs

The project intentionally does not place live orders. That keeps the public version safer and makes the project suitable as a research and engineering portfolio artifact. A live adapter would require stronger exchange-specific testing, credential management, order reconciliation, and risk controls.

## What I Would Improve Next

- More automated report generation
- More dashboard charts from saved equity curves
- Cleaner plugin-style strategy registration
- Stronger data validation for candle inputs
- Optional exchange adapter interface with strict paper/live separation
- CI checks for dashboard and report generation
