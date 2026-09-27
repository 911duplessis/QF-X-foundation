# Replication R1: Volatility Expansion v1 (long) on the broker crypto universe

Status: **FROZEN, version 2**. Draft `4bb951a`; v1 frozen `28fe237`
(D1 = keep, D2 = yes). **v2 amendment (2026-09-27): D1 reversed to exclude
BTC-base symbols** by the account owner. When the amendment was made:
- no data for any BTC cross pair had been received;
- no strategy result existed for any replication symbol;
- inspection of any symbol was limited to the intake log below.

The reversal therefore cannot be result-driven. v1 remains in git history.

- Instrument metadata values (spreads, swaps, contract details) are **facts to
  record under the fixed rules below**, not choices. They must be recorded in
  a commit **before any strategy computation** on replication symbols.
- Any change to a rule requires a v2.
- See "Data intake log" for exports received before this freeze.

## Purpose

Confirm or reject the BTCUSD long observation from Volatility Expansion v1
(drift p = 0.044, walk-forward t = 1.61, not qualified) on instruments the
project has never analysed. This is a **confirmation**, not a discovery run:

- The hypothesis is Volatility Expansion v1 **exactly as frozen** (`5feeb35`):
  same grid, compression rule, gates and per-coin parameter selection.
- **Direction is frozen to long.** Short is not tested as a competing
  replication hypothesis.
- One primary pooled test decides the outcome. Per-coin results are
  descriptive only; a single coin with p <= 0.05 is not a replication.

## Broker universe (captured 2026-09-27, before any export)

Source: MT5 Market Watch / Symbols panel screenshot supplied by the account
owner, stored at `assets/replication_r1_broker_crypto_symbols_2026-09-27.png`
(sha256 `bc55bbe8a8757f07665b34f3656b324ca3de9a79e903bcbee4a82054802a1084`).

20 crypto symbols listed: BTCUSD.m, BCHUSD.m, ETHUSD.m, LTCUSD.m, XRPUSD.m,
ADAUSD.m, DOTUSD.m, XLMUSD.m, KSMUSD.m, SOLUSD.m, TRXUSD.m, UNIUSD.m,
BTCEUR.m, BTCGBP.m, BTCJPY.m, BTCXAU.m, AVAXUSD.m, DOGEUSD.m, LINKUSD.m,
MATICUSD.m.

## Eligibility rule

A symbol is eligible if and only if **all** of the following hold:

1. It appears in the captured list above.
2. Its base asset is not BTC, the discovery asset. **D1 = exclude (v2):**
   BTCUSD.m (discovery symbol), BTCEUR.m, BTCGBP.m, BTCJPY.m and BTCXAU.m are
   excluded, leaving 15 candidates. Reason: the crosses are BTC priced in
   other currencies over the discovery period (~95%+ correlated hourly
   moves), so including them would partly re-test the discovery data. They
   need not be exported.
3. Its MT5 H1 export passes `qfx.backtest.mt5.load_mt5` with exactly the
   BTCUSD settings: server timezone Europe/Athens, interval 1h, max gap 4 days,
   D1-prefix trimming, Gate 0 unchanged.
4. After trimming, its first H1 bar is <= 2021-01-01 00:00 UTC and its last
   H1 bar is >= 2026-08-24 00:00 UTC.

Symbols failing any condition are excluded and listed with the reason. There
is **no minimum N**; the rule is not relaxed to reach one. If N = 0, the
replication cannot proceed, and that is a valid outcome.

## Instrument metadata (to capture before freeze)

Recorded from each symbol's MT5 contract specification. For the cost rows,
the recorded value is the one QF-X uses.

| field | used for |
|---|---|
| symbol, description, base / quote asset | eligibility D1 |
| contract size, digits, point, tick size, tick value | price units, sizing |
| spread (quoted at capture time) | spread floor |
| commission | costs |
| swap type (points / percent / money), swap long, swap short | financing |
| rollover time, triple-swap day, whether swaps apply on weekends | financing |
| trading hours / sessions | Gate 0 gap interpretation |
| first and last available H1 timestamp (from the export, not the spec) | eligibility |

