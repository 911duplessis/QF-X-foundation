# FX Session Directional Persistence v1

Status: **DRAFT**, awaiting the account owner's decisions D1-D7 below.
Nothing is frozen, and no code exists for this hypothesis. **No FX price data
has been read.** The seven-pair H1 archive is quarantined unread (see
`fx_session_persistence_intake.md`). The pre-data power calculation below
uses only already-published figures.

## Hypothesis (one symmetric claim)

> Conditional on an early-session directional displacement meeting the
> pre-registered threshold, subsequent same-session returns tend to continue
> in the direction of that displacement.

- Long and short are **one hypothesis**: the mechanism is directional
  persistence, which is symmetric. This departs from earlier practice
  (separate long/short hypotheses) for that stated reason. Pooling both
  directions doubles the sample, and long and short drift largely offset.
- Long and short results are **always reported separately** as diagnostics,
  so a pooled result cannot hide an asymmetric failure.
- The drift control remains mandatory.

It is distinct from prior hypotheses:
- trend continuation: generic multi-day trend;
- sweep: liquidity reversal;
- volatility expansion: compression, then breakout;
- this one: session-conditioned intraday persistence.

## Universe

EURUSD.m, GBPUSD.m, USDJPY.m, USDCHF.m, AUDUSD.m, USDCAD.m, NZDUSD.m
(7 USD majors, no crosses).

- **Evidence:** broker export filenames (intake log) and MT5 Specification
  windows captured 2026-09-27, stored in `assets/`:

| pair | screenshot sha256 |
|---|---|
| AUDUSD | `093550111d0094b66ec79aea64f06449ec2c8484f58600112b730276a9779adf` |
| EURUSD | `86a74416980ce7739386d7f370e984251738d735212f134c85c100b7a1f5b52a` |
| GBPUSD | `6e019b23eb096752e692ab065e405b7482a38eddae0a7c6249ee3de3e6326ae2` |
| NZDUSD | `a95e44ce7f93d40744d2dedfeec283861da61452a5aa8f77626018ab8da10c75` |
| USDCAD | `7f82f81e8dfd26ecd9e1aa16d27e136e1a71460bac13da28d6e4386b8d634d04` |
| USDCHF | `4c38c8a45e2f4080b8797d53623f765a7aeab6a787fbcccb07a41c3ad367fb68` |
| USDJPY | `90df4619f1861486baf137791a045f15c003feab9484c82c6bb898a29a9b85f5` |

- **Contract details, all seven:**
  - calculation Forex; contract size 100,000 base currency;
  - digits 5 (USDJPY: 3); execution Market, Fill or Kill;
  - quotes Monday-Thursday 00:00-24:00 and Friday 00:00-23:58 server time
    (trading Monday opens 00:02); no Sunday session;
  - no swap section is shown (see D7).

## Contamination disclosure

EURUSD.m test windows are **not untouched**. The trend-continuation
walk-forward reported coarse **session breakdowns** of EURUSD trades
(asia / london / overlap / new_york).
- That is recorded here as a disclosure, **not as evidence** for this
  hypothesis.
- No parameter below was derived from it.
- The other six pairs have not been analysed in this project.
- The research log must restate this disclosure next to the verdict.

## Definitions (H1 bars; UTC internally)

1. **Session anchor (D1):** London local time (Europe/London, DST-aware).
   The session open is 08:00 London; the session end is 16:00 London.
2. **Early window (grid K):** the K H1 bars starting at 08:00 London.
3. **Displacement:** d = close of the last window bar - open of the first
   window bar. Scale: s = ATR(24) x sqrt(K), with ATR(24) = the mean true
   range of the 24 H1 bars ending at the bar before the window (causal).
4. **Signal (grid theta):** |d| >= theta x s. Direction = sign(d). At most one
   signal per pair per day. No signal if any window bar, the entry bar or the
   ATR history is missing.
5. **Entry:** market order at the open of the first bar after the window
   (`delay_bars` = 1), paying half spread + slippage.
6. **Protective stop (D3):** entry -/+ 2.0 x ATR(24) (long / short).
   No profit target.
7. **Exit:** at the open of the 16:00-London bar (time exit), or at the stop
   if hit first. Pessimistic fills as in the bracket engine: stop first, gaps
   fill at the open.
   - The whole trade lies inside one London session and ends before the
     22:00-server rollover, so **no swap is ever charged by construction**.

## Grid (D2): 4 combinations

| axis | values |
|---|---|
| K (early-window hours) | 1, 2 |
| theta (displacement threshold, in s units) | 0.5, 1.0 |

Stop multiple, session times and exit are fixed; they are **not** in the grid.

