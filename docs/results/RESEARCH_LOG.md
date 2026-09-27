# QF-X Research Log

Interpretation of generated results. Files in this directory ending in `.md`/`.json`
next to an experiment are generated and must not be hand-edited; conclusions live here.

Research sequence: rolling walk-forward (done) -> trend continuation (no demonstrated edge) -> liquidity sweep/reversal (no demonstrated edge; no timing edge vs drift baseline) -> volatility expansion (not qualified) -> Replication R1 of the BTCUSD long candidate (not replicated; candidate closed)
-> volatility expansion -> regime-conditional combinations -> meta-engine
-> portfolio/correlation -> shadow trading. No execution layer before shadow trading passes.

Language rule: results say "no demonstrated edge", never "does not work".

## 2026-09 - Statistical resolution of the completed experiments (descriptive)

Report: [power_analysis.md](power_analysis.md) (+ `.json`). Module `qfx.research.power`, committed before it was run.

**Descriptive only.** Every verdict above stands; no rule, threshold or result is redefined. Per-trade data were reproduced from the frozen experiment code, and all 16 reproductions match their published pooled means exactly (the run asserts it).

Design MDE = the smallest true mean edge per trade with an 80% chance of passing *all* qualification components. The components are t >= 2 (day-clustered), >= 60% of windows profitable, and drift p <= 0.05. Forced track, test segments.

| instrument | bracket hypotheses (sweep, expansion) | trend continuation |
|---|---|---|
| EURUSD | 3.1-6.7 bps (2.5-5x cost) | 17.5 |
| XAUUSD | 6.4-26.5 | 61.1 |
| BTCUSD | 15.8-32.3 | 113.4 |
| Replication pool (ETH+LTC+XRP) | 55.9 | - |

- **Resolution depends mostly on the instrument's per-trade dispersion, not on the hypothesis.** EURUSD tests were sharp: a few-bps edge would very likely have been caught. BTC and gold tests only resolved edges of roughly 15-30+ bps/trade (4-20x costs). Trend continuation on BTC was close to blind.
  - **Consequence for the verdicts:** EURUSD failures are strong evidence of no edge above ~4-7 bps there. BTC and gold failures only rule out large edges.
- **The t >= 2 rule is the binding constraint almost everywhere.** The window rule needs about half the edge; the drift test is close to the t rule.
- **The BTCUSD candidate never had a fair confirmation test.**
  - If its observed +15.85 bps were the true edge, the discovery design had 34% power and the replication 12% power to pass t >= 2.
  - The replication still carries information: its -26.27 bps is 2.14 SE below +15.85 (one-sided p = 0.016). The data are fairly inconsistent with an effect of that size.
  - The closure stands, now with the reason made explicit.
- **Why the replication pool was so coarse:** per-trade dispersion of 307 bps, driven by LTC and XRP trades carrying 60-168 bps costs, and a few window-level trade clusters.

**Implication for the next design (a recommendation, not a finding):** hypotheses tested one instrument at a time on BTC, gold or altcoins at H1 can only detect implausibly large edges. The places where this framework has resolution are low-cost, low-dispersion instruments. EURUSD reached 3-7 bps; pooled FX majors with long broker history would plausibly reach ~2-3 bps. Risk-normalized (R) returns could further reduce dispersion from volatility regimes. Any such design must be pre-registered with its own power target *before* data are examined.

## 2026-09 - Replication R1: Volatility Expansion v1 (long) on the broker crypto universe

Pre-registration trail:
- universe captured `4bb951a`;
- v1 frozen `28fe237`;
- v2 amendment (BTC-base symbols excluded) `32c16e4`;
- spreads, specs and financing `4cc06bd` / `3ab38da`;
- eligibility (checkpoint 3) `737a190`;
- checkpoint-4 spec, code and tests `1b6fb6e`, committed before any replication result.

Report: [replication_r1.md](replication_r1.md) (+ `.json`); eligibility: [replication_r1_eligibility.md](replication_r1_eligibility.md).

**Primary outcome: NOT REPLICATED.** The pooled ETH/LTC/XRP result fails 7 rules:

| rule | result |
|---|---|
| pooled test net > 0 (deployed) | -15.78 bps/trade (forced -26.27) |
| positive at 2x costs | -19.83 |
| >= 60% traded windows profitable | 25% (forced 17%) |
| median window > 0 | -16.3 |
| >= 60% windows surviving 2x costs | 0% |
| day-clustered t >= 2 | -0.59 (forced -1.34) |
| block drift p <= 0.05 | 0.327 |

- **Effectively an ETH test.**
  - The frozen cost gate (spread <= 25% of stop distance) admitted 5 LTC trades (168 bps cost/trade) and 91 XRP trades (60 bps). All 122 deployed trades and 190 of 286 forced trades are ETH.
  - N = 3 by rule, but the evidence comes mostly from one coin.
  - This is the frozen rule working as specified; it is not changed after the fact.