## Quoted spreads at capture (spread floors)

Source: 15 MT5 Market Watch bid/ask snapshots, 2026-09-27 11:35-11:42 server
time, stored at `assets/replication_r1_market_watch_quotes_2026-09-27.zip`
(sha256 `88309d2a158b9535126327bdef2199cfc9561094d5007cb2b2aa04ea5a545135`).

- **Measurement rule (fixed in v2):** spread floor = median of (ask - bid)
  over all snapshots that contain the symbol.
- The capture was on a Sunday. Weekend crypto spreads are usually wider, so
  these floors are conservative; per-bar MT5 spreads still apply when wider.
- High-spread symbols (e.g. LTC, XRP) are **not** excluded. The frozen cost
  gate (spread <= 0.25 x stop distance) decides trade by trade.

| symbol | spread floor (price units) | bps at capture | snapshots |
|---|---|---|---|
| BCHUSD.m | 0.8 | 23.3 | 2 |
| ETHUSD.m | 1.4 | 5.2 | 15 |
| LTCUSD.m | 1.43 | 198.7 | 15 |
| XRPUSD.m | 0.01 | 65.1 | 15 |
| ADAUSD.m | 0.0007 | 27.2 | 15 |
| DOTUSD.m | 0.005 | 39.9 | 15 |
| XLMUSD.m | 0.0004 | 18.3 | 15 |
| KSMUSD.m | 0.05 | 101.3 | 15 |
| SOLUSD.m | 0.21 | 16.9 | 15 |
| TRXUSD.m | 0.00058 | 17.4 | 15 |
| UNIUSD.m | 0.0101 | 10.1 | 15 |
| AVAXUSD.m | 0.0242 | 21.8 | 15 |
| DOGEUSD.m | 0.00024 | 24.5 | 15 |
| LINKUSD.m | 0.02 | 13.9 | 15 |
| MATICUSD.m | 0.0006 | 49.9 | 15 |

## Instrument metadata (recorded 2026-09-27)

Source: MT5 Specification windows (JustMarkets, server "JustMarkets-Demo3",
broker Just Global Markets Ltd.), screenshots stored at
`assets/replication_r1_spec_*.png`. Values as displayed.

| symbol | eligibility so far | digits | contract size | trade mode | quote sessions (server time) | margin rate |
|---|---|---|---|---|---|---|
| ETHUSD.m | passes history rule | 2 | 1 | Full access | 00:05-24:00 daily | 0.002 |
| XRPUSD.m | passes history rule | 4 | 1,000 | Full access | 00:05-24:00 daily | 0.005 |
| DOGEUSD.m | export pending | 5 | 10,000 | Full access | 00:00-24:00 daily | 0.05 |
| SOLUSD.m | ineligible (history) | 2 | 100 | Full access | 00:00-24:00 daily | 0.05 |
| DOTUSD.m | ineligible (history) | 3 | 100 | **Close only** | 00:00-24:00 daily | 0.05 |
| ADAUSD.m | ineligible (history) | 4 | 1,000 | Full access | not captured | not captured |
| LTCUSD.m | passes history rule | not captured | | | | |

- **Common to all captured:**
  - Exchange XCCC; calculation CFD; execution Market; filling Fill or Kill;
  - volume 0.01 to 100, step 0.01;
  - Sunday trading has a 10-minute break (00:09-00:19);
  - tick size and tick value display as 0.
- QF-X does not need contract size or tick value: returns and costs are in
  price units and bps, where they cancel.
- **Commission: 0** (broker crypto conditions page, Standard account).
- **Swap: none on this account.** Two independent sources agree:
  - no swap section appears in any captured Specification window;
  - the JustMarkets crypto conditions page (text pasted by the account owner
    on 2026-09-27, excerpt stored at `assets/replication_r1_broker_crypto_conditions_2026-09-27.md`)
    says every crypto symbol is "Extended Swap-free available" and that
    "all customer accounts from any country are automatically given
    swap-free status".
