# Methodology

The research workflow follows a conservative validation process.

## 1. Strategy Hypothesis

Each strategy starts with a specific market hypothesis, for example:

- strong assets tend to continue leading during healthy regimes
- severe pullbacks may revert in long-term uptrends
- trend winners can justify adding capital after confirmation

## 2. Backtest

Each strategy is tested over multiple years of historical data with fees included.

## 3. Stress Testing

The framework supports fee stress and variant testing to identify fragile results.

## 4. Split Periods

Results are reviewed year by year and across rolling windows. This helps identify whether performance depends on one unusually strong market period.

## 5. Portfolio Construction

Strategies are combined only after checking whether they behave differently. Correlation between return streams is treated as a first-class metric.

## 6. Paper-Live Monitoring

Paper-live monitoring is used to test operational behavior:

- state recovery
- stale data
- no-trade conditions
- unexpected orders
- reporting consistency

The goal is not to prove profitability in a short period. The goal is to verify that the system behaves as designed.
