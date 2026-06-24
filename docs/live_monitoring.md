# Paper-Live Monitoring

The paper-live layer is designed to test whether the research system behaves correctly outside a historical replay.

It does not prove profitability by itself. Its purpose is to validate operations, state recovery, signal frequency, and execution assumptions before any real capital is considered.

## What It Tracks

- supervisor heartbeat
- latest bot cycle status
- current equity
- open positions
- generated targets
- trade count
- alerts and errors
- stale reports
- connectivity failures
- state recovery after restart

## Current Status

The system is paper-live operational and waiting for qualifying market signals.

That means:

- the monitoring loop can run continuously
- state can be preserved between cycles
- reports can be inspected after each run
- the system has not yet produced enough live paper trades to compare against historical trade behavior

## Why No Trades Can Still Be Healthy

Several strategy families are deliberately selective. A quiet period is expected when:

- trend filters are not active
- assets fail momentum or liquidity thresholds
- drawdown or damage gates block entries
- the portfolio allocator has no valid targets

The objective is not constant activity. The objective is for live behavior to match the research assumptions.

## Promotion Checklist

Before a strategy is considered for real capital, the monitoring process should show:

- fresh reports over multiple days
- no repeated crash or connectivity failure
- no unexplained state reset
- signal frequency within historical range
- live paper trades consistent with backtest logic
- drawdown and allocation behavior within expected limits
- clear logs for every decision to trade or wait

## Research Boundary

The public repository documents the research architecture and monitoring process. Experimental lab scripts, raw market data, credentials, local databases, and messy sprint outputs should remain outside the public repo unless they are cleaned and converted into reusable examples.