- The demo rollover check is now optional confirmation, not a blocker.
- Current trade mode (e.g. DOTUSD "Close only") is not an eligibility
  criterion; eligibility is historical.

### Financing rule (recorded 2026-09-27)

- **Primary: financing = 0** (swap-free account status). The primary
  outcome and all qualification rules use this.
- **Descriptive sensitivity: standard (non-swap-free) rates**, per the same
  broker page:
  - the published long swap in points per night;
  - charged at 22:00 server time on weekdays only, with Wednesday tripled;
  - converted to bps of entry price.

  Reported next to the primary result for the replication and for the
  BTCUSD v1 re-costing. It has **no qualification role**, but it shows
  whether any edge depends on swap-free status.
- Risk recorded: swap-free status is a broker policy and can change; a
  result that only survives at zero financing depends on it.

| symbol | standard long swap (points/night) | digits (from quotes) | bps per night at capture prices |
|---|---|---|---|
| BTCUSD.m | -8466.6 | 2 | -9.99 |
| ETHUSD.m | -280.56 | 2 | -10.33 |
| LTCUSD.m | -10.632 | 2 | -14.74 |
| XRPUSD.m | -27.828 | 4 | -18.1 |
| BCHUSD.m | -39.228 | 2 | -11.42 |
| UNIUSD.m | -98.53 | 4 | -9.84 |
| AVAXUSD.m | -336 | 4 | -30.29 |
| DOGEUSD.m | -32.16 | 5 | -32.81 |
| LINKUSD.m | -19.68 | 3 | -13.71 |
| MATICUSD.m | -4.08 | 4 | -33.93 |

Estimated impact on the BTCUSD v1 candidate at standard rates: average hold
6-30 hours by window (~0.5-1 rollover per trade plus Wednesday triples),
about -5 to -10 bps against +15.85 bps/trade. The exact re-costing is
computed with the financing implementation (checkpoint 4).

## Costs (rule-based, fixed before data)

- **Spread floor:** the broker's quoted spread recorded at capture, in price
  units. Per-bar MT5 spread is used when wider, as for all prior runs.
- **Slippage:** spread floor / 6 per side, the same ratio as BTCUSD
  (5 / 30).
- **Commission:** as recorded (0 if none).
- **Financing (new):** each trade is charged the recorded long swap for every
  broker rollover its holding period crosses, with the triple-swap rule and
  the weekend rule as recorded, converted to bps of entry price.
  - Applied identically to observed trades and to drift-control trades.
  - Doubled in the 2x cost stress, together with spread, slippage and commission.
- **BTCUSD re-costing:** the v1 BTCUSD long result is re-reported with
  financing as a descriptive sensitivity check only. It cannot promote the
  BTC hypothesis.

## Walk-forward

- Window lengths unchanged: 24M train, 6M validation, 6M test, 6M step.
- **Decision D2 = yes:** a common origin of 2021-01-01 00:00 UTC for every
  eligible coin, so that test windows are identical calendar periods across
  coins and can be pooled window by window. This differs from prior runs,
  which used each instrument's own first bar; recorded as a procedural difference.
- **Data start:** bars before 2021-01-01 00:00 UTC are discarded after
  eligibility is checked.
- **Data end:** each eligible coin is truncated at the earliest last-bar
  timestamp across all eligible coins, so every coin covers the same span.
  The v1 partial-final-window rule (>= 50% test coverage) is unchanged.
- Parameter selection **per coin**, exactly as v1: train screen, validation
  selection, deployed and forced tracks. No pooling of parameters across coins.

## Primary outcome (single test)

**Pooled statistic:** mean net bps per trade (after financing) over all
eligible coins' test-segment trades on the track named in the rule, per window
and pooled across windows.

