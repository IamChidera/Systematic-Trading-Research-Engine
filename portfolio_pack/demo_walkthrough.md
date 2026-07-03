# Demo Walkthrough

Use this when showing the project in an interview or screen share.

## 1. Open With The README

Say:

This project is a Python research framework for systematic trading strategy evaluation and paper-live operations monitoring. I built it to show the full workflow from data and backtesting to risk monitoring and dashboard review.

Show:

- project description
- results preview charts
- architecture section
- operational layer section

## 2. Show The Package Structure

Open `src/trading_research`.

Explain:

- indicators prepare features
- regimes define market filters
- strategies generate entries and exits
- backtester tracks cash, positions, trades, and equity
- portfolio handles allocation and correlation analysis
- paper_state persists paper-live state in SQLite
- ops contains operational helpers
- metrics calculates return, drawdown, Sharpe, CAGR, and profit factor

## 3. Show The Dashboard

Run:

```powershell
streamlit run dashboard\ops_dashboard.py
```

Explain:

The dashboard is designed for operations review. It shows supervisor status, bot state, why signals have not fired, open positions, charts, logs, and the signal proximity radar.

## 4. Show The Signal Radar

Open the `Signal Radar` tab.

Explain:

This answers a practical live-monitoring question: if nothing traded, was the system healthy and waiting, or did something silently fail? It ranks closest waiting bots, blockers, stale reports, open gates, and current holding state.

## 5. Show The Tests

Run:

```powershell
python -m pytest
```

Explain:

The public repo includes tests for metrics, operations helpers, and portfolio logic. This is not just a notebook; it is structured as a Python project.

## 6. Close With The Lesson

Say:

The main lesson from the project is that strategy research is only one part of trading systems. Execution assumptions, risk monitoring, state recovery, and operational observability are just as important.
