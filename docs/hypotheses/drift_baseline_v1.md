# Drift Baseline v1 (timing-shuffled control)

Status: **DRAFT**, awaiting approval. Nothing below has been implemented or run.
Once approved, the status changes to FROZEN in a commit made before any code,
and the JSON block becomes machine-checked like the sweep specification.

## Purpose

A control, not a tradeable hypothesis. It answers one question per hypothesis:
**does the hypothesis's entry timing add value beyond identical trades placed at
random times?** Random-timed trades with the same direction, bracket geometry,
gates, costs and holding rules earn market drift plus whatever the geometry
itself produces. A hypothesis only shows timing value if it beats that.

## Scope

- Bracket hypotheses: `sweep_reversal_long` and `sweep_reversal_short` (v1,
  evaluated retroactively; their results and verdicts do not change), and every
  future bracket hypothesis.
- Out of scope for v1: trend continuation (signal-exit engine, no stop geometry
  to copy).

## Construction

Evaluated per hypothesis, symbol, walk-forward window and segment (train,
validation, test), using the **forced-track parameters already selected in
that window**. The control never selects parameters of its own.

1. **Template trades.** Collect the hypothesis's orders in the segment after all
   gates: signal bar g, and stop distance in ATR units
   k_g = |close[g] - stop[g]| / ATR[g]. Direction, `target_r` and
   `max_hold_bars` come from the hypothesis and its selected parameters.
2. **Random timing (hour-matched).** For each repetition, each template is
   placed on a random bar of the same segment with the **same UTC hour** as its
   signal bar g, sampled without replacement. This keeps the hypothesis's
   session mix (for example, sweeps clustering at the London open) so session
   effects are not mistaken for timing value.
3. **Geometry.** Stop = close[h] -/+ k_g x ATR[h] at the random bar h (below for
   longs, above for shorts). Everything else is unchanged.
4. **Same gates.** The volatility-shock and cost gates are applied at h. A
   rejected draw is redrawn from the same hour's remaining bars, up to
   `max_redraws` times. After that, the template is dropped and the drop is counted.
5. **Same execution.** Same bracket engine, costs, per-bar spread floor and
   delay. Orders arriving while a position is open are dropped, exactly as for
   the hypothesis. The control's trade count is reported next to the
   hypothesis's.
6. **Determinism.** Repetition r uses a seed derived from
   sha256("hypothesis|symbol|window|segment|r"). Re-running reproduces identical
   results.

## Statistics

For every window and segment, the report shows:

- the hypothesis net bps/trade and its trade count;
- the control's mean, median, 5th and 95th percentile net bps/trade and trade count;
- the hypothesis's excess over the control mean;
- the hypothesis's one-sided p-value: (1 + #{control_r >= hypothesis}) / (N + 1).

Pooled across windows, control repetition r is pooled over all windows (the
same r in each), which gives N pooled control results per segment type. The
hypothesis's pooled result is ranked within them.

## Pre-registered questions and decision rules

- **Q1: drift explanation (train).** If the hypothesis's pooled *train* net lies
  inside the control's 5-95% band, its in-sample result is attributed to drift
  and geometry, not timing. This tests the open question on sweep long-side
  train positivity. Above the 95th percentile means timing had in-sample value.
- **Q2: timing value (test).** Pooled *test* p <= 0.05 means timing adds value
  out of sample. Otherwise: no demonstrated timing value.
- **Q3: drift line.** The control's pooled mean per direction is reported as
  the drift benchmark each future directional result is read against.

## Proposed qualification amendment (for approval, separate decision)

For future hypotheses only, add one rule to walk-forward qualification: the
deployed track's pooled test net must beat its timing-shuffled control at
p <= 0.05. Sweep Reversal v1 is not re-qualified, since it already fails.

## Explicitly excluded in v1

- No parameter selection for the control.
- No matching on volatility regime or day of week (hour-of-day only). This
  limits degrees of freedom; a finer match would need a v2.
- No control for trend continuation.

## Frozen parameters (after approval)

```json
{
  "name": "drift_baseline",
  "version": 1,
  "applies_to": ["sweep_reversal_long", "sweep_reversal_short"],
  "track": "forced",
  "segments": ["train", "validation", "test"],
  "sampling": "hour_matched",
  "repetitions": 500,
  "max_redraws": 20,
  "seed_scheme": "sha256(hypothesis|symbol|window|segment|repetition)",
  "p_value": "(1 + count(control >= hypothesis)) / (repetitions + 1)",
  "band": [0.05, 0.95],
  "timing_value_max_p": 0.05,
  "qualification_amendment": {"proposed": true, "max_p": 0.05}
}
```
