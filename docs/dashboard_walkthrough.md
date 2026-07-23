# Dashboard Walkthrough

For public captures, start the dashboard with `TRADING_DASHBOARD_DEMO=1`. This masks private paths and the exact live account value while preserving operating state.

## Start here: System Status

Use this page to answer whether the stack is healthy before discussing performance.

1. Confirm heartbeat age, restart history, failed components, and warnings.
2. Keep **Kraken Live Value** separate from **Paper Stack** value.
3. Read the per-bot operating table from left to right: role, mode, state, exposure, observed orders, blocker, verdict.
4. Treat “no order” as explainable only when the radar and health reports are fresh.

## Portfolio Lab

Show sleeve targets, expanded asset previews, drawdown brakes, observation maturity, dry-run tickets, and reconciliation warnings.

## Signal Radar and Activation Audit

Use these views to explain inactivity and research discipline. Proximity is an operational explanation, not a recommendation. Activation experiments remain paper-only until their gates are passed.

## Charts, history, and logs

Use charts for trend and comparison; use reports and logs for causality. Do not use a screenshot of a green chart as the sole evidence for a decision.

## Presenter close

“This dashboard is where research claims meet operating evidence. It exposes health, state, risk, blockers, and readiness without mixing backtest, paper, and live results.”