## Walk-forward and selection

- 24M train / 6M validation / 6M test, 6M step; common origin 2021-01-04 UTC.
- **Parameter selection (D4): pooled across pairs.** One parameter set per
  window is chosen on the pooled train/validation results, instead of seven
  per-pair selections. This has 7x fewer degrees of freedom and matches the
  claim ("FX majors"). The train screen and validation selection work as in
  v1, applied to pooled trades.
- Deployed and forced tracks as before.

## Costs

- **Spread floor** = quoted spread from the captured Market Watch (identical
  in all seven screenshots). The capture was on a **Sunday**, so these are
  Friday-close quotes and conservative. Per-bar MT5 spread applies when wider.
- **Slippage** = floor / 6; **commission (D6)** = 0 pending confirmation for
  the account type.

| pair | spread floor | points | bps at capture | round trip incl. slippage (bps) |
|---|---|---|---|---|
| EURUSD.m | 0.00012 | 12 | 1.05 | 1.40 |
| GBPUSD.m | 0.00009 | 9 | 0.68 | 0.91 |
| USDJPY.m | 0.025 | 25 | 1.59 | 2.12 |
| USDCHF.m | 0.00013 | 13 | 1.57 | 2.09 |
| AUDUSD.m | 0.00009 | 9 | 1.28 | 1.71 |
| USDCAD.m | 0.00022 | 22 | 1.56 | 2.07 |
| NZDUSD.m | 0.00014 | 14 | 2.47 | 3.30 |

## Pre-data power calculation (gate)

- **Inputs:** only published figures and stated planning assumptions; no FX
  price data. Per-trade dispersion comes from the published EURUSD results
  (`power_analysis.json`): sweep 23-24 bps, expansion 33-34 bps
  (comparable multi-hour holds); trend 57 bps (multi-day, not comparable).
- **Test span:** 780 trading days (test windows 2023-07-04 to 2026-07-04;
  the final partial window covers < 50% and is excluded).
- **Formula (day-clustered):** MDE = 2.84 x sd x sqrt((1 + (k-1) rho) / (D k)),
  where k = 7 f is the expected number of signalling pairs per day and rho
  the cross-pair correlation of same-day trade returns.

| scenario | sd | rho | f | MDE (bps) |
|---|---|---|---|---|
| **central** | 30 | 0.5 | 0.40 | **2.51** |
| sd 40 | 40 | 0.5 | 0.40 | 3.35 |
| rho 0.7 | 30 | 0.7 | 0.40 | 2.74 |
| few signals (f 0.25) | 30 | 0.5 | 0.25 | 2.71 |
| all pessimistic | 40 | 0.7 | 0.25 | 3.80 |
| EURUSD alone, central | 30 | - | 0.40 | 4.04 |

- **Gate (D5):** the central estimate must be <= 3 bps (**met: 2.51**).
- The design is **tight**: pessimistic combinations exceed 3 bps.
- The realized MDE is reported after the run **descriptively only**. It
  cannot change the verdict or the rules.

## Qualification (unchanged standards)

Every walk-forward rule on the pooled deployed track, with:
- day-clustered t >= 2 (always reporting trades, unique days, windows, raw t
  and clustered t);
- block-randomized drift control p <= 0.05, via the same timestamp-group
  procedure as Replication R1, extended to replay each template's side.
  The control asks whether early-session displacement adds anything over
  random days at the same hour with the same side mix.

Long / short and per-pair results are descriptive only.

## Decisions for the account owner

| # | decision | recommendation |
|---|---|---|
| D1 | Session anchor: London local (DST-aware) vs fixed UTC | **London local**: the session is defined by market hours, which move with DST |
| D2 | Grid: K in {1, 2}, theta in {0.5, 1.0} (4 combinations) | **approve as is**; do not add |
| D3 | Protective stop 2.0 x ATR(24), no target, time exit at 16:00 London | **approve**: no target keeps the test about persistence, not about the R-multiple |
| D4 | Parameter selection pooled across pairs vs per pair | **pooled** (7x fewer degrees of freedom) |
| D5 | Power gate on the central estimate <= 3 bps, pessimistic reported | **approve**; alternative: require the pessimistic <= 3 (fails now, which means redesign) |
| D6 | Commission: confirm 0 for your account type | please confirm |
| D7 | Swap: irrelevant by construction (all positions close before rollover) | **approve**; no financing model needed |

## Explicitly excluded

- No New York session in v1 (a separate hypothesis if ever wanted).
- No news, holiday, day-of-week or volatility-regime filters.
- No crosses; no per-pair exclusions after data are read.
