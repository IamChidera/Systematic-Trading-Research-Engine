# Changelog

All notable public-package changes are documented here.

## 0.2.0 - 2026-07-24

### Added

- Typed contracts between independent strategy sleeves and the portfolio.
- Account-level target aggregation with explicit unused-cash treatment.
- Broker-neutral reconciliation from current holdings to target weights.
- Exchange minimum-quantity and quantity-step handling.
- Sell-before-buy execution phases with post-sale reconciliation.
- Account-relative turnover and ticket controls without fixed GBP ceilings.
- Human-readable reasoning on every planned ticket.
- Durable SQLite execution-cycle and ticket ledger.
- Deterministic end-to-end operating-core demo.
- GitHub Actions test and demo workflow.
- Presentation-safe dashboard screenshot automation.
- Public/private product and security boundaries.

### Changed

- Package version increased from `0.1.0` to `0.2.0`.
- Dashboard metrics use readable status labels and responsive metric rows.
- Architecture and operations documentation now describe the executable
  operating core rather than only monitoring concepts.

### Not Included

- Live broker credentials or account state.
- Private strategy parameters and unreviewed research sprints.
- A public live-order submission adapter.
- Any claim of guaranteed or expected investment return.
