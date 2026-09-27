# Volatility Expansion v1

Status: **FROZEN** before any implementation. Approved 2026-09-27 (draft
`fe4ebfe`, corrected per review: `atr_period` removed, compression rank
defined, drift control's ATR normalisation stated). Any change requires a v2;
the JSON block at the end is machine-checked by test. No code for this
hypothesis existed before this commit.

## Hypothesis

After a period of unusually narrow price range (compression), a close outside
that range tends to be followed by continuation in the breakout direction
(expansion). Entry follows the breakout close, with a stop defined by the
compression range and a target fixed in multiples of initial risk (R). Stand
aside when volatility-shock, spread, data-quality or risk gates fail.

## Disclosure: contamination with a prior observation

The research log (trend-continuation walk-forward) records a post-hoc
observation: trend entries in the lowest-volatility tercile did better than
those in the highest, measured on the same 2023-2026 test windows this
hypothesis will be evaluated on. Compression is a low-volatility condition by
definition, so this hypothesis is **not independent** of that observation, and
its test windows are not fully untouched for volatility-related questions.

Mitigations, fixed now:

- Compression uses a standard, literature-style definition (the box width's
  percentile within its own trailing history), not the tercile construction
  from the log.
- The compression threshold (20th percentile) and the lookback (500 bars) are
  fixed canonical values. **They are not grid parameters** and will not be tuned.
- No volatility-tercile, minimum or maximum volatility filter beyond the
  definition itself, and no session filter.
- The result must also beat the Drift Baseline v1 control (hour-matched random
  timing), which absorbs time-of-day effects.
- The research log entry for this run must restate this disclosure next to
  the verdict.

## Direction handling

Two independent hypotheses, never averaged:

- `vol_expansion_long`: upside breakout from compression -> long.
- `vol_expansion_short`: downside breakout from compression -> short.

Each has its own walk-forward, parameter selection, deployed and forced tracks,
drift-baseline comparison and verdict.

## Definitions (H1 bars, UTC, causal)

1. **Box.** For signal bar j and the grid's `box_bars` N, the box covers bars
   j-N .. j-1 (it excludes the signal bar). Box high = max high, box low = min
   low, width W = box high - box low.
2. **Compression.** The reference set is the widths of the L =
   `compression_lookback_bars` N-bar boxes ending at bars j-2, j-3, .., j-1-L
   (the L boxes immediately before the current one). The box is compressed
   when its **rank** is at most `compression_percentile`:
   #{reference widths strictly smaller than W} / L <= 0.20.
   The reference set must be complete (all L boxes exist); otherwise there is
   no signal.
3. **Breakout.** On bar j, with a compressed box: close[j] > box high gives a
   long signal; close[j] < box low gives a short signal. The signal bar is j.
   There is no other confirmation.
4. **Stop** (grid `stop`):
   - `box_opposite`: long stop = box low; short stop = box high.
   - `box_mid`: stop = (box high + box low) / 2.
5. **Entry.** Market order at the open of bar j+1 (`delay_bars` = 1), filled with
   half spread + slippage against the trade. If the fill is already at or
   beyond the stop, the trade is skipped.
6. **Risk and target.** R = |entry fill - stop|. Target = entry fill +/-
   `target_r` x R.
7. **Exits.** Identical to Liquidity Sweep Reversal v1, using the same bracket
   engine:
   - time stop at `max_hold_bars`, then stop, then target;
   - **stop first** when one bar touches both stop and target;
   - a gap through the stop fills at the open;
   - end of data exits at the last close;
   - every exit pays half spread + slippage.
8. **One position at a time** per hypothesis. Signals while a position is open
   or an entry is pending are ignored.

## Gates (at the signal bar; failing any gate = no trade)

- **Volatility shock:** the same QF-X kill switch and values as the prior
  hypotheses: EWMA vol (half-life 6) greater than 2.5 x EWMA vol (half-life 240).
  Note: large breakout bars can trip it; it is kept unchanged anyway.
- **Cost:** spread (max of per-bar spread and configured floor) must not exceed
  0.25 x the distance from the signal close to the stop.
- **Data quality:** Gate 0 at load (unchanged).

## Explicitly excluded in v1

- Compression threshold and lookback are not in the grid.
- No volatility-regime, session, day-of-week or trend-direction filter.
- No retest or pullback entry; no volume or tick-volume condition.
- No trailing stops or scaling.

## Grid (8 combinations)

| axis | values |
|---|---|
| `box_bars` | 12, 24 |
| `stop` | box_opposite, box_mid |
| `target_r` | 1.0, 2.0 |

## Evaluation and qualification

- Rolling walk-forward, unchanged: 24M train / 6M validation / 6M test, 6M step.
  Deployed and forced tracks, the same stability and qualification rules,
  and the same costs.
- **Drift Baseline v1 applied unchanged** (hour-matched, 500 repetitions,
  forced-track parameters, one-sided randomization test). Its scope already
  covers "every future bracket hypothesis"; the only change is adding the
  two hypothesis names to its `applies_to` list. The method and values are
  unchanged.
- **ATR appears only inside the drift control, never in this hypothesis.**
  The control records each template's stop distance in ATR units and
  rescales it at the random bar. It uses ATR(24) (simple mean of 24 true
  ranges), exactly as in the Drift Baseline v1 run on the sweep hypothesis.
  This is part of the control's fixed procedure, not a parameter of this
  hypothesis, and it does not affect the hypothesis's own signals, stops,
  targets or gates.
- **Qualification:** every walk-forward rule **and** drift-baseline p <= 0.05
  (necessary, not sufficient), evaluated per direction.
- Results in bps and R, per direction; exit-reason breakdown reported.

## Frozen parameters

```json
{
  "name": "volatility_expansion",
  "version": 1,
  "hypotheses": ["vol_expansion_long", "vol_expansion_short"],
  "grid": {
    "box_bars": [12, 24],
    "stop": ["box_opposite", "box_mid"],
    "target_r": [1.0, 2.0]
  },
  "fixed": {
    "compression_percentile": 0.2,
    "compression_lookback_bars": 500,
    "compression_rule": "count(reference_width < width) / lookback <= compression_percentile",
    "max_hold_bars": 48,
    "vol_long_halflife": 240.0,
    "vol_shock_halflife": 6.0,
    "vol_shock_ratio": 2.5,
    "max_spread_to_stop": 0.25,
    "same_bar_stop_target": "stop_first",
    "delay_bars": 1
  },
  "walkforward": "unchanged from liquidity_sweep_reversal_v1",
  "costs": "unchanged from liquidity_sweep_reversal_v1",
  "drift_baseline": {"spec": "drift_baseline_v1", "applies": true, "max_p": 0.05, "control_atr_period": 24}
}
```
