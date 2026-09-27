# FX Session Directional Persistence v1 (seven USD majors, H1)

Specification (frozen before this run): `docs/hypotheses/fx_session_persistence_v1.md`. Common origin 2021-01-04 UTC; 24M/6M/6M, 6M step; parameters selected jointly across pairs; commission 0; financing 0 (no position crosses rollover).

## Primary outcome: **NOT QUALIFIED**

Failures: no traded test windows; day-clustered t +0.00 < 2.0; block drift p 0.577 > 0.05

## Pooled test sample and clustering

| track | trades | unique calendar days | test windows | mean net bps | raw trade-level t (diagnostic) | day-clustered t (qualification) | achieved resolution (bps) |
|---|---|---|---|---|---|---|---|
| deployed | 0 | 0 | 0 | +0.00 | +0.00 | +0.00 | - |
| forced | 1871 | 609 | 6 | -1.91 | -2.83 | -1.91 | 2.86 |

Achieved resolution = 2.8416 x clustered SE; descriptive only (design MDE was 2.51 bps central).

## Walk-forward stability (pooled across pairs)

| track | windows | traded | abstained | profitable | median bps | worst bps | dispersion | survive 2x | concentration | pooled trades | pooled net | pooled 2x net | pooled validation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 0 | 6 | 0% | +0.0 | +0.0 | 0.0 | 0% | - | 0 | +0.00 | +0.00 | +0.00 |
| forced | 6 | 6 | 0 | 0% | -1.2 | -4.2 | 1.6 | 0% | - | 1871 | -1.91 | -3.82 | -1.88 |

## Block-randomized drift control (forced track, test segments)

| observed mean | control mean | difference | p | p (total) | control p5 / p50 / p95 | observed percentile | trades obs / ctrl | groups | mean dropped groups |
|---|---|---|---|---|---|---|---|---|---|
| -1.91 | -1.77 | -0.14 | 0.577 | 0.577 | -3.29 / -1.75 / -0.24 | 42% | 1871 / 1871 | 609 | 0.00 |

- train (selection-biased, not evidence): observed -1.02, control -1.32, p 0.311
- validation (selection-biased, not evidence): observed -1.88, control -1.52, p 0.647

## Windows (joint selection; pooled test)

| # | test period | K / theta | train survivors | deployed | val net | test trades | net bps | 2x net | block drift p |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-07-04 to 2024-01-03 | 2 / 0.5 | 0 | no (no candidate passed train screen) | -4.41 | 449 | -0.94 | -2.86 | 0.313 |
| 1 | 2024-01-04 to 2024-07-03 | 2 / 0.5 | 0 | no (no candidate passed train screen) | -0.94 | 419 | -0.43 | -2.31 | 0.375 |
| 2 | 2024-07-04 to 2025-01-03 | 2 / 0.5 | 0 | no (no candidate passed train screen) | -0.43 | 435 | -4.19 | -6.10 | 0.836 |
| 3 | 2025-01-05 to 2025-07-03 | 1 / 1.0 | 1 | no (validation net <= 0) | -0.94 | 215 | -0.60 | -2.54 | 0.393 |
| 4 | 2025-07-04 to 2026-01-02 | 1 / 1.0 | 0 | no (no candidate passed train screen) | -0.60 | 201 | -4.07 | -5.99 | 0.824 |
| 5 | 2026-01-04 to 2026-07-03 | 2 / 1.0 | 0 | no (no candidate passed train screen) | -3.61 | 152 | -1.37 | -3.23 | 0.449 |

## Descriptive only (deployed track; no qualification role)

| group | trades | unique days | mean net bps | raw t | clustered t |
|---|---|---|---|---|---|
| long | 0 | 0 | +0.00 | +0.00 | +0.00 |
| short | 0 | 0 | +0.00 | +0.00 | +0.00 |
| EURUSD.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| GBPUSD.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| USDJPY.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| USDCHF.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| AUDUSD.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| USDCAD.m | 0 | 0 | +0.00 | +0.00 | +0.00 |
| NZDUSD.m | 0 | 0 | +0.00 | +0.00 | +0.00 |

Exit reasons: {}. Late time exits: 0. Signal days: 0; mean signalling pairs per signal day: 0.00 (power assumption: k = 7 x 0.40 = 2.8 per day).

## Descriptive only (forced track; no qualification role)

| group | trades | unique days | mean net bps | raw t | clustered t |
|---|---|---|---|---|---|
| long | 963 | 486 | -2.54 | -2.82 | -2.17 |
| short | 908 | 474 | -1.25 | -1.23 | -0.96 |
| EURUSD.m | 309 | 309 | +0.01 | +0.00 | +0.00 |
| GBPUSD.m | 311 | 311 | -0.22 | -0.14 | -0.14 |
| USDJPY.m | 247 | 247 | +1.09 | +0.51 | +0.51 |
| USDCHF.m | 296 | 296 | -2.67 | -1.62 | -1.62 |
| AUDUSD.m | 240 | 240 | -3.14 | -1.36 | -1.36 |
| USDCAD.m | 228 | 228 | -4.39 | -3.69 | -3.69 |
| NZDUSD.m | 240 | 240 | -5.17 | -2.50 | -2.50 |

Exit reasons: {'time': 1176, 'stop': 695}. Late time exits: 0. Signal days: 609; mean signalling pairs per signal day: 3.07 (power assumption: k = 7 x 0.40 = 2.8 per day).

Data: EURUSD.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; GBPUSD.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; USDJPY.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; USDCHF.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; AUDUSD.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; USDCAD.m 35709 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC; NZDUSD.m 35708 bars, 2021-01-04 00:00 to 2026-09-25 20:00 UTC
