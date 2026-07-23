# Systematic Trading Research Engine

> An auditable system for turning trading ideas into monitored, risk-controlled portfolios.

[![CI](https://github.com/IamChidera/Systematic-Trading-Research-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/IamChidera/Systematic-Trading-Research-Engine/actions/workflows/ci.yml)

A Python research and operations framework for testing systematic crypto strategies, rejecting fragile ideas, constructing portfolios, and monitoring paper/live readiness under explicit controls.

The project demonstrates the engineering process behind an algorithmic trading system: data preparation, backtesting, walk-forward validation, fee stress testing, regime detection, portfolio construction, stateful paper monitoring, execution dry-runs, risk checks, and daily operational review.

It is a research and engineering project, not financial advice or a promise of future returns.

## Start Here

| If you want to… | Open |
| --- | --- |
| Understand the product in two minutes | [Sellable evidence pack](docs/SELLABLE_EVIDENCE.md) |
| See the honest maturity boundary | [Product maturity](docs/PRODUCT_MATURITY.md) |
| Run the operating core end to end | `python -m trading_research.demo` |
| Run a five-minute demonstration | [Demo video script](docs/demo_video_script.md) |
| See how ideas earn promotion | [Strategy promotion pipeline](docs/assets/strategy_promotion_pipeline.svg) |
| Understand system boundaries | [Architecture diagram](docs/assets/system_architecture.svg) |
| Review weekly operations | [Weekly operating report](docs/weekly_operating_report.md) |
| Inspect rejections and paper/live drift | [Failed strategy archive](docs/failed_strategy_archive.md) · [Live-vs-paper comparison](docs/live_vs_paper.md) |

## Dashboard Evidence

![Presentation-safe system status](docs/screenshots/system_status.png)

The dashboard has a presentation-safe mode that masks private filesystem paths and the exact live account value while retaining operational state:

```powershell
$env:TRADING_DASHBOARD_DEMO="1"
streamlit run dashboard\ops_dashboard.py
```

## Highlights

- Multi-asset strategy backtesting
- Regime filters using trend, momentum, drawdown, volume, and breadth
- Position sizing and portfolio allocation
- Fee and slippage stress testing
- Walk-forward and year-by-year validation
- Paper-live state persistence with SQLite
- Crash-tolerant monitoring loop
- Execution-cost dry-run simulation
- Portfolio-level risk snapshots
- Tiny-live readiness checks
- Daily operations journal structure
- Streamlit operations dashboard
- Typed strategy-to-portfolio contracts
- Account-relative target reconciliation
- Explainable sell-before-buy order planning
- Durable SQLite execution-decision ledger
- Automated test and demo workflow in GitHub Actions

## Professional Operating Core

Version `0.2.0` adds a broker-neutral operating core rather than presenting
monitoring documentation as if it were an execution product.

```text
independent sleeve targets
  -> validated account-level portfolio target
  -> current holdings reconciliation
  -> exchange-minimum and cash checks
  -> sell phase
  -> post-sale reconciliation
  -> buy phase
  -> durable decision ledger
```

The execution policy is account-relative. It does not contain a fixed account
value or fixed order-notional ceiling. Every planned ticket records its current
weight, target weight, and strategy explanation.

Run the deterministic local demonstration:

```bash
pip install -e ".[dev]"
python -m trading_research.demo
```

The demo contacts no broker and submits no orders. It writes a two-cycle
sell-then-buy report and SQLite ledger under `outputs/portfolio_demo/`.

The public/private boundary is deliberate:

- Public: contracts, portfolio construction, reconciliation, paper/dry-run
  ledger, tests, dashboard, and reproducible examples.
- Private: API credentials, account state, broker adapters, raw provider
  messages, unreviewed research sprints, and proprietary strategy parameters.

![Presentation-safe promoted portfolio](docs/screenshots/kraken_portfolio.png)

## Results Preview

The framework was used to compare strategy engines and portfolio allocations over a multi-year crypto market sample.

![Portfolio return comparison](docs/assets/portfolio_return_comparison.png)

![Return vs drawdown](docs/assets/return_vs_drawdown.png)

![Annual returns](docs/assets/annual_returns.png)

![Fee stress](docs/assets/fee_stress.png)

## Architecture

![Auditable system architecture](docs/assets/system_architecture.svg)

The repository uses a package-first structure:

```text
src/trading_research/
  indicators.py      market features and technical indicators
  regimes.py         trend, momentum, drawdown, and volume filters
  strategies.py      strategy signal generation
  backtester.py      cash, positions, trades, and equity curves
  portfolio.py       allocation and correlation utilities
  paper_state.py     SQLite paper-state persistence
  ops.py             paper-live execution, risk, and readiness helpers
  contracts.py       typed sleeve and account target contracts
  execution.py       target reconciliation and explainable order planning
  execution_ledger.py durable SQLite decision evidence
  metrics.py         return, CAGR, Sharpe, drawdown, and profit factor
```

More detail is available in [docs/architecture.md](docs/architecture.md).

## Research Pipeline

![Strategy promotion pipeline](docs/assets/strategy_promotion_pipeline.svg)

```text
historical candles
  -> feature engineering
  -> regime detection
  -> strategy simulation
  -> fee and slippage stress
  -> walk-forward validation
  -> portfolio allocation
  -> paper-live monitoring
```

The key principle is to test whether an idea survives outside one attractive backtest period.

## Operational Layer

The project includes a sanitized operations layer for paper-live monitoring:

```text
bot reports
  -> execution dry-run
  -> risk snapshot
  -> readiness check
  -> daily journal
  -> dashboard review
```

This layer is designed to answer practical questions:

- Is the supervisor still running?
- Did any bot generate an order?
- What would the estimated fee, spread, and slippage be?
- Which bots and assets are currently exposed?
- Are any guardrails warning before tiny-live review?
- Is the system waiting healthily or failing silently?
- Which bot and asset are closest to firing, and what blocked them?

More detail is available in [docs/operations.md](docs/operations.md) and [docs/live_monitoring.md](docs/live_monitoring.md).

## Core Ideas

The framework compares several independent strategy families:

| Engine | Idea | Role |
| --- | --- | --- |
| Mean Reversion | Buy severe pullbacks in healthy regimes | Defensive core |
| Relative Strength | Rotate toward stronger assets | Diversification sleeve |
| Trend Pyramid | Add to confirmed winners | Growth sleeve |
| Portfolio Allocator | Combine engines by target weights | Risk management |
| Operations Layer | Monitor paper-live execution and risk | Production discipline |

## Strategy Evaluation

Each strategy is evaluated using:

- total return and CAGR
- maximum drawdown
- Sharpe ratio
- trade count
- win rate
- profit factor
- best and worst trade
- yearly performance
- fee-stress performance
- live/paper signal frequency once monitored

The framework also checks whether strategies are complementary by comparing their return correlations.

## Walk-Forward Validation

The research process separates attractive in-sample behavior from more useful out-of-sample behavior. Strategies are reviewed across individual years and rolling windows to identify whether performance depends on a single market regime.

## Risk Management

Risk controls include:

- regime filters before entry
- position sizing by sleeve
- trailing stops
- drawdown monitoring
- paper-state recovery
- fee and slippage stress testing
- portfolio-level allocation limits
- stale heartbeat detection
- supervisor failure alerts
- readiness checks before any tiny-live review

## Performance Results

Example historical research outputs:

| Portfolio | Return | CAGR | Sharpe | Max Drawdown |
| --- | ---: | ---: | ---: | ---: |
| Benchmark: Bot3 70 / Bot7 30 | 148.05% | 21.48% | 1.46 | 14.47% |
| Growth: Bot3 60 / Bot7 20 / Bot10 20 | 163.16% | 23.03% | 1.38 | 16.96% |
| Growth: Bot3 50 / Bot7 25 / Bot10 25 | 194.40% | 26.03% | 1.38 | 19.14% |
| Growth: Bot3 20 / Bot7 30 / Bot10 50 | 277.37% | 32.91% | 1.30 | 24.78% |

These figures are historical research results and should not be treated as expected future returns.

## Example Research Questions

- Does a strategy survive realistic fees and slippage?
- Does performance hold across different market periods?
- Which assets contribute most to profit and drawdown?
- Are strategy returns correlated or complementary?
- Can regime filters reduce drawdown without removing too much upside?
- Does a simple static allocation beat more complex dynamic allocators?
- Is a quiet paper-live period healthy waiting or silent failure?
- Which signal was closest to becoming actionable?
- Would a generated order still make sense after spread, fee, and slippage assumptions?

## Project Structure

```text
Systematic-Trading-Research-Engine/
  README.md
  requirements.txt
  .gitignore
  src/
    trading_research/
      __init__.py
      indicators.py
      metrics.py
      backtester.py
      regimes.py
      strategies.py
      portfolio.py
      paper_state.py
      ops.py
  scripts/
    run_backtest.py
    run_portfolio_demo.py
    run_regime_scan.py
    run_paper_cycle.py
  dashboard/
    ops_dashboard.py
  docs/
    architecture.md
    methodology.md
    operations.md
    live_monitoring.md
    sample_results.md
    assets/
  tests/
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Expected Data Format

The scripts expect CSV files with these columns:

```text
timestamp,open,high,low,close,volume
```

Timestamps should be parseable by pandas. Files can be daily candles or intraday candles resampled to daily bars.

Example:

```text
data/BTCUSDT.csv
data/SOLUSDT.csv
```

## Run a Backtest

```bash
python scripts/run_backtest.py --data-dir data --symbols BTCUSDT SOLUSDT --start 2021-06-15 --end 2026-06-15
```

## Run a Regime Scan

```bash
python scripts/run_regime_scan.py --data-dir data --symbols BTCUSDT SOLUSDT
```

## Run One Paper Cycle

```bash
python scripts/run_paper_cycle.py --state-file paper_state.db
```

The paper cycle uses SQLite to preserve cash, positions, and events between runs.

## Run The Portfolio Operating Demo

```bash
python -m trading_research.demo
```

This deterministic scenario proves that the operating core:

- aggregates independent sleeve targets,
- preserves unused capital as cash,
- compares desired weights with actual holdings,
- performs risk-reducing sells before buys,
- waits for post-sale reconciliation before spending proceeds,
- respects market minimums and quantity steps,
- explains every ticket, and
- records both cycles in an append-only SQLite ledger.

## Run the Operations Dashboard

```bash
streamlit run dashboard/ops_dashboard.py
```

On Windows PowerShell:

```powershell
streamlit run dashboard\ops_dashboard.py
```

To point the dashboard at a custom paper-live report folder:

```powershell
$env:PAPER_OPS_ROOT="C:\path\to\top5_ops"
streamlit run dashboard\ops_dashboard.py
```

## Run Tests

```bash
python -m pytest
```

## Future Improvements

Planned extensions:

- richer chart generation from saved equity curves
- additional walk-forward reporting
- automated HTML performance reports
- optional broker plugins behind the public execution contract
- stricter tests for execution, risk, and readiness paths
- permission-layer research across BTC, QQQ, credit, and alt-cycle leaders

## Example Output

Typical reports include:

| Metric | Description |
| --- | --- |
| Return | Total strategy return over the test period |
| CAGR | Annualized return |
| Sharpe | Daily-return Sharpe ratio |
| Max Drawdown | Largest peak-to-trough equity decline |
| Trades | Number of completed trades |
| Profit Factor | Gross profit divided by gross loss |
| Win Rate | Percentage of winning trades |
| Paper Ops Ready | Whether the supervisor and guardrails are healthy |
| Dry-Run Tickets | Simulated order tickets before live execution |

## Engineering Notes

The code intentionally separates:

- indicators from strategy logic
- strategy logic from portfolio allocation
- backtesting from paper-state persistence
- execution dry-runs from real exchange adapters
- research scripts from reusable modules
- public architecture from private experimental sprint outputs

This keeps the framework easier to test, review, and extend.

## Disclaimer

This repository is for research and portfolio-engineering demonstration only. It does not place live orders and should not be used as financial advice.

