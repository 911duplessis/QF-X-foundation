# Drift Baseline v1 (timing-shuffled control)

Status: **FROZEN** before implementation. Approved 2026-09-27 (draft commit
`cae9793`, refined per review). Any change requires a v2; the JSON block at the
end is machine-checked by test. **The sweep hypothesis parameters must not be
changed on the basis of this control**: it tests the already-defined
hypothesis and is not an optimization loop.

## Purpose

A control, not a tradeable hypothesis. It answers one question per hypothesis:
**does the hypothesis's entry timing add value beyond identical trades placed at
random times?** Random-timed trades with the same direction, bracket geometry,
gates, costs and holding rules earn market drift plus whatever the geometry
itself produces. A hypothesis only shows timing value if it beats that.

## Scope

Extension record: on 2026-09-27 `vol_expansion_long` and `vol_expansion_short`
were added to `applies_to` (approved as an extension, not a new version). The
method, parameters and p-value rule are unchanged. For every hypothesis, ATR
units use ATR(24), the simple mean of the last 24 true ranges.

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

## Statistical test (fixed before execution)

A **one-sided empirical randomization test**, evaluated separately for long and
short, never combined.

- **Test statistic T:** mean net bps per trade. T_obs is computed on the
  hypothesis's actual trades; T_r on control repetition r (r = 1..N).
- **Primary effect size:** T_obs - mean(T_r), the difference in mean net
  bps/trade between the actual trades and the matched random-time control.
- **p-value:** (1 + #{r : T_r >= T_obs}) / (N + 1). The alternative is that
  the hypothesis's timing is better than random timing.
- **Secondary statistic:** total net P&L in bps (sum over trades), with its
  own p-value by the same formula, because mean bps/trade can hide
  differences in trade count.
- A repetition with zero trades has T_r = 0 and total 0; the count of such
  repetitions is reported.

Reported for every window and segment, and pooled:

- observed hypothesis mean (T_obs), trade count and total P&L;
- random-control mean (mean of T_r) and mean trade count;
- the difference T_obs - mean(T_r);
- the empirical p-value (primary and secondary);
- the 5th, 50th and 95th percentiles of T_r;
- the percentile of T_obs within the null distribution (share of T_r < T_obs);
- templates dropped after `max_redraws`.

**Pooling:** control repetition r is pooled over all windows (the same r in
each), which gives N pooled values of T per segment type. T_obs pooled is
the mean over all of the hypothesis's trades in that segment type.

## Pre-registered questions and decision rules

- **Q1: drift explanation (train).** If pooled *train* T_obs lies inside the
  control's 5th-95th percentile band, the in-sample result is attributed to
  drift and geometry, not timing. This tests the open question on sweep
  long-side train positivity. Above the 95th percentile means timing had
  in-sample value; below the 5th means timing was worse than random.
- **Q2: timing value (test).** Pooled *test* p <= 0.05 (primary statistic)
  means a demonstrated timing edge out of sample. Otherwise: no demonstrated
  timing edge.
- **Q3: drift line.** The control's pooled mean per direction is reported as
  the drift benchmark each future directional result is read against.

## Qualification amendment (approved)

For future hypotheses:

> **A hypothesis must demonstrate statistically significant improvement over
> its matched drift baseline at p <= 0.05 before its timing edge can be
> considered demonstrated.**

p <= 0.05 is **necessary, not sufficient**. All existing walk-forward
qualification rules remain mandatory, so a tiny but statistically significant
effect cannot pass with poor economic significance or instability. Sweep
Reversal v1 is not re-qualified, since it already fails.

## Explicitly excluded in v1

- No parameter selection for the control.
- No matching on volatility regime or day of week (hour-of-day only). This
  limits degrees of freedom; a finer match would need a v2.
- No control for trend continuation.

## Frozen parameters

```json
{
  "name": "drift_baseline",
  "version": 1,
  "applies_to": ["sweep_reversal_long", "sweep_reversal_short", "vol_expansion_long", "vol_expansion_short"],
  "track": "forced",
  "segments": ["train", "validation", "test"],
  "sampling": "hour_matched",
  "repetitions": 500,
  "max_redraws": 20,
  "seed_scheme": "sha256(hypothesis|symbol|window|segment|repetition)",
  "test": "one_sided_empirical_randomization",
  "statistic": "mean_net_bps_per_trade",
  "effect_size": "observed_mean_minus_control_mean",
  "secondary_statistic": "total_net_bps",
  "p_value": "(1 + count(control >= observed)) / (repetitions + 1)",
  "zero_trade_repetition_value": 0.0,
  "percentiles": [0.05, 0.5, 0.95],
  "band": [0.05, 0.95],
  "timing_value_max_p": 0.05,
  "directions_separate": true,
  "qualification_amendment": {"approved": true, "max_p": 0.05, "walkforward_rules_remain_mandatory": true}
}
```
