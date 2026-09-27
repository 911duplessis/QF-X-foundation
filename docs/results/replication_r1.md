# Replication R1: Volatility Expansion v1 (long) on ETHUSD, LTCUSD, XRPUSD

Specification (frozen, v2): `docs/hypotheses/replication_r1_vol_expansion_crypto.md`. Universe N = 3 by the pre-registered eligibility rule. Common window origin 2021-01-01 UTC; 24M/6M/6M, 6M step; per-coin parameter selection as v1; financing 0 (swap-free).

## Primary outcome: **NOT REPLICATED**

Failures: pooled test net <= 0; negative at 2x costs; profitable windows 25% < 60%; median window net <= 0; windows surviving stress 0% < 60%; day-clustered t -0.59 < 2.0; block drift p 0.327 > 0.05

## Pooled test sample and clustering

| track | trades | unique calendar days | test windows | mean net bps | raw trade-level t (diagnostic) | day-clustered t (qualification) |
|---|---|---|---|---|---|---|
| deployed | 122 | 119 | 4 | -15.78 | -0.59 | -0.59 |
| forced | 286 | 244 | 6 | -26.27 | -1.45 | -1.34 |

## Walk-forward stability (pooled across coins, window by window)

| track | windows | traded | abstained | profitable | median bps | worst bps | dispersion | survive 2x | concentration | pooled trades | pooled net | pooled 2x net | pooled validation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 4 | 2 | 25% | -16.3 | -31.0 | 11.7 | 0% | - | 122 | -15.78 | -19.83 | +16.28 |
| forced | 6 | 6 | 0 | 17% | -19.8 | -51.1 | 19.4 | 0% | - | 286 | -26.27 | -39.42 | -5.76 |

## Block-randomized drift control (forced track, test segments)

| observed mean | control mean | difference | p | p (total) | control p5 / p50 / p95 | observed percentile | trades obs / ctrl | groups | mean dropped groups |
|---|---|---|---|---|---|---|---|---|---|
| -26.27 | -32.85 | +6.58 | 0.327 | 0.253 | -62.33 / -32.52 / -0.80 | 67% | 286 / 339 | 422 | 0.37 |

- train (selection-biased, not evidence): observed +23.33, control -11.85, p 0.002
- validation (selection-biased, not evidence): observed -5.76, control -18.47, p 0.251

## Windows (pooled test, deployed track)

| # | test period | params per coin | coins deployed | trades | net bps | block drift p |
|---|---|---|---|---|---|---|
| 0 | 2023-07-01 to 2023-12-31 | ETHUSD: 24/box_mid/2.0; LTCUSD: 12/box_mid/2.0; XRPUSD: 12/box_mid/2.0 | 1/3 | 31 | -11.66 | 0.645 |
| 1 | 2024-01-01 to 2024-06-30 | ETHUSD: 24/box_opposite/2.0; LTCUSD: 12/box_mid/1.0; XRPUSD: 12/box_mid/2.0 | 1/3 | 31 | +0.83 | 0.519 |
| 2 | 2024-07-01 to 2024-12-31 | ETHUSD: 12/box_mid/2.0; LTCUSD: 12/box_mid/1.0; XRPUSD: 12/box_opposite/1.0 | 0/3 | 0 | +0.00 | 0.752 |
| 3 | 2025-01-01 to 2025-06-30 | ETHUSD: 24/box_opposite/2.0; LTCUSD: 12/box_opposite/1.0; XRPUSD: 12/box_opposite/1.0 | 1/3 | 27 | -20.94 | 0.383 |
| 4 | 2025-07-01 to 2025-12-31 | ETHUSD: 24/box_opposite/2.0; LTCUSD: 12/box_mid/2.0; XRPUSD: 24/box_opposite/1.0 | 0/3 | 0 | +0.00 | 0.635 |
| 5 | 2026-01-01 to 2026-06-30 | ETHUSD: 24/box_opposite/1.0; LTCUSD: 24/box_mid/2.0; XRPUSD: 24/box_opposite/1.0 | 1/3 | 33 | -31.03 | 0.038 |

## Per coin (descriptive only; no qualification role)

| coin | forced test trades | net bps | t (IID) | profitable windows | deployed windows | 2x net |
|---|---|---|---|---|---|---|
| ETHUSD.m | 190 | -20.39 | -1.03 | 17% | 4/6 | -23.78 |
| LTCUSD.m | 5 | -103.11 | -0.34 | 50% | 0/6 | +0.00 |
| XRPUSD.m | 91 | -34.32 | -0.94 | 25% | 0/6 | -109.62 |

## Financing sensitivity (descriptive only)

Primary uses financing = 0 (swap-free). Standard swaps: long points/night at 22:00 server, weekdays, Wednesday x3.

| track | coin | trades | net bps swap-free | net bps standard swaps |
|---|---|---|---|---|
| deployed | ETHUSD.m | 122 | -15.78 | -24.07 |
| deployed | LTCUSD.m | 0 | +0.00 | +0.00 |
| deployed | XRPUSD.m | 0 | +0.00 | +0.00 |
| deployed | pooled | 122 | -15.78 | -24.07 |
| forced | ETHUSD.m | 190 | -20.39 | -27.79 |
| forced | LTCUSD.m | 5 | -103.11 | -111.28 |
| forced | XRPUSD.m | 91 | -34.32 | -45.33 |
| forced | pooled | 286 | -26.27 | -34.83 |

**BTCUSD v1 candidate re-costed (forced test, diagnostic only):** 211 trades, +15.85 bps swap-free vs +9.91 bps at standard swaps.

Data: ETHUSD.m 50194 bars, 2021-01-01 00:00 to 2026-09-26 21:00 UTC; LTCUSD.m 50198 bars, 2021-01-01 00:00 to 2026-09-26 21:00 UTC; XRPUSD.m 50198 bars, 2021-01-01 00:00 to 2026-09-26 21:00 UTC
