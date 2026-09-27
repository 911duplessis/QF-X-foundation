# Test ledger

Status: **living record**, updated in the same commit as each new result.
It is the single list of every **primary qualification test** run in this
project. It exists so that the multiple-testing history is explicit when the
next hypothesis is pre-registered.

- The ledger records; it never re-judges. Every verdict comes from its
  frozen specification and published result file.
- Figures are copied from the result files. `tests/test_ledger.py` fails if
  they drift.
- **Descriptive analyses are not tests** and are not counted: the power
  analysis, per-pair and long/short splits, financing sensitivities, the
  BTCUSD re-costing, and train/validation drift diagnostics.

## Tests run (17 primary tests; 0 qualified)

| # | test | pre-registration | qualified | forced trades | forced net bps | forced day-clustered t | drift p | resolution (bps) | grid |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `trend_continuation:BTCUSD` | none (grid fixed in code before the run; no frozen spec document) | no | 117 | -13.22 | -0.33 | - | 113.4 | 9 |
| 2 | `trend_continuation:EURUSD` | none (grid fixed in code before the run; no frozen spec document) | no | 89 | -7.59 | -1.24 | - | 17.5 | 9 |
| 3 | `trend_continuation:XAUUSD` | none (grid fixed in code before the run; no frozen spec document) | no | 104 | +9.22 | +0.43 | - | 61.1 | 9 |
| 4 | `sweep_reversal_long:BTCUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 285 | -13.87 | -1.26 | 0.878 | 31.3 | 8 |
| 5 | `sweep_reversal_long:EURUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 329 | -1.56 | -1.21 | 0.487 | 3.7 | 8 |
| 6 | `sweep_reversal_long:XAUUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 255 | -0.19 | -0.03 | 0.918 | 16.1 | 8 |
| 7 | `sweep_reversal_short:BTCUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 498 | -1.71 | -0.31 | 0.086 | 15.8 | 8 |
| 8 | `sweep_reversal_short:EURUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 482 | -1.88 | -1.70 | 0.617 | 3.1 | 8 |
| 9 | `sweep_reversal_short:XAUUSD` | `liquidity_sweep_reversal_v1.md`, frozen `604f63a` | no | 450 | -3.09 | -1.37 | 0.455 | 6.4 | 8 |
| 10 | `vol_expansion_long:BTCUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 211 | +15.85 | +1.59 | 0.044 | 28.3 | 8 |
| 11 | `vol_expansion_long:EURUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 225 | +0.67 | +0.30 | 0.200 | 6.3 | 8 |
| 12 | `vol_expansion_long:XAUUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 159 | +21.51 | +2.30 | 0.174 | 26.5 | 8 |
| 13 | `vol_expansion_short:BTCUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 189 | +7.12 | +0.63 | 0.132 | 32.3 | 8 |
| 14 | `vol_expansion_short:EURUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 207 | -1.53 | -0.65 | 0.539 | 6.7 | 8 |
| 15 | `vol_expansion_short:XAUUSD` | `volatility_expansion_v1.md`, frozen `5feeb35` | no | 189 | -11.69 | -2.19 | 0.836 | 15.3 | 8 |
| 16 | `replication_r1:ETH+LTC+XRP` | `replication_r1_vol_expansion_crypto.md` v2, frozen `28fe237` / checkpoint 4 `1b6fb6e` | no | 286 | -26.27 | -1.34 | 0.327 | 55.9 | 8 |
| 17 | `fx_session_persistence_v1:7 majors` | `fx_session_persistence_v1.md`, frozen `a624b64` | no | 1871 | -1.91 | -1.91 | 0.577 | 2.9 | 4 |

**Column definitions**
- **Forced:** the forced walk-forward track (always trades the
  validation-best cell), test segments, net of costs.
- **Day-clustered t:** net bps / day-clustered SE.
  - Tests 1-15: the SE is taken from `power_analysis.json` (published
    after the fact). Those tests' own qualification used the IID t.
  - Tests 16-17 used the clustered t for qualification.
- **Drift p:** the drift control on test segments. Tests 1-3 had no drift
  control.
- **Resolution:** 2.8416 x the day-clustered SE, i.e. the smallest true
  edge per trade with 80% power to reach t >= 2.
  - Tests 1-16: from `power_analysis.json`, computed after the results.
  - Test 17: the achieved resolution. Its pre-data design MDE was 2.51 bps.
- **Grid:** parameter cells searched per test. Selection happens inside the
  walk-forward, so this counts search, not additional tests.

