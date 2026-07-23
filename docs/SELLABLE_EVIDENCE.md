# Sellable Evidence Pack

## Product statement

> We built an auditable system for turning trading ideas into monitored, risk-controlled portfolios.

The product is the decision process, not a return promise. Every idea has evidence, gates, an operating state, and a recorded outcome.

## Proof map

| Buyer question | Evidence | What it proves |
| --- | --- | --- |
| How does an idea become deployable? | [Strategy promotion pipeline](assets/strategy_promotion_pipeline.svg) | Advancement is gated, reversible, and evidence-based. |
| What are the system boundaries? | [Architecture diagram](assets/system_architecture.svg) | Research, portfolio, operations, and execution concerns are separated. |
| Can I see it working? | [Dashboard walkthrough](dashboard_walkthrough.md), [System Status](screenshots/system_status.png), and [Kraken Portfolio](screenshots/kraken_portfolio.png) | Operators can inspect health, exposure, blockers, and readiness. |
| What is reviewed every week? | [Weekly report template](weekly_operating_report.md) and [current example](weekly_reports/2026-07-15.md) | Decisions and exceptions are captured on a repeatable cadence. |
| Do failed ideas disappear? | [Failed strategy archive](failed_strategy_archive.md) | Rejections are first-class research output. |
| Is paper behavior reconciled to live behavior? | [Live-vs-paper comparison](live_vs_paper.md) | Execution drift is measured before capital is increased. |
| Can someone understand it quickly? | [Five-minute demo](demo_video_script.md) | The story is concise, visual, and claim-safe. |

## Claim policy

Use these claims:

- auditable research-to-operations workflow;
- explicit promotion and rejection gates;
- portfolio-level risk controls;
- paper/live separation and reconciliation;
- monitored health, exposure, execution assumptions, and exceptions.

Avoid guaranteed or expected returns, proof of live profitability based on backtests, or production-readiness claims without completed gates.

## Evidence standard

Every published metric should include its period, data source, cost assumptions, mode (`backtest`, `paper`, or `live`), and generation timestamp. Empty or failed gates are valid evidence; silence is not.
