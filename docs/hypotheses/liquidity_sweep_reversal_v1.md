# Liquidity Sweep Reversal v1 (frozen specification)

Status: **FROZEN** before any implementation or result exists. Approved 2026-09-27.
Any change to a rule or value below requires a new version (v2) with its own
walk-forward run; v1 results stay on record. The JSON block at the end is the
machine-checked copy: a test fails if the code differs from it.

## Hypothesis

After price takes out a prior confirmed swing high or low and closes back inside
it, price tends to reverse. Enter only after the grid's confirmation rule is met,
with a volatility-aware stop beyond the sweep extreme and a target fixed in
multiples of initial risk (R). Stand aside when volatility, spread, data quality
or risk gates fail.

## Direction handling

Two independent hypotheses, never averaged:

- `sweep_reversal_short`: buy-side liquidity sweep (above a swing high) -> short.
- `sweep_reversal_long`: sell-side liquidity sweep (below a swing low) -> long.

Each has its own walk-forward, parameter selection, deployed and forced tracks,
and verdict.

## Definitions (H1 bars, UTC, causal)

1. **Levels.** Swing highs/lows from `qfx.structure.find_swings` with the grid's
   `swing_lookback` k. A swing at bar s is confirmed at bar s + k and can be
   swept from bar s + k + 1 onward.
2. **Level lifetime.** A level is removed when it is swept, when a bar closes
   beyond it (breakout, not a sweep), or when it is older than
   `level_max_age_bars` bars (measured from the swing bar).
3. **Sweep.** On bar i, a buy-side sweep occurs when high[i] > level and
   close[i] < level for at least one active swing-high level; sell-side is the
   mirror (low[i] < level, close[i] > level). Every level swept on bar i is
   removed. The sweep extreme is high[i] (buy-side) or low[i] (sell-side).
4. **Confirmation** (grid):
   - `none`: the sweep bar i is the signal bar.
   - `structure`: the signal bar is the first bar j in i+1 .. i+`confirmation_window_bars`
     that closes beyond the sweep bar's opposite extreme (short: close[j] < low[i];
     long: close[j] > high[i]). The setup is cancelled if, before that, any bar
     trades beyond the sweep extreme, or if no bar confirms within the window.
     Only one pending setup per hypothesis; a newer sweep replaces a pending one.
5. **Stop.** Sweep extreme +/- `stop_atr_mult` x ATR(`atr_period`) measured at the
   signal bar (short: above the sweep high; long: below the sweep low). ATR is the
   simple mean of true range over the last `atr_period` bars ending at the signal bar.
6. **Entry.** Market order at the open of the bar after the signal bar
   (`delay_bars` = 1), filled with half spread + slippage against the trade.
   If the fill is already at or beyond the stop, the trade is skipped.
7. **Risk and target.** R = |entry fill - stop|. Target = entry fill +/- `target_r` x R.
8. **Exits**, checked on every bar from the entry bar onward, in this order:
   1. Stop: triggered when the bar's range reaches the stop. Fill at the stop, or
      at the open if the bar opens beyond the stop.
   2. Target: triggered when the bar's range reaches the target. Fill at the target.
   3. **Stop and target touched in the same bar: the stop is taken (stop first).**
   4. Time stop: exit at the open of the bar `max_hold_bars` bars after entry.
   5. End of data: exit at the last close.

   Every exit pays half spread + slippage against the trade.
9. **One position at a time** per hypothesis. Setups that complete while a
   position is open or an entry is pending are ignored.

## Gates (evaluated at the signal bar; failing any gate = no trade)

- **Volatility shock:** EWMA vol (half-life `vol_shock_halflife`) greater than
  `vol_shock_ratio` x EWMA vol (half-life `vol_long_halflife`) of H1 log returns.
  Same values as the trend-continuation hypothesis; this QF-X kill switch
  predates the high-volatility observation in the research log.
- **Cost:** the signal bar's spread (the larger of per-bar MT5 spread and the
  configured spread floor) must not exceed `max_spread_to_stop` x the distance
  from the signal bar's close to the stop.
- **Data quality:** Gate 0 at load (unchanged).

## Explicitly excluded in v1

- No volatility-tercile (minimum or maximum volatility) filter.
- No session restriction.
- No separate equal-high/low weighting (equal levels are already swing levels).
- No opposing-liquidity targets.

## Evaluation

Unchanged rolling walk-forward (24M train / 6M validation / 6M test, 6M step),
deployed and forced tracks, the same qualification and stability rules, and the
same cost assumptions as the trend-continuation run. Results are reported per
direction, in bps and in R.

## Frozen parameters

```json
{
  "name": "liquidity_sweep_reversal",
  "version": 1,
  "hypotheses": ["sweep_reversal_long", "sweep_reversal_short"],
  "grid": {
    "swing_lookback": [3, 5],
    "confirmation": ["none", "structure"],
    "target_r": [1.0, 2.0]
  },
  "fixed": {
    "level_max_age_bars": 120,
    "confirmation_window_bars": 6,
    "atr_period": 24,
    "stop_atr_mult": 0.5,
    "max_hold_bars": 48,
    "vol_long_halflife": 240.0,
    "vol_shock_halflife": 6.0,
    "vol_shock_ratio": 2.5,
    "max_spread_to_stop": 0.25,
    "same_bar_stop_target": "stop_first",
    "delay_bars": 1
  },
  "walkforward": {
    "train_months": 24,
    "validation_months": 6,
    "test_months": 6,
    "step_months": 6,
    "min_train_trades": 30,
    "min_validation_trades": 5,
    "min_test_trades": 30,
    "min_test_t": 2.0,
    "min_profitable_windows": 0.6,
    "min_stress_survival": 0.6,
    "max_window_concentration": 0.5,
    "stress_multiplier": 2.0
  },
  "costs": {
    "EURUSD": {"spread": 0.0001, "slippage": 0.00002, "commission": 0.0},
    "XAUUSD": {"spread": 0.25, "slippage": 0.05, "commission": 0.0},
    "BTCUSD": {"spread": 30.0, "slippage": 5.0, "commission": 0.0}
  }
}
```