**Nominal near-misses (none qualified; listed so they cannot be re-mined)**
- #10 BTCUSD vol expansion long: drift p 0.044. It failed the walk-forward
  rules, and Replication R1 (#16) then failed.
- #12 XAUUSD vol expansion long: forced clustered t +2.30, but the deployed
  track failed qualification and drift p was 0.174.
- #15 XAUUSD vol expansion short: forced clustered t -2.19, i.e. a significant
  **loss**. It is not an inverse-signal lead: reversing a failed hypothesis
  after seeing the data would be post-hoc.

## Data usage by series

Every test used the whole series shown (train, validation and test
segments). A later test on the same series is **not** independent of these.

| series | span used | tests | count |
|---|---|---|---|
| EURUSD (`data/mt5`, 2020-10 to 2026-09) and EURUSD.m (`fx_session_v1`, 2021-01 to 2026-09) | 2020-10-28 to 2026-09-25 | 2, 5, 8, 11, 14, 17 | **6** |
| XAUUSD | 2020-10-22 to 2026-09-04 | 3, 6, 9, 12, 15 | 5 |
| BTCUSD | 2020-12-02 to 2026-08-24 | 1, 4, 7, 10, 13 (+ R1 re-costing, descriptive) | 5 |
| ETHUSD.m, LTCUSD.m, XRPUSD.m | 2021-01-01 to 2026-09-27 | 16 | 1 |
| GBPUSD.m, USDJPY.m, USDCHF.m, AUDUSD.m, USDCAD.m, NZDUSD.m | 2021-01-04 to 2026-09-25 | 17 | 1 |

Also on record: EURUSD trend-continuation session breakdowns (disclosed in
spec 17), and the single-split trend baseline that preceded test 1
(`baseline_trend_continuation.md`, not a qualification test).

**Untouched by any test:**
- all history after the last bar used, which is **2026-09-25** for FX and
  gold and 2026-08-24 for BTCUSD;
- every broker symbol not listed above;
- all timeframes other than H1.

## Rule for future pre-registrations (adopted 2026-09-27)

Before a specification is frozen, it must contain a **ledger section** stating:

1. **Overlap:** which ledger tests used the same instrument series and period.
2. **Family size:** the number of prior ledger tests on overlapping data,
   plus this one.
3. **Adjustment:** how the overlap is handled, chosen before any data is
   read. It has to be one of:
   - a multiplicity-adjusted primary threshold (for example Bonferroni or
     Holm on the drift p across the stated family, or a higher t); or
   - a confirmatory design on data untouched by any ledger test (later
     history, or instruments not yet used), with the overlapping data used
     only for development.
4. The ledger row is added in the same commit as the result, whatever the
   verdict.

A test with no ledger section cannot be frozen.

## Machine-readable ledger

```json
{"tests": [
  {"id": "trend_continuation:BTCUSD", "hypothesis": "trend_continuation", "universe": ["BTCUSD"], "result_file": "docs/results/walkforward_trend_continuation.json", "qualified": false, "forced_trades": 117, "forced_net_bps": -13.22, "forced_t_day": -0.33, "drift_p": null, "design_mde_bps": 113.4, "grid": 9},
  {"id": "trend_continuation:EURUSD", "hypothesis": "trend_continuation", "universe": ["EURUSD"], "result_file": "docs/results/walkforward_trend_continuation.json", "qualified": false, "forced_trades": 89, "forced_net_bps": -7.59, "forced_t_day": -1.24, "drift_p": null, "design_mde_bps": 17.5, "grid": 9},
  {"id": "trend_continuation:XAUUSD", "hypothesis": "trend_continuation", "universe": ["XAUUSD"], "result_file": "docs/results/walkforward_trend_continuation.json", "qualified": false, "forced_trades": 104, "forced_net_bps": 9.22, "forced_t_day": 0.43, "drift_p": null, "design_mde_bps": 61.1, "grid": 9},
  {"id": "sweep_reversal_long:BTCUSD", "hypothesis": "sweep_reversal_long", "universe": ["BTCUSD"], "result_file": "docs/results/walkforward_sweep_reversal_long.json", "qualified": false, "forced_trades": 285, "forced_net_bps": -13.87, "forced_t_day": -1.26, "drift_p": 0.878, "design_mde_bps": 31.3, "grid": 8},
  {"id": "sweep_reversal_long:EURUSD", "hypothesis": "sweep_reversal_long", "universe": ["EURUSD"], "result_file": "docs/results/walkforward_sweep_reversal_long.json", "qualified": false, "forced_trades": 329, "forced_net_bps": -1.56, "forced_t_day": -1.21, "drift_p": 0.487, "design_mde_bps": 3.7, "grid": 8},
  {"id": "sweep_reversal_long:XAUUSD", "hypothesis": "sweep_reversal_long", "universe": ["XAUUSD"], "result_file": "docs/results/walkforward_sweep_reversal_long.json", "qualified": false, "forced_trades": 255, "forced_net_bps": -0.19, "forced_t_day": -0.03, "drift_p": 0.918, "design_mde_bps": 16.1, "grid": 8},
  {"id": "sweep_reversal_short:BTCUSD", "hypothesis": "sweep_reversal_short", "universe": ["BTCUSD"], "result_file": "docs/results/walkforward_sweep_reversal_short.json", "qualified": false, "forced_trades": 498, "forced_net_bps": -1.71, "forced_t_day": -0.31, "drift_p": 0.086, "design_mde_bps": 15.8, "grid": 8},
  {"id": "sweep_reversal_short:EURUSD", "hypothesis": "sweep_reversal_short", "universe": ["EURUSD"], "result_file": "docs/results/walkforward_sweep_reversal_short.json", "qualified": false, "forced_trades": 482, "forced_net_bps": -1.88, "forced_t_day": -1.7, "drift_p": 0.617, "design_mde_bps": 3.1, "grid": 8},
  {"id": "sweep_reversal_short:XAUUSD", "hypothesis": "sweep_reversal_short", "universe": ["XAUUSD"], "result_file": "docs/results/walkforward_sweep_reversal_short.json", "qualified": false, "forced_trades": 450, "forced_net_bps": -3.09, "forced_t_day": -1.37, "drift_p": 0.455, "design_mde_bps": 6.4, "grid": 8},
  {"id": "vol_expansion_long:BTCUSD", "hypothesis": "vol_expansion_long", "universe": ["BTCUSD"], "result_file": "docs/results/walkforward_vol_expansion_long.json", "qualified": false, "forced_trades": 211, "forced_net_bps": 15.85, "forced_t_day": 1.59, "drift_p": 0.044, "design_mde_bps": 28.3, "grid": 8},
  {"id": "vol_expansion_long:EURUSD", "hypothesis": "vol_expansion_long", "universe": ["EURUSD"], "result_file": "docs/results/walkforward_vol_expansion_long.json", "qualified": false, "forced_trades": 225, "forced_net_bps": 0.67, "forced_t_day": 0.3, "drift_p": 0.2, "design_mde_bps": 6.3, "grid": 8},
  {"id": "vol_expansion_long:XAUUSD", "hypothesis": "vol_expansion_long", "universe": ["XAUUSD"], "result_file": "docs/results/walkforward_vol_expansion_long.json", "qualified": false, "forced_trades": 159, "forced_net_bps": 21.51, "forced_t_day": 2.3, "drift_p": 0.174, "design_mde_bps": 26.5, "grid": 8},
  {"id": "vol_expansion_short:BTCUSD", "hypothesis": "vol_expansion_short", "universe": ["BTCUSD"], "result_file": "docs/results/walkforward_vol_expansion_short.json", "qualified": false, "forced_trades": 189, "forced_net_bps": 7.12, "forced_t_day": 0.63, "drift_p": 0.132, "design_mde_bps": 32.3, "grid": 8},
  {"id": "vol_expansion_short:EURUSD", "hypothesis": "vol_expansion_short", "universe": ["EURUSD"], "result_file": "docs/results/walkforward_vol_expansion_short.json", "qualified": false, "forced_trades": 207, "forced_net_bps": -1.53, "forced_t_day": -0.65, "drift_p": 0.539, "design_mde_bps": 6.7, "grid": 8},
  {"id": "vol_expansion_short:XAUUSD", "hypothesis": "vol_expansion_short", "universe": ["XAUUSD"], "result_file": "docs/results/walkforward_vol_expansion_short.json", "qualified": false, "forced_trades": 189, "forced_net_bps": -11.69, "forced_t_day": -2.19, "drift_p": 0.836, "design_mde_bps": 15.3, "grid": 8},
  {"id": "replication_r1:ETH+LTC+XRP", "hypothesis": "vol_expansion_long (replication)", "universe": ["ETHUSD.m", "LTCUSD.m", "XRPUSD.m"], "result_file": "docs/results/replication_r1.json", "qualified": false, "forced_trades": 286, "forced_net_bps": -26.27, "forced_t_day": -1.34, "drift_p": 0.327, "design_mde_bps": 55.9, "grid": 8},
  {"id": "fx_session_persistence_v1:7 majors", "hypothesis": "fx_session_persistence", "universe": ["EURUSD.m", "GBPUSD.m", "USDJPY.m", "USDCHF.m", "AUDUSD.m", "USDCAD.m", "NZDUSD.m"], "result_file": "docs/results/fx_session_persistence_v1.json", "qualified": false, "forced_trades": 1871, "forced_net_bps": -1.91, "forced_t_day": -1.91, "drift_p": 0.577, "design_mde_bps": 2.86, "grid": 4}
]}
```