- **ETH is the fairest test available, and it fails clearly.**
  - Liquid, cheap (7.3 bps cost/trade), and the coin most correlated with BTC.
  - Forced track: -20.39 bps/trade, 1 of 6 windows profitable.
  - If the BTCUSD observation reflected a crypto-wide breakout effect, ETH is where it should have appeared.
- **Clustering diagnostics:**
  - forced: 286 trades on 244 unique days, raw t -1.45 vs clustered -1.34;
  - deployed: 122 trades on 119 days.
  - The cross-coin clustering we guarded against was small, because LTC and XRP rarely traded.
  - The projected ~600-trade sample did not materialize, for the cost reason above.
- **Block drift control:**
  - test: the observed result beats the matched random timing by +6.58 bps (p = 0.327), but both are negative;
  - train p = 0.002, which is selection-biased and not evidence (as recorded in the spec);
  - the control produced more trades than observed (339 vs 286), consistent with breakout signals clustering in time.
- **XRP, descriptive only:** gross before costs is roughly +26 bps/trade on 91 trades, and net is -34 after 60 bps of costs. It is too few trades and too expensive to mean anything, and per-coin results have no qualification role.

**Financing sensitivity (descriptive):**
- Standard swaps would make the pooled result worse: forced -26.27 -> -34.83.
- **BTCUSD v1 candidate re-costed:** +15.85 -> **+9.91 bps/trade** at standard swaps (-5.94), within the -5 to -10 estimate recorded before the run.

**Status of the BTCUSD long observation: not replicated, demoted.**
- Original evidence: drift p = 0.044, walk-forward t = 1.61, not significant after multiple-comparison adjustment.
- It did not reproduce on the one independent, affordable, highly correlated instrument available (ETH).
- The most likely explanation is a BTC- and period-specific result (chance plus drift).
- Per the research rules this reads "no demonstrated edge", not "volatility expansion does not work".
- The BTCUSD observation is **closed**: re-testing it on the same data, or on newly chosen instruments after seeing this result, would be a new discovery exercise and needs its own pre-registration.

**Limitations recorded:**
- the broker's short crypto history (most coins from 2022) limited the universe;
- high spreads on LTC and XRP limited the effective sample;
- a failure driven mostly by ETH is weaker evidence about low-spread altcoins in general than about ETH.

## 2026-09 - Volatility Expansion v1 (H1): walk-forward and drift control

Specification frozen before implementation: [volatility_expansion_v1.md](../hypotheses/volatility_expansion_v1.md) (draft `fe4ebfe`, frozen `5feeb35`); implementation `2d93049` committed before any result.
Reports: walk-forward [long](walkforward_vol_expansion_long.md) / [short](walkforward_vol_expansion_short.md); drift control [drift_baseline_v1_vol_expansion.md](drift_baseline_v1_vol_expansion.md) (+ `.json` for each).

**Contamination disclosure (restated as the specification requires):** compression is a low-volatility condition, and a post-hoc observation that low-volatility trend entries did better was made earlier on these same 2023-2026 test windows. This hypothesis is not independent of that observation and its test windows were not fully untouched for volatility questions. The compression threshold (20th-percentile rank) and lookback (500 bars) were fixed before this run and were not tuned.

**Verdict: no qualified hypothesis.** One candidate (BTCUSD long) needs confirmation on data this project has not yet seen.

| direction | symbol | forced test trades | net bps/trade | walk-forward t | walk-forward (deployed) | drift control mean | vs drift p | qualified |
|---|---|---|---|---|---|---|---|---|
| long | BTCUSD | 211 | +15.85 | +1.61 | fails (t, concentration) | -3.41 | **0.044** | NO |
| long | EURUSD | 225 | +0.67 | +0.30 | fails | -0.98 | 0.200 | NO |
| long | XAUUSD | 159 | +21.51 | +2.31 | fails (concentration 52%; forced track passes) | **+13.64** | 0.174 | NO |
| short | BTCUSD | 189 | +7.12 | +0.64 | fails | -6.21 | 0.132 | NO |
| short | EURUSD | 207 | -1.53 | -0.64 | fails | -1.44 | 0.539 | NO |
| short | XAUUSD | 189 | -11.69 | -2.23 | fails | -6.09 | 0.836 | NO |

