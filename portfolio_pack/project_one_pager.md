# Project One-Pager

## Systematic Trading Research Engine

A Python research and operations platform for testing systematic crypto trading strategies across multiple assets, market regimes, portfolio allocations, and paper-live monitoring workflows.

## What It Demonstrates

- Python software engineering
- Data pipeline design
- Quantitative research workflow
- Backtesting and performance analytics
- Walk-forward validation
- Fee and slippage stress testing
- Portfolio construction
- SQLite-backed paper-state persistence
- Streamlit dashboard design
- Risk, readiness, and operations monitoring

## Why It Matters

Most student trading projects stop at a single backtest. This project goes further by asking whether strategies survive realistic evaluation:

- different market years
- rolling windows
- fee stress
- portfolio drawdowns
- stale report detection
- paper-live state recovery
- execution dry-run checks
- healthy-waiting versus silent-failure analysis

## Key Engineering Features

- Modular package structure under `src/trading_research`
- Reusable metrics, portfolio, regime, and paper-state modules
- Streamlit operations dashboard
- Signal proximity radar showing closest waiting setup and blocked condition
- Daily operations journal generated from bot, execution, and risk reports
- Crash-tolerant supervisor loop for paper-live monitoring
- Tests for metrics, portfolio logic, and operations helpers

## Example Historical Research Results

| Portfolio | Return | CAGR | Sharpe | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| Benchmark: Bot3 70 / Bot7 30 | 148.05% | 21.48% | 1.46 | 14.47% |
| Growth: Bot3 60 / Bot7 20 / Bot10 20 | 163.16% | 23.03% | 1.38 | 16.96% |
| Growth: Bot3 50 / Bot7 25 / Bot10 25 | 194.40% | 26.03% | 1.38 | 19.14% |
| Growth: Bot3 20 / Bot7 30 / Bot10 50 | 277.37% | 32.91% | 1.30 | 24.78% |

These are historical research outputs, not expected future returns.

## Current Operational Capability

The system can run paper-live monitoring cycles, preserve state, simulate execution costs, aggregate portfolio exposure, generate daily journals, and show operational health in a dashboard.

## Repository

https://github.com/IamChidera/Systematic-Trading-Research-Engine
