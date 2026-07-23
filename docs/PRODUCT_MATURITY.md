# Product Maturity

## Current Position

This repository is a working research and portfolio operating core. It is more
than a collection of notebooks, but it is not presented as a turnkey retail
trading robot.

## What Is Reproducible Publicly

- indicator, regime, strategy, backtest, metric, and portfolio utilities
- typed contracts for independent strategy sleeves
- account-level portfolio target construction
- current-holdings versus target reconciliation
- exchange minimum and quantity-step handling
- sell-before-buy execution planning
- dry-run execution assumptions and risk snapshots
- SQLite paper-state and execution-decision ledgers
- deterministic end-to-end portfolio demo
- Streamlit operations dashboard
- automated tests and GitHub Actions CI

## What Exists Privately

- live and paper supervisor processes
- broker-specific adapters and credential handling
- promoted-strategy parameter locks
- research factories and rejected-candidate archives
- raw broker, market, and signal-provider data
- live account reconciliation and operational state

Those components are excluded to protect credentials, personal account data,
provider content, and potentially commercial strategy IP.

## What Is Not Yet Claimed

- unattended multi-broker commercial deployment
- audited institutional controls
- independent verification of historical performance
- guaranteed profitability
- suitability for another person's capital or risk tolerance

## Commercial Direction

The intended architecture is open core plus private plugins:

```text
public research and portfolio contracts
  + private strategy plugins
  + private broker adapters
  + hosted monitoring and evidence
  = configurable commercial operating product
```

The next product threshold is not another backtest. It is a clean plugin SDK,
configuration schema, broker conformance tests, versioned releases, and several
months of uninterrupted paper/dry-run/live evidence.