- **XAUUSD long is the case the drift control was built for.** On the forced track it passes every walk-forward rule: 159 trades, +21.5 bps/trade, t = 2.31, 71% of windows profitable, 71% surviving 2x costs, 46% concentration. Random-timed long gold trades with identical brackets, gates and costs earned +13.64 bps/trade over the same windows. The excess (+7.86) is not significant (p = 0.174). Most of the apparent edge is gold's drift. Without the control this would have looked like the first qualified strategy.
- **BTCUSD long is the first p <= 0.05 against drift, and it still does not qualify.**
  - For: it beat its matched random control in 5 of 6 test windows, with no window dominating (34% forced concentration).
  - Against: walk-forward significance fails (forced t = 1.61, deployed t = 1.07), and deployed concentration is 55%. The secondary total-P&L p is 0.058.
  - Multiple testing: with 6 comparisons in this run, the chance of at least one p <= 0.05 under the null is 26%, and p = 0.044 does not survive a Bonferroni threshold of 0.0083.
  - Train and validation were also above the drift band (p = 0.020 and 0.040), but those segments are selection-biased and overlapping, so they add little.
- **Mechanics verified.** Compression flags 20.8-22.1% of bars (a 20th-percentile rank rule); stop exits land at -1.02 to -1.04 R and 2R targets at +1.97 R; the cost gate removed ~38% of BTC setups (2021-22 spreads) and none elsewhere.
- **Trade-count note.** Controls produced more trades than the hypothesis (for example 202 vs 159 for XAU long), because breakout signals cluster and the engine drops signals while a position is open. The primary statistic (mean per trade) is unaffected; total P&L p-values are reported as the secondary check and agree in direction.
- **No parameter, filter or entry rule was changed after seeing these results.**

**What would move BTCUSD long forward (not done; requires your decision):** a confirmation run of Volatility Expansion v1 **unchanged**, long BTCUSD only, on data after 2026-09-04 (the end of the current export), with the qualification rules and drift control fixed in advance. Re-testing on the existing data cannot confirm it. The existing data has been used, and any re-analysis of it becomes another comparison.

## 2026-09 - Drift Baseline v1: timing-shuffled control for Sweep Reversal v1

Specification frozen before implementation: [drift_baseline_v1.md](../hypotheses/drift_baseline_v1.md) (draft `cae9793`, frozen `73e744b`); code committed before the run.
Report: [drift_baseline_v1.md](drift_baseline_v1.md) · data: [drift_baseline_v1.json](drift_baseline_v1.json). 500 hour-matched repetitions per window and segment; one-sided empirical randomization test.

**Q2 (pre-registered, test segments): no demonstrated timing edge in either direction on any instrument.** Sweep timing is statistically indistinguishable from random timing out of sample.

| direction | symbol | sweep test mean | control mean (drift line, Q3) | difference | p | sweep percentile in null | Q1 (train) |
|---|---|---|---|---|---|---|---|
| long | BTCUSD | -13.87 | -2.18 | -11.69 | 0.878 | 12% | inside band: drift/geometry |
| long | EURUSD | -1.56 | -1.55 | -0.00 | 0.487 | 51% | above band (see caveat) |
| long | XAUUSD | -0.19 | +6.64 | -6.84 | 0.918 | 8% | inside band: drift/geometry |
| short | BTCUSD | -1.71 | -9.90 | +8.19 | 0.086 | 92% | inside band: drift/geometry |
| short | EURUSD | -1.88 | -1.58 | -0.29 | 0.617 | 38% | inside band: drift/geometry |
| short | XAUUSD | -3.09 | -3.40 | +0.31 | 0.455 | 55% | inside band: drift/geometry |

(bps per trade; secondary total-P&L p-values agree within 0.03 in every case.)

- **The open question is answered for gold and BTC.** The sweep-long in-sample positivity is drift and geometry, not sweep timing: XAUUSD long train +2.42 bps vs +2.55 for random-timed trades with identical brackets (45th percentile); BTCUSD long inside the band too.
- **Gold drift is large, and sweep timing gave it away.** Random long gold trades earned +6.64 bps/trade in the test windows; the sweep-timed ones earned -0.19 (8th percentile). Any future long-gold result must be read against about +6.6 bps, not zero.
- **EURUSD long is the only in-sample exception, and it did not survive.** Train p = 0.004 and validation p = 0.020, then test p = 0.487 (exactly the random-timing result). Caveat on Q1: train and validation p-values are biased toward significance, because the forced track selects the parameter set that did best there, and 24-month train windows overlap (each period counted up to 4 times when pooled). Only test p-values are clean. An in-sample result that vanishes in untouched test data is the expected signature of selection, not of an edge.
- **BTC short is the closest to significance and still fails.** p = 0.086, and in absolute terms it still loses (-1.71 bps/trade). Beating a strongly negative drift line (-9.90 for random shorts in a bull market) is not a tradeable edge.
- **Six test comparisons, none significant.** No multiple-comparison adjustment is needed to reach the conclusion; one would only make it stronger.
- **Sweep parameters were not changed on the basis of this control**, as specified.

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

**Next control, now run:** see Drift Baseline v1 above. It confirms the drift explanation for gold and BTC.

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