**Replication is confirmed only if every rule below holds:**

1. Pooled net bps/trade > 0 and pooled expectancy > 0 (deployed track).
2. **Calendar-day clustered t >= 2**:
   - t = mean / SE_cluster;
   - clusters are UTC calendar days of trade entry;
   - SE_cluster = sqrt( G/(G-1) x sum_g (sum_{i in g} (x_i - mean))^2 ) / n, over G clusters and n trades.
3. All existing walk-forward consistency rules, applied to pooled per-window
   results:
   - >= 60% of traded test windows profitable;
   - median window > 0;
   - >= 60% of windows positive at 2x costs;
   - no window > 50% of pooled P&L;
   - pooled validation > 0;
   - >= 30 pooled test trades.
4. Pooled result positive at 2x costs (including financing).
5. **Block-randomized drift control p <= 0.05** (below).

The per-coin results are secondary and descriptive only: trades, bps/trade,
t, windows, drift p and cost sensitivity. They get no qualification
opportunity.

## Block-randomized drift control

Drift Baseline v1 statistics (500 repetitions, sha256 seeds, one-sided
empirical p = (1 + #{control >= observed}) / (N + 1), forced track) with
timestamp-block randomization:

1. **Groups.** For each walk-forward segment, all observed signals (after
   gates) are grouped by signal timestamp. Every coin that signalled at time t
   belongs to group t.
2. **Replacement.** In each repetition, each group gets **one** random
   replacement timestamp t' drawn without replacement from bars of the
   same segment with the same UTC hour, at which all group members have data.
3. **Replay, not re-detection.** Each member's own signal is replayed at t':
   - long;
   - the same stop distance in ATR(24) units, rescaled with ATR at t';
   - the same target R and max hold;
   - the member's own costs, financing, gates and execution.

   Volatility Expansion conditions are **not** re-evaluated at t'.
4. **Gates.** If any member fails a gate at t', the whole group is redrawn,
   up to 20 times. After that, the whole group is dropped and the drop is
   recorded. Members are never retained selectively.
5. **Statistic.** Each repetition's control trades from all coins are pooled
   into the same pooled statistic as the observed result.

## Data intake log

Exports received **before** this freeze commit, in two uploads on 2026-09-27.
The eligibility rule (conditions 3-4) was already committed in the draft
`4bb951a` before any file arrived.

Inspection so far was limited to the header and the first and last timestamp
of each file. No prices, returns or signals were read. Gate 0 has not been
run. The files are not committed; hashes are recorded here.

| file | sha256 | first bar (server) | condition 4 |
|---|---|---|---|
| ETHUSD.m_H1_202101010000_202609270000.csv | `bc251b7f0cfabd762f0b2bfd5dd71aab5850a90920fb8bfe674584cc888dfc12` | 2021-01-01 00:00 | passes (Gate 0 pending) |
| LTCUSD.m_H1_202101010000_202609270000.csv | `c9119d5d28d4c28e64d81d5ec3504cfc96cd6038f32abc4fc18accd4969891df` | 2021-01-01 00:00 | passes (Gate 0 pending) |
| XRPUSD.m_H1_202101010000_202609270000.csv | `985fa84fb00e602d631d8323b60ff6aa83868dcd8285e199a9112c6021744e10` | 2021-01-01 00:00 | passes (Gate 0 pending) |
| ADAUSD.m_H1_202206200000_202609270000.csv | `8348ce2c1b3cfdf1b679d6cf02460c01c5c267b30ce83e23342da8fac85e294c` | 2022-06-20 00:00 | **fails: ineligible** |
| DOTUSD.m_H1_202206200000_202609270000.csv | `40450db1196c3447297615cebafc1ade4b75110b380f7ad9d843d2fc72e8bac3` | 2022-06-20 00:00 | **fails: ineligible** |
| XLMUSD.m_H1_202206200000_202609270000.csv | `e90aa2dbe803b5291aa5ac95ae0d960d67b06cc7faf2ec2551629516003f60e7` | 2022-06-20 00:00 | **fails: ineligible** |
| SOLUSD.m_H1_202208150000_202609270000.csv | `9c3a1b9da48e71a7406dc3bbe57220577b87932e7eda8203deea058703e418f2` | 2022-08-15 00:00 | **fails: ineligible** |
| KSMUSD.m_H1_202208150000_202609270000.csv | `80035fd405d9a6715ee9efbf9f6d93e855839fa21bc7c9562d54b98cad8c9844` | 2022-08-15 00:00 | **fails: ineligible** |
| TRXUSD.m_H1_202402061100_202609270000.csv | `082f35094a5a932ea6fd5c275bb59b0b6be4f2e6a2bdd0f3c577235978b7a33c` | 2024-02-06 11:00 | **fails: ineligible** |

Not yet received (v2 universe): BCHUSD.m, UNIUSD.m, AVAXUSD.m, DOGEUSD.m,
LINKUSD.m, MATICUSD.m. BTC cross pairs are no longer needed.

**Export instruction for the remaining symbols:** export H1 from the earliest
date the terminal offers (not from 2021-01-01), so that condition 4 is tested
against the broker's full history and not against the chosen export start.

**Caveat on the three passing files:** they were exported starting exactly
at 2021-01-01 00:00 server time (= 2020-12-31 22:00 UTC), which satisfies
condition 4 by 2 hours. It shows the broker has H1 history at least that far
back. Whether it goes further back does not affect eligibility.

## Eligibility outcome (checkpoint 3, 2026-09-27)

All 15 candidate exports were received. The rule was applied by
`qfx.research.replication_eligibility` (data quality and history only; no
returns, signals or strategy computation). Generated report:
`docs/results/replication_r1_eligibility.md` (+ `.json`).

**Eligible: N = 3: ETHUSD.m, LTCUSD.m, XRPUSD.m.**

- History rule (first H1 <= 2021-01-01 UTC): passed by ETH, LTC, XRP and BCH.
  The other 11 start 2022-06 or later.
- **BCHUSD.m fails Gate 0 (unchanged):** `resolution_change` from a feed
  outage on 2021-02-06/07 with six consecutive gaps: 2021-02-06 09:00->11:00 (+2h); 2021-02-06 13:00->15:00 (+2h); 2021-02-06 15:00->21:00 (+6h); 2021-02-06 22:00->00:00 (+2h); 2021-02-07 00:00->04:00 (+4h); 2021-02-07 04:00->08:00 (+4h).
  The rule is not relaxed; BCH is excluded.
- LINKUSD.m also fails Gate 0: a 1,129-day gap.
- Eligible files stored at `data/mt5/replication_r1/` (sha256 in the report);
  ineligible files are logged by hash only.
- All three eligible series end at 2026-09-26 21:00 UTC, so the data-end rule
  truncates nothing.

Consequence, stated in advance of any result: with N = 3 highly correlated
coins, the day-clustered t will have far fewer effective observations than
the trade count suggests. A failure to replicate at N = 3 is weaker evidence
against the BTC observation than a failure at larger N would be. A success
still has to pass every rule.

## Checkpoint 4 freeze (2026-09-27)

Committed together with the checkpoint-4 code and tests, **before any
replication result exists**. Up to and including this commit:
- no strategy calculation (signals, trades, returns) has been run on
  ETHUSD.m, LTCUSD.m or XRPUSD.m;
- the only computations on replication data were the checkpoint-3
  data-quality and history checks.

**Frozen as approved by the account owner:**

1. **Universe:** ETHUSD.m, LTCUSD.m, XRPUSD.m only (N = 3). No further
   exclusions based on results; no shorter-history coins added.
2. **Walk-forward:**
   - Volatility Expansion v1 unchanged, long only;
   - per-coin parameter selection exactly as v1;
   - common origin 2021-01-01 UTC; 24M / 6M / 6M windows with a 6M step;
   - results pooled across coins window by window;
   - qualification on the pooled **deployed** track (as v1).
3. **Clustered t:** calendar-day (UTC entry date) clustered SE; threshold
   t >= 2. The report always shows:
   - number of trades;
   - number of unique calendar days;
   - number of test windows;
   - the raw trade-level t (**diagnostic only**);
   - the day-clustered t (**used for qualification**).
4. **Drift control:**
   - replays observed signals, never searches for new ones;
   - same-UTC-hour randomization;
   - signals at the same timestamp form a group, and the whole group gets
     one random timestamp;
   - on any member's gate failure (or missing bar), the whole group is
     redrawn, up to 20 redraws, then dropped and recorded;
   - 500 fixed-seed repetitions;
   - same pooled statistic as observed (mean net bps/trade, forced track as
     in Drift Baseline v1);
   - p = (1 + #{control >= observed}) / 501.
5. **Primary outcome:** the pooled deployed track passes every walk-forward
   rule, with the IID pooled t replaced by day-clustered t >= 2, **and**
   block drift p <= 0.05 on test segments. Per-coin results are descriptive.
6. **Financing:**
   - primary = 0 (swap-free account);
   - standard swaps (22:00 server, weekdays, Wednesday x3; holding interval
     [entry, exit + 1 bar)) reported as a descriptive sensitivity for the
     replication, and separately as a BTCUSD v1 re-costing;
   - neither can alter the replication verdict.

## Explicitly forbidden

- New parameter grid, compression threshold or lookback.
- New filters (session, volatility tercile, trend, day-of-week).
- Excluding coins for expected behaviour, cost, or results.
- Pooling parameters across coins.
- Any change after replication data is exported.

## Checkpoints (each one a separate commit)

1. **This draft:** universe captured and screenshot hashed.
2. **FREEZE** (this commit): decisions D1/D2 made, intake log recorded.
   Then contract specifications are recorded in a separate commit, before
   step 4.
3. Export H1 data for the captured symbols, run Gate 0, apply the eligibility
   rule, and commit the eligibility report before any strategy code runs on
   these symbols.
4. Implement and test the financing model, pooled clustered t, and block drift
   control, before any replication result.
5. Walk-forward, then the drift test, then the research log. PR.

## Frozen parameters (completed at freeze)

```json
{
  "name": "replication_r1_vol_expansion_crypto",
  "version": 2,
  "status": "frozen",
  "amendments": [{"version": 2, "date": "2026-09-27", "change": "D1 reversed: exclude BTC-base symbols",
                  "made_before": "any BTC-cross data and any replication result"}],
  "hypothesis": {"spec": "volatility_expansion_v1", "frozen_commit": "5feeb35", "direction": "long"},
  "universe_capture": {
    "date": "2026-09-27",
    "screenshot_sha256": "bc55bbe8a8757f07665b34f3656b324ca3de9a79e903bcbee4a82054802a1084",
    "symbols": ["BTCUSD.m", "BCHUSD.m", "ETHUSD.m", "LTCUSD.m", "XRPUSD.m", "ADAUSD.m", "DOTUSD.m",
                "XLMUSD.m", "KSMUSD.m", "SOLUSD.m", "TRXUSD.m", "UNIUSD.m", "BTCEUR.m", "BTCGBP.m",
                "BTCJPY.m", "BTCXAU.m", "AVAXUSD.m", "DOGEUSD.m", "LINKUSD.m", "MATICUSD.m"]
  },
  "eligibility": {
    "exclude_discovery_symbol": "BTCUSD.m",
    "exclude_btc_base_asset": true,
    "candidates": ["BCHUSD.m", "ETHUSD.m", "LTCUSD.m", "XRPUSD.m", "ADAUSD.m", "DOTUSD.m", "XLMUSD.m", "KSMUSD.m", "SOLUSD.m", "TRXUSD.m", "UNIUSD.m", "AVAXUSD.m", "DOGEUSD.m", "LINKUSD.m", "MATICUSD.m"],
    "loader": {"tz": "Europe/Athens", "interval_hours": 1, "max_gap_days": 4, "trim_d1_prefix": true},
    "first_h1_at_or_before": "2021-01-01T00:00:00Z",
    "last_h1_at_or_after": "2026-08-24T00:00:00Z",
    "data_start": "2021-01-01T00:00:00Z",
    "data_end": "earliest_last_bar_across_eligible_coins",
    "minimum_n": null
  },
  "financing": {"primary_bps_per_night": 0.0, "basis": "account swap-free status (spec window + broker page)",
                "sensitivity": "standard_long_swap_points_22:00_server_weekdays_wednesday_triple",
                "sensitivity_role": "descriptive_only",
                "standard_long_swap_points": {"BTCUSD.m": -8466.6, "ETHUSD.m": -280.56, "LTCUSD.m": -10.632, "XRPUSD.m": -27.828, "BCHUSD.m": -39.228, "UNIUSD.m": -98.53, "AVAXUSD.m": -336, "DOGEUSD.m": -32.16, "LINKUSD.m": -19.68, "MATICUSD.m": -4.08}},
  "costs": {"spread_floor": "median_quoted_spread_across_market_watch_snapshots",
            "spread_floor_values": {"BCHUSD.m": 0.8000000000000114, "ETHUSD.m": 1.400000000000091, "LTCUSD.m": 1.4300000000000068, "XRPUSD.m": 0.010000000000000009, "ADAUSD.m": 0.0007000000000000339, "DOTUSD.m": 0.0050000000000001155, "XLMUSD.m": 0.0003999999999999837, "KSMUSD.m": 0.04999999999999982, "SOLUSD.m": 0.20999999999999375, "TRXUSD.m": 0.0005800000000000249, "UNIUSD.m": 0.010099999999999554, "AVAXUSD.m": 0.024200000000000443, "DOGEUSD.m": 0.0002400000000000041, "LINKUSD.m": 0.019999999999999574, "MATICUSD.m": 0.0005999999999999894}, "slippage_ratio_of_floor": 0.16666666666666666,
            "commission": 0.0, "stress_multiplier_includes_financing": true},
  "walkforward": {"windows": "unchanged", "common_origin": "2021-01-01T00:00:00Z", "selection": "per_coin_as_v1"},
  "primary": {"statistic": "pooled_mean_net_bps_after_financing", "clustered_t_min": 2.0,
              "cluster": "utc_entry_day", "drift_max_p": 0.05, "existing_walkforward_rules": "all"},
  "drift_control": {"spec": "drift_baseline_v1", "randomization_unit": "signal_timestamp_group",
                    "hour_matched": true, "repetitions": 500, "max_redraws": 20,
                    "gate_failure": "redraw_or_drop_whole_group", "re_detect_signals": false},
  "per_coin_results": "descriptive_only",
  "checkpoint4": {
    "eligible": ["ETHUSD.m", "LTCUSD.m", "XRPUSD.m"],
    "origin": "2021-01-01T00:00:00Z",
    "qualification_track": "deployed",
    "drift_track": "forced",
    "clustered_t_min": 2.0,
    "cluster": "utc_entry_day",
    "report_fields": ["trades", "unique_days", "windows", "raw_t_diagnostic", "clustered_t"],
    "drift": {"repetitions": 500, "p_denominator": 501, "max_redraws": 20, "max_p": 0.05,
              "group": "same_signal_timestamp", "hour_matched": true, "redraw_scope": "whole_group"},
    "financing_primary": 0.0,
    "financing_sensitivity": {"rollover_hour_server": 22, "weekdays_only": true, "triple_weekday": "wednesday",
                              "holding_interval": "entry_to_exit_plus_one_bar"},
    "strategy_computation_before_checkpoint4": false
  }
}
```
