# Five-Minute Demo Video Script

## 0:00–0:25 — The problem

**Screen:** README hero and architecture visual.

**Narration:** “Most trading demos jump from an attractive chart to a claim. This system focuses on the missing middle: how an idea is tested, rejected or promoted, combined with other ideas, and monitored under explicit risk controls.”

## 0:25–1:05 — The product

**Screen:** `docs/assets/system_architecture.svg`.

**Narration:** “Historical candles enter a reproducible research layer. Strategies pass through robustness checks, portfolio construction, paper monitoring, execution dry-runs, and readiness gates. Every stage creates inspectable artifacts.”

**Callout:** “Research, paper, and live states remain visibly separate.”

## 1:05–1:50 — Promotion discipline

**Screen:** `docs/assets/strategy_promotion_pipeline.svg`.

**Narration:** “Ideas do not graduate because one backtest looks good. They must survive cost stress, out-of-sample periods, correlation review, paper observation, and operational readiness. Failed candidates enter an archive with a reason and a retest condition.”

## 1:50–2:35 — Research evidence

**Screen:** README result charts: return versus drawdown, annual returns, and fee stress.

**Narration:** “Returns are shown with drawdown, annual consistency, and transaction-cost sensitivity. These are historical research outputs—not forecasts. The purpose is to expose fragility before an idea reaches operations.”

## 2:35–3:45 — Dashboard walkthrough

**Screen:** Operations dashboard, beginning with System Status.

**Narration:** “The operating view answers four questions: Is the system healthy? What is exposed? Why is nothing firing? And what would block promotion? Live account value is shown separately from paper telemetry. The per-bot table records role, state, exposure, trade history, blockers, and an operator verdict.”

**Screen:** Portfolio Lab, then Signal Radar.

**Narration:** “Portfolio targets, sleeve brakes, dry-run tickets, and signal proximity make quiet periods explainable. No order can be a healthy outcome when the rules say wait.”

## 3:45–4:30 — Paper versus live

**Screen:** `docs/live_vs_paper.md` comparison table.

**Narration:** “Before capital is increased, expected paper orders are reconciled with actual live fills. Differences in timing, quantity, fees, slippage, and position state become exceptions with owners and actions.”

## 4:30–5:00 — Close

**Screen:** Evidence pack index.

**Narration:** “The deliverable is not a promise of returns. It is an auditable system for turning trading ideas into monitored, risk-controlled portfolios—complete with promotion gates, rejection history, operating reports, and live-versus-paper reconciliation.”

## Capture checklist

- Record at 1440p or 1080p with browser zoom at 100%.
- Hide API keys, account identifiers, paths, and private logs.
- Use a fixed report snapshot so figures do not change mid-recording.
- Add a visible “Historical research / not financial advice” footer to result shots.
