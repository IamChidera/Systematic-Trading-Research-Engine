# Demo Walkthrough

This demo shows how the Systematic Trading Research Engine moves from research to paper-live operations and tiny-live readiness.

The project is designed to demonstrate engineering discipline, not a promise of trading profit.

## Demo Goal

Show a complete systematic-trading workflow:

```text
Research idea
  -> backtest
  -> robustness checks
  -> portfolio comparison
  -> paper-live monitoring
  -> execution dry-run
  -> risk review
  -> tiny-live readiness
```

## What To Show First

Open the repository README and start with the Results Preview:

- Portfolio return comparison
- Return versus drawdown
- Annual returns
- Fee stress testing

These charts communicate the key point quickly: the framework does not only report returns; it checks robustness.

## 1. Research Layer

Explain the research process:

- Load historical market data.
- Generate strategy signals.
- Simulate cash, positions, trades, and equity.
- Compare engines by return, Sharpe, drawdown, and profit factor.
- Stress test fees and slippage.
- Review year-by-year and walk-forward performance.

Useful files:

```text
src/trading_research/backtester.py
src/trading_research/strategies.py
src/trading_research/metrics.py
docs/methodology.md
docs/sample_results.md
```

Suggested talking point:

```text
The framework is built to reject attractive but fragile backtests before they reach paper-live monitoring.
```

## 2. Portfolio Layer

Show that strategies are treated as portfolio components rather than isolated magic signals.

Key ideas:

- A defensive core can be combined with growth sleeves.
- Allocation matters as much as entry logic.
- Return, drawdown, and correlation are reviewed together.

Useful files:

```text
src/trading_research/portfolio.py
docs/architecture.md
docs/assets/portfolio_return_comparison.png
docs/assets/return_vs_drawdown.png
```

Suggested talking point:

```text
The system is designed to compare independent return sources and avoid treating every bot as a separate bet when they may share the same market risk.
```

## 3. Paper-Live Operations

Show the operational layer:

- Supervisor heartbeat
- Bot reports
- Execution dry-runs
- Risk snapshots
- Daily journal
- Dashboard

Useful files:

```text
dashboard/ops_dashboard.py
docs/operations.md
docs/live_monitoring.md
```

To run the dashboard:

```powershell
$env:PAPER_OPS_ROOT="C:\path\to\top5_ops"
streamlit run dashboard\ops_dashboard.py
```

Suggested talking point:

```text
The paper-live layer answers whether the system is waiting healthily or failing silently.
```

## 4. Risk And Readiness Layer

Show how the system checks operational readiness before any tiny-live test.

The readiness workflow checks:

- supervisor freshness,
- failed components,
- dry-run order conversion,
- risk warnings,
- API environment variable presence,
- manual exchange confirmations.

Suggested talking point:

```text
Tiny-live readiness is treated as an operational gate. Strategy performance alone is not enough.
```

## 5. External Signal Auditor

Optional extended demo: Bot40-style signal-provider auditing.

The idea:

- Collect Telegram signal messages.
- Parse entry, target, stop, side, and leverage.
- Evaluate whether target or stop was hit first.
- Rank providers by complete signals, win rate, profit factor, average R, and time-to-target.

Suggested talking point:

```text
Instead of blindly copying signal channels, the system measures whether providers have evidence of positive expectancy.
```

## Demo Script

Use this order for a five-minute demo:

1. Show README charts.
2. Explain the research pipeline.
3. Show strategy and portfolio evaluation metrics.
4. Open the operations dashboard.
5. Show paper-live health, open positions, risk snapshot, and journal.
6. Explain tiny-live readiness checks.
7. Close with how the system can be extended with new strategies or signal providers.

## What This Demonstrates

The project demonstrates:

- Python engineering
- pandas-based research workflows
- stateful paper trading
- SQLite persistence
- portfolio analytics
- risk monitoring
- operational dashboards
- software separation between research, paper execution, and live readiness

## What This Demo Does Not Claim

This demo does not claim:

- guaranteed profit,
- future performance,
- live trading suitability for all users,
- financial advice.

The value of the project is the disciplined process: generate ideas, test them, reject weak ones, monitor paper behavior, and only then consider tiny-live execution.
