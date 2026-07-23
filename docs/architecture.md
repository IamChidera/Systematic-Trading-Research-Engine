# Architecture

The project is split into reusable modules and small command-line scripts.

## Modules

| Module | Responsibility |
| --- | --- |
| `indicators.py` | Technical indicators and derived market features |
| `regimes.py` | Market-state filters such as trend, momentum, drawdown, and volume |
| `strategies.py` | Strategy signal generation |
| `backtester.py` | Cash, positions, trade execution, and equity tracking |
| `portfolio.py` | Equity-curve blending, correlations, and allocation utilities |
| `contracts.py` | Typed strategy-sleeve and account-target contracts |
| `execution.py` | Account-relative target reconciliation and order planning |
| `execution_ledger.py` | Durable SQLite decision and ticket evidence |
| `paper_state.py` | SQLite persistence for paper-live monitoring |
| `metrics.py` | Return, CAGR, Sharpe, drawdown, win rate, and profit factor |

## Data Flow

```text
CSV candles
  -> indicator preparation
  -> regime detection
  -> strategy signal
  -> backtest execution
  -> equity curve
  -> portfolio analytics
```

## Operating Core

```mermaid
flowchart LR
    A["Independent Sleeve Targets"] --> B["Portfolio Target"]
    B --> C["Holdings Reconciliation"]
    C --> D{"Sells Required?"}
    D -- Yes --> E["Sell Tickets"]
    E --> F["Broker-State Refresh"]
    F --> C
    D -- No --> G["Buy Tickets"]
    C --> H["Execution Ledger"]
    E --> H
    G --> H
```

The operating core uses target differences rather than fixed cash tiers. It
keeps strategy logic separate from broker mechanics and records why each ticket
exists. Broker-specific authentication and order submission are plugin
boundaries and are intentionally excluded from the public package.

## Paper Monitoring

The paper-state layer is intentionally simple:

```text
load state
evaluate signal
update cash and positions
write state
log event
```

This makes each cycle restartable. If a scheduled process stops, the next run can restore the previous state from SQLite.

## Operations Flow

```mermaid
flowchart LR
    A["Paper Bot Reports"] --> B["Execution Dry-Run"]
    A --> C["Risk Snapshot"]
    B --> D["Readiness Check"]
    C --> D
    D --> E["Daily Journal"]
    E --> F["Dashboard"]
```

The monitoring layer remains report-driven. The operating core additionally
turns typed portfolio targets into broker-neutral planned tickets, while the
public package still never signs or submits a real order.
