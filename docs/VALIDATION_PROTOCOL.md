# QF-X Validation Protocol

No strategy proceeds toward live execution until the preceding validation gates have passed.

## Gate 0 — Data integrity

Check duplicates, missing fields, impossible OHLC relationships, timezone consistency, stale data, corrupted observations and look-ahead contamination.

## Gate 1 — Deterministic tests

Test normal cases, boundaries, missing inputs, extreme values, invalid inputs and session boundaries.

## Gate 2 — Historical backtest

Include realistic spread, commissions/fees, slippage, execution delay and instrument-specific contract economics.

## Gate 3 — Walk-forward validation

Use chronological train, validation and test periods. Never randomly shuffle time-series observations.

## Gate 4 — Out-of-sample evaluation

Measure expectancy, median trade, profit factor, maximum drawdown, recovery, trade count, exposure, turnover, MAE/MFE, regime performance, session performance and cost sensitivity.

## Gate 5 — Robustness

Stress wider spreads, worse slippage, delayed execution, parameter perturbations, missing observations and materially different market periods.

## Gate 6 — Shadow operation

Generate decisions without placing orders. Compare expected versus hypothetical realized execution and monitor drift and kill conditions.

## Gate 7 — Controlled deployment

Only after the preceding gates have passed may an execution adapter be considered.

No validation result guarantees future profitability.
