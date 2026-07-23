# Failed Strategy Archive

Rejected strategies are evidence that the research process can say “no.” Add one row when a candidate fails a gate; do not delete it when a successor is created.

| ID | Candidate | Tested period | Failed gate | Evidence | Failure mode | Decision | Retest condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FSA-001 | Example: unfiltered pullback | YYYY-MM-DD to YYYY-MM-DD | drawdown | run ID / report | losses concentrated in weak regimes | Archived | retest only with pre-registered regime filter |

## Required rejection record

Store the immutable strategy/config version, dataset and test period, cost assumptions, in/out-of-sample results, exact failed threshold, failure type, decision date, reviewer, and a narrow retest condition or “do not retest.”

## Failure taxonomy

| Code | Type | Meaning |
| --- | --- | --- |
| STAT | Statistical | Weak sample size, unstable parameters, or out-of-sample decay. |
| COST | Execution cost | Edge disappears under plausible fees, spread, or slippage. |
| RISK | Risk | Drawdown, concentration, or tail behavior exceeds the limit. |
| CORR | Portfolio | Adds little independent value after correlation analysis. |
| OPS | Operational | Cannot be monitored, recovered, reconciled, or executed safely. |
| DATA | Data quality | Result depends on missing, stale, leaked, or non-reproducible data. |

An archive entry is not a post-hoc story. The failed gate must point to a reproducible report or run ID.
