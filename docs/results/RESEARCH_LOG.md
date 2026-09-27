# QF-X Research Log

Interpretation of generated results. Files in this directory ending in `.md`/`.json`
next to an experiment are generated and must not be hand-edited; conclusions live here.

Research sequence: rolling walk-forward (done) -> trend continuation (no demonstrated edge) -> liquidity sweep/reversal (no demonstrated edge)
-> volatility expansion -> regime-conditional combinations -> meta-engine
-> portfolio/correlation -> shadow trading. No execution layer before shadow trading passes.

Language rule: results say "no demonstrated edge", never "does not work".

## 2026-09 - Walk-forward: Liquidity Sweep Reversal v1 (H1)

Specification frozen before implementation: [liquidity_sweep_reversal_v1.md](../hypotheses/liquidity_sweep_reversal_v1.md) (commit `604f63a`); code committed before the first run.
Reports: [long](walkforward_sweep_reversal_long.md) ([json](walkforward_sweep_reversal_long.json)) · [short](walkforward_sweep_reversal_short.md) ([json](walkforward_sweep_reversal_short.json))

**Verdict: no demonstrated edge in either direction on any instrument, deployed or forced.** Directions reported separately, as specified.

| direction | symbol | forced: profitable windows | forced test trades | net bps/trade | t | avg R | upper bound (mean + 2 SE, bps) | deployed |
|---|---|---|---|---|---|---|---|---|
| long (sell-side sweep) | BTCUSD | 2/6 | 285 | -13.9 | -1.27 | -0.14 | +8.0 | traded 3/6 windows, 171 trades, -23.2 bps |
| long (sell-side sweep) | EURUSD | 3/7 | 329 | -1.6 | -1.21 | -0.10 | +1.0 | traded 5/7 windows, 226 trades, -2.2 bps |
| long (sell-side sweep) | XAUUSD | 2/7 | 255 | -0.2 | -0.03 | +0.06 | +11.3 | traded 3/7 windows, 82 trades, -13.0 bps |
| short (buy-side sweep) | BTCUSD | 3/6 | 498 | -1.7 | -0.30 | -0.08 | +9.9 | abstained in all 6 |
| short (buy-side sweep) | EURUSD | 0/7 | 482 | -1.9 | -1.70 | -0.14 | +0.3 | abstained in all 7 |
| short (buy-side sweep) | XAUUSD | 2/7 | 450 | -3.1 | -1.41 | -0.10 | +1.3 | abstained in all 7 |

- **Sample size problem largely solved for this hypothesis.** 255-498 forced out-of-sample trades per instrument and direction (2.5-5x the trend run) make the result informative: on EURUSD any edge in either direction is bounded at about +1 bps per trade, below its ~1.3 bps round-trip cost. On XAUUSD shorts the bound is +1.3 bps. BTC and XAU longs remain wide (+8 to +11 bps) because per-trade dispersion is larger.
- **Mechanics verified on real trades.** Stop exits average -1.03 to -1.05 R (1 R plus costs), 2R targets +1.95 to +1.97 R; the worst trade (-4.2 R, XAUUSD) is a gap through the stop filled at the open, as specified. The cost gate removed ~42% of BTC setups (2021-22 spread era) and <3% elsewhere.
- **Direction asymmetry is in-sample only.** Short candidates almost never pass the train screen (deployed abstains everywhere); long candidates pass with small margins (+0.4 to +10 bps) and then fail out of sample. The likely explanation is market drift, not sweep structure: gold and BTC rose strongly over 2020-2026, so any long-only rule earns drift in train. Not tested; see next step.
- **The deployed track behaved correctly.** Every window where it traded shorts would have been a train-screen failure; the forced track confirms those would have lost (all three short pooled results negative).

**Candidate next control (not yet run, must be specified before running):** a drift baseline, meaning random-timed entries with identical brackets and holding rules, per direction. Any future directional hypothesis should be judged against it rather than against zero.

## 2026-09 - Walk-forward: trend continuation (H1)

Report: [walkforward_trend_continuation.md](walkforward_trend_continuation.md) · data: [walkforward_trend_continuation.json](walkforward_trend_continuation.json)

**Verdict: no demonstrated edge on any instrument, deployed or forced.** This supersedes the single-split baseline below.

| symbol | forced: profitable windows | median window bps | pooled trades / net bps / t | deployed |
|---|---|---|---|---|
| BTCUSD | 3/6 (50%) | -28.6 | 117 / -13.2 / -0.34 | traded 2 of 6 windows, both lost |
| EURUSD | 2/7 (29%) | -14.6 | 89 / -7.6 / -1.25 | abstained in all 7 windows |
| XAUUSD | 3/7 (43%) | -5.5 | 104 / +9.2 / +0.40 | pooled +9.2 bps, but one window = 116% of P&L |

- **The framework behaved as intended.** The deployed track abstained in all EURUSD windows because no candidate passed train and validation, which is the NO_TRADE outcome working. XAUUSD's small positive pooled result is exactly the "one exceptional period" case: window 1 (+123 bps x 9 trades) carries more than the whole pooled P&L, and the concentration rule rejects it.
- **Selection has no persistence.** Validation performance does not predict test performance (for example XAU window 6: validation +95 bps, test -179 bps; BTC window 1: validation +298, test -113). Chosen parameters also change almost every window. That is the signature of no stable conditional edge, not of a tuning problem.
- **Costs are not the binding constraint** on FX/gold (about 1-2 bps per trade). The gross signal is.
- **BTC train windows before mid-2023 include the 80-168 bps spread era**, so the train screen rejects most candidates there. BTC walk-forward results mainly reflect 2023-2026 cost conditions.
- **Sample size is still the limiting factor.** Forced pooled out-of-sample trades are 89-117 per instrument, about 4-5x the single split but still below what distinguishes a 5-10 bps edge from zero (per-trade sd is roughly 50-400 bps).

**Hypothesis for the regime-conditional stage (not a finding):** entries during high volatility (top tercile relative to the window's train period) lost on all three instruments (BTC -221 bps / 16 trades, EURUSD -14.5 / 8, XAUUSD -17.1 / 52), while low-volatility entries were positive on BTC (+37.6 / 68) and XAUUSD (+83.8 / 25). This is a post-hoc, small-cell observation from 9 cells examined per symbol; it may only be used if a volatility condition is fixed *before* a new walk-forward run.

## 2026-09 - Single split baseline: trend continuation (H1)

Report: [baseline_trend_continuation.md](baseline_trend_continuation.md)

- **No qualified edge.** The volatility-normalised trend-continuation hypothesis fails out of sample on all three instruments. Treat it as the NO_TRADE baseline that later hypotheses must beat.
- **Sign instability is the main failure.** EURUSD goes -0.4 / +37.7 / -36.3 bps across train/validation/test; XAUUSD +33.7 / -20.7 / +10.8. An edge that flips sign between periods cannot be traded.
- **Samples are too thin.** The slow parameters the grid prefers produce 11-24 trades per unseen segment. BTC test (+336 bps, t=2.19) rests on 14 trades after a negative validation period, which is noise, not evidence.
- **Costs are not the binding constraint on FX/gold** (1-2 bps per trade, and doubling them changes little). The gross signal is the problem.
- **BTC costs changed structurally.** Median quoted spread at this broker was 80 bps (2021) and 168 bps (2022), falling to about 2 bps by 2025-26. BTC train results are not cost-comparable to test.
- **Train selection overfits toward few-trade corners** (largest lookback, highest threshold). Future grids need a minimum-sample rule that is harder to game, or fewer free parameters.

