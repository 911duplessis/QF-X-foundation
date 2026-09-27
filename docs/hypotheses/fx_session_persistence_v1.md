# FX Session Directional Persistence v1

Status: **DRAFT**. D1-D5 and D7 are approved; **D6 (commission) is pending and blocks the freeze**.
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

These are implementation definitions, **not tuning parameters**.

**Conventions**
- An H1 bar is identified by its **open** time and covers [open, open + 1h).
- Raw MT5 timestamps (server time, Europe/Athens) are converted to UTC by
  the existing loader, then to London local time with
  `zoneinfo("Europe/London")`. Hard-coded UTC or server hours are not allowed.
  - Check, computed hourly over 2020-2026: Athens minus London is +2h at
    every instant, because both follow the EU DST dates. So 08:00 London is
    always 10:00 server time.
  - The code still converts via the timezone database, and a test asserts
    the mapping on both sides of each DST switch.
- **Session day** = London calendar date, Monday-Friday. At most one signal
  per pair per session day.

**Timeline for session day D** (London local, bar open times)

| role | bars | K = 1 | K = 2 |
|---|---|---|---|
| ATR history | the 24 bars immediately before the window (by bar count) | last opens 07:00 | last opens 07:00 |
| observation window | the K bars opening at 08:00, ..., 08:00 + (K-1)h | 08:00 | 08:00, 09:00 |
| signal evaluated | at the close of the last window bar | 09:00 | 10:00 |
| entry fill | open of the bar opening at 08:00 + K h | 09:00 open | 10:00 open |
| time-exit fill | open of the bar opening at 16:00 | 16:00 open | 16:00 open |

The last bar held to its end is the 15:00 bar. The time exit fills at the
16:00 bar's open with exit-side costs.

1. **ATR causality (frozen):**
   - ATR(24) = the arithmetic mean of the true ranges of the 24 available H1
     bars immediately preceding the first window bar. The last of them is the
     bar opening at 07:00 London, which closes at the window start.
   - It **never includes any window bar, the entry bar or later bars**.
   - True range uses the prior bar's close. On Monday the 24 bars reach back
     into Friday (bar count, not clock time), so the weekend gap enters one
     true range. That is accepted and fixed.
   - The same ATR value is used for the threshold scale and for the stop.
     It is computed once per signal and never updated.
2. **Displacement:** d = close of the last window bar - open of the first
   window bar (mid prices). Scale: s = ATR(24) x sqrt(K).
3. **Signal (grid theta):** if |d| >= theta x s, go long when d > 0 and short
   when d < 0. d = 0 gives no signal.
4. **Eligibility (decided before data, by availability only, never by
   price):** a day is skipped for a pair if any of these is missing:
   - the bar opening at 08:00 London;
   - any window bar;
   - the entry bar;
   - fewer than 25 bars of history.
5. **Entry:** market order at the entry-fill bar open (`delay_bars` = 1, the
   existing convention), paying half spread + slippage.
6. **Protective stop (D3):** entry -/+ 2.0 x ATR(24) (long / short), active
   from the entry bar onward. No profit target.
7. **Exit:**
   - **Time exit** at the open of the bar opening at 16:00 London.
   - **Stop exit** first if hit, using the bracket engine's pessimistic
     fills: stop first on a same-bar touch, and a gap through the stop fills
     at the open.
   - If the 16:00 bar is missing, the time exit fills at the open of the next
     available bar. Every such case is counted and reported.
   - **Swap:** all fills occur before 18:00 server time, so no position
     crosses the 22:00 server rollover and **no swap is charged by
     construction**. A test asserts this.

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

**Design requirement (D5):** the pre-registered **central design MDE** must
be <= 3 bps. It is **2.51 bps**, so the requirement passes.

**Sensitivity analysis:** under pessimistic assumptions the MDE is
3.35-3.80 bps.
- This shows that resolution depends on the dispersion and correlation
  assumptions.
- It is **not** evidence that the design is robustly <= 3 bps. It must not be
  described as "powered" in an unconditional sense.
- It does not trigger a redesign.

The MDE is a design quantity, not a prediction of the outcome. Achieved
resolution (the realized clustered SE x 2.8416) is reported after the run,
**descriptively only**. It cannot change the verdict, the rules or the
qualification thresholds.

## Qualification (unchanged standards)

Every walk-forward rule on the pooled deployed track, with:
- day-clustered t >= 2 (always reporting trades, unique days, windows, raw t
  and clustered t);
- block-randomized drift control p <= 0.05, via the same timestamp-group
  procedure as Replication R1, extended to replay each template's side.
  The control asks whether early-session displacement adds anything over
  random days at the same hour with the same side mix.

Long / short and per-pair results are descriptive only.

## Decisions (account owner, 2026-09-27)

| # | decision | status |
|---|---|---|
| D1 | Session anchor: London local time, DST-aware via `Europe/London` | **approved** |
| D2 | Grid: K in {1, 2}, theta in {0.5, 1.0}; no additions after results | **approved** |
| D3 | 2.0 x ATR(24) stop, no target, time exit at the 16:00-London bar open (exact convention above) | **approved** |
| D4 | One parameter set per window, selected jointly across all seven pairs | **approved** |
| D5 | Central design MDE <= 3 bps as the formal requirement; pessimistic cases reported as sensitivity only | **approved with the wording above** |
| D6 | Commission per lot for this account's FX instruments | **PENDING**: must be established from broker or account evidence, not assumed. It blocks the freeze. |
| D7 | Swap outside the primary cost model (no position crosses rollover) | **approved** |

## Explicitly excluded

- No New York session in v1 (a separate hypothesis if ever wanted).
- No news, holiday, day-of-week or volatility-regime filters.
- No crosses; no per-pair exclusions after data are read.
