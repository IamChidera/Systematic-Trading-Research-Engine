# Live-vs-Paper Reconciliation

The comparison is an execution-control document, not a performance contest. It asks whether the live account behaved like the approved paper decision after real-world constraints.

## Weekly comparison

| Dimension | Paper expectation | Live observation | Difference | Tolerance | Verdict |
| --- | --- | --- | ---: | ---: | --- |
| Decision timestamp | — | — | — seconds | configured window | — |
| Side and symbol | — | — | exact match | exact | — |
| Requested quantity | — | — | —% | configured | — |
| Filled quantity | — | — | —% | configured | — |
| Reference price | — | — | — bps | configured | — |
| Fees | model assumption | actual | — bps | configured | — |
| Slippage | model assumption | actual | — bps | configured | — |
| Final position | expected units | reconciled units | — | configured | — |
| Risk state | expected flags | actual flags | exact match | exact | — |

## Exception record

| ID | Order / cycle | Severity | Mismatch | Likely cause | Capital impact | Action | Owner | State |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| — | — | — | — | — | — | — | — | Open / Closed |

## Promotion rule

Do not increase live capital while a material reconciliation exception is open. Promotion requires matching decision intent, reconciled positions, observed costs inside the approved stress envelope, no unresolved safety incident, and explicit operator approval.
