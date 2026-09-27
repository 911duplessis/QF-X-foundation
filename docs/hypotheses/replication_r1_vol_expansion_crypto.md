# Replication R1: Volatility Expansion v1 (long) on the broker crypto universe

Status: **FROZEN** (all choices). Draft `4bb951a`; decisions D1 = keep and
D2 = yes made by the account owner on 2026-09-27.

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
2. It is not BTCUSD.m, the discovery symbol. **Decision D1 = keep:** BTC
   cross pairs (BTCEUR, BTCGBP, BTCJPY, BTCXAU) remain eligible, giving 19
   candidates.

   *Recorded dissent:* the crosses are BTC priced in other currencies over
   the discovery period, with ~95%+ correlated hourly moves. If they pass,
   the pooled result partly re-tests the discovery data. The research log
   must report the primary result both as specified and, descriptively,
   without the four crosses. The descriptive version has no qualification
   role.
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

Not yet received: BCHUSD.m, UNIUSD.m, BTCEUR.m, BTCGBP.m, BTCJPY.m, BTCXAU.m,
AVAXUSD.m, DOGEUSD.m, LINKUSD.m, MATICUSD.m.

**Export instruction for the remaining symbols:** export H1 from the earliest
date the terminal offers (not from 2021-01-01), so that condition 4 is tested
against the broker's full history and not against the chosen export start.

**Caveat on the three passing files:** they were exported starting exactly
at 2021-01-01 00:00 server time (= 2020-12-31 22:00 UTC), which satisfies
condition 4 by 2 hours. It shows the broker has H1 history at least that far
back. Whether it goes further back does not affect eligibility.

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
  "version": 1,
  "status": "frozen",
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
    "exclude_btc_base_asset": false,
    "descriptive_without_btc_crosses": true,
    "loader": {"tz": "Europe/Athens", "interval_hours": 1, "max_gap_days": 4, "trim_d1_prefix": true},
    "first_h1_at_or_before": "2021-01-01T00:00:00Z",
    "last_h1_at_or_after": "2026-08-24T00:00:00Z",
    "data_start": "2021-01-01T00:00:00Z",
    "data_end": "earliest_last_bar_across_eligible_coins",
    "minimum_n": null
  },
  "costs": {"spread_floor": "quoted_at_capture", "slippage_ratio_of_floor": 0.16666666666666666,
            "financing": "recorded_long_swap_per_rollover", "stress_multiplier_includes_financing": true},
  "walkforward": {"windows": "unchanged", "common_origin": "2021-01-01T00:00:00Z", "selection": "per_coin_as_v1"},
  "primary": {"statistic": "pooled_mean_net_bps_after_financing", "clustered_t_min": 2.0,
              "cluster": "utc_entry_day", "drift_max_p": 0.05, "existing_walkforward_rules": "all"},
  "drift_control": {"spec": "drift_baseline_v1", "randomization_unit": "signal_timestamp_group",
                    "hour_matched": true, "repetitions": 500, "max_redraws": 20,
                    "gate_failure": "redraw_or_drop_whole_group", "re_detect_signals": false},
  "per_coin_results": "descriptive_only"
}
```
