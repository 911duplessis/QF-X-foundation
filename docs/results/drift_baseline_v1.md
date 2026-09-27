# Drift Baseline v1: timing-shuffled control for Liquidity Sweep Reversal v1

Specification (frozen before implementation): `docs/hypotheses/drift_baseline_v1.md`. One-sided empirical randomization test, 500 hour-matched repetitions per window and segment, forced-track parameters. Statistic: mean net bps/trade; effect = observed - control mean; p = (1 + #{control >= observed}) / (N + 1). Total net bps is the secondary statistic. Long and short are separate hypotheses.

## Pre-registered answers

| direction | symbol | Q1 train (drift?) | Q2 test (timing edge?) | Q3 drift line: control test mean bps |
|---|---|---|---|---|
| long | BTCUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -2.18 |
| long | EURUSD | above band: timing had in-sample value | no demonstrated timing edge | -1.55 |
| long | XAUUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | +6.64 |
| short | BTCUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -9.90 |
| short | EURUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -1.58 |
| short | XAUUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -3.40 |

## Pooled comparisons

| direction | symbol | segment | observed mean | trades | control mean | ctrl trades | difference | p | p (total) | ctrl p5 / p50 / p95 | observed pctl | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | BTCUSD | train | +4.66 | 549 | -4.53 | 530 | +9.19 | 0.178 | 0.178 | -21.11 / -4.42 / +13.00 | 82% | 1.1/683 |
| long | BTCUSD | validation | +0.35 | 261 | -1.08 | 248 | +1.43 | 0.421 | 0.421 | -19.43 / -1.83 / +17.68 | 58% | 0.0/314 |
| long | BTCUSD | test | -13.87 | 285 | -2.18 | 277 | -11.69 | 0.878 | 0.882 | -18.50 / -2.28 / +14.48 | 12% | 0.0/345 |
| long | EURUSD | train | +1.17 | 1292 | -1.38 | 1243 | +2.55 | 0.004 | 0.004 | -2.63 / -1.36 / -0.19 | 100% | 0.0/1418 |
| long | EURUSD | validation | +1.46 | 328 | -1.19 | 322 | +2.65 | 0.020 | 0.020 | -3.22 / -1.24 / +0.88 | 98% | 0.0/368 |
| long | EURUSD | test | -1.56 | 329 | -1.55 | 315 | -0.00 | 0.487 | 0.511 | -3.56 / -1.61 / +0.51 | 51% | 0.0/363 |
| long | XAUUSD | train | +2.42 | 1131 | +2.55 | 1071 | -0.13 | 0.547 | 0.523 | -0.43 / +2.63 / +5.46 | 45% | 0.0/1333 |
| long | XAUUSD | validation | +4.19 | 278 | +6.70 | 268 | -2.50 | 0.683 | 0.673 | -0.39 / +6.79 / +13.55 | 32% | 0.0/330 |
| long | XAUUSD | test | -0.19 | 255 | +6.64 | 244 | -6.84 | 0.918 | 0.918 | -1.68 / +6.56 / +15.50 | 8% | 0.0/298 |
| short | BTCUSD | train | -9.39 | 755 | -17.97 | 688 | +8.58 | 0.082 | 0.098 | -28.38 / -17.88 / -7.92 | 92% | 3.7/849 |
| short | BTCUSD | validation | -14.41 | 347 | -13.16 | 325 | -1.25 | 0.591 | 0.615 | -25.65 / -12.83 / -2.14 | 41% | 0.0/389 |
| short | BTCUSD | test | -1.71 | 498 | -9.90 | 454 | +8.19 | 0.086 | 0.092 | -18.98 / -9.89 / +0.20 | 92% | 0.0/555 |
| short | EURUSD | train | -1.00 | 1969 | -1.49 | 1883 | +0.49 | 0.200 | 0.224 | -2.38 / -1.49 / -0.52 | 80% | 0.0/2389 |
| short | EURUSD | validation | -1.84 | 512 | -1.74 | 487 | -0.09 | 0.531 | 0.573 | -3.34 / -1.75 / -0.07 | 47% | 0.0/626 |
| short | EURUSD | test | -1.88 | 482 | -1.58 | 452 | -0.29 | 0.617 | 0.665 | -3.12 / -1.61 / +0.02 | 38% | 0.0/584 |
| short | XAUUSD | train | -1.52 | 1914 | -2.75 | 1886 | +1.23 | 0.070 | 0.070 | -4.24 / -2.71 / -1.40 | 93% | 0.0/2162 |
| short | XAUUSD | validation | -6.52 | 476 | -4.09 | 475 | -2.43 | 0.902 | 0.902 | -7.27 / -4.10 / -0.74 | 10% | 0.0/540 |
| short | XAUUSD | test | -3.09 | 450 | -3.40 | 452 | +0.31 | 0.455 | 0.449 | -7.30 / -3.33 / +0.25 | 55% | 0.0/514 |

## sweep_reversal_long: per window (test segment)

| symbol | # | test period | params | observed mean | trades | control mean | difference | p | observed pctl |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 2023-06-02 to 2023-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | -7.11 | 34 | +6.16 | -13.28 | 0.675 | 33% |
| BTCUSD | 1 | 2023-12-02 to 2024-06-02 | swing_lookback=5 confirmation=structure target_r=2.0 | +32.43 | 33 | +2.78 | +29.64 | 0.206 | 80% |
| BTCUSD | 2 | 2024-06-02 to 2024-12-02 | swing_lookback=5 confirmation=none target_r=2.0 | -35.71 | 79 | +5.53 | -41.23 | 0.998 | 0% |
| BTCUSD | 3 | 2024-12-02 to 2025-06-02 | swing_lookback=3 confirmation=structure target_r=1.0 | -17.47 | 47 | -9.11 | -8.35 | 0.651 | 35% |
| BTCUSD | 4 | 2025-06-02 to 2025-12-02 | swing_lookback=3 confirmation=structure target_r=2.0 | +0.78 | 44 | -2.57 | +3.36 | 0.439 | 56% |
| BTCUSD | 5 | 2025-12-02 to 2026-06-02 | swing_lookback=3 confirmation=structure target_r=2.0 | -24.47 | 48 | -16.28 | -8.19 | 0.633 | 37% |
| EURUSD | 0 | 2023-04-28 to 2023-10-27 | swing_lookback=5 confirmation=structure target_r=2.0 | -9.92 | 18 | -2.95 | -6.97 | 0.804 | 20% |
| EURUSD | 1 | 2023-10-29 to 2024-04-26 | swing_lookback=5 confirmation=none target_r=2.0 | +2.05 | 58 | -0.85 | +2.90 | 0.118 | 88% |
| EURUSD | 2 | 2024-04-28 to 2024-10-28 | swing_lookback=5 confirmation=structure target_r=2.0 | -10.29 | 27 | -0.40 | -9.89 | 0.964 | 4% |
| EURUSD | 3 | 2024-10-28 to 2025-04-28 | swing_lookback=5 confirmation=none target_r=2.0 | +2.75 | 50 | -0.23 | +2.98 | 0.267 | 73% |
| EURUSD | 4 | 2025-04-28 to 2025-10-28 | swing_lookback=5 confirmation=none target_r=1.0 | +0.35 | 64 | -1.46 | +1.81 | 0.224 | 78% |
| EURUSD | 5 | 2025-10-28 to 2026-04-28 | swing_lookback=5 confirmation=none target_r=2.0 | -2.94 | 67 | -3.09 | +0.15 | 0.455 | 55% |
| EURUSD | 6 | 2026-04-28 to 2026-09-04 | swing_lookback=5 confirmation=none target_r=1.0 | -3.05 | 45 | -1.83 | -1.22 | 0.780 | 22% |
| XAUUSD | 0 | 2023-04-23 to 2023-10-20 | swing_lookback=5 confirmation=none target_r=1.0 | -6.22 | 55 | -2.72 | -3.50 | 0.812 | 19% |
| XAUUSD | 1 | 2023-10-22 to 2024-04-22 | swing_lookback=5 confirmation=structure target_r=2.0 | -11.93 | 21 | +13.48 | -25.41 | 0.946 | 5% |
| XAUUSD | 2 | 2024-04-22 to 2024-10-22 | swing_lookback=3 confirmation=structure target_r=2.0 | -0.71 | 33 | +14.21 | -14.92 | 0.854 | 15% |
| XAUUSD | 3 | 2024-10-22 to 2025-04-22 | swing_lookback=3 confirmation=structure target_r=2.0 | +40.60 | 22 | +24.51 | +16.09 | 0.182 | 82% |
| XAUUSD | 4 | 2025-04-22 to 2025-10-22 | swing_lookback=3 confirmation=structure target_r=2.0 | -0.13 | 28 | +10.58 | -10.71 | 0.701 | 30% |
| XAUUSD | 5 | 2025-10-22 to 2026-04-22 | swing_lookback=3 confirmation=none target_r=2.0 | +9.53 | 75 | +7.14 | +2.39 | 0.423 | 58% |
| XAUUSD | 6 | 2026-04-22 to 2026-09-04 | swing_lookback=3 confirmation=structure target_r=2.0 | -49.40 | 21 | -8.43 | -40.97 | 0.958 | 4% |

## sweep_reversal_short: per window (test segment)

| symbol | # | test period | params | observed mean | trades | control mean | difference | p | observed pctl |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 2023-06-02 to 2023-12-02 | swing_lookback=3 confirmation=none target_r=1.0 | -15.12 | 107 | -21.54 | +6.42 | 0.220 | 78% |
| BTCUSD | 1 | 2023-12-02 to 2024-06-02 | swing_lookback=5 confirmation=none target_r=1.0 | -9.84 | 87 | -11.76 | +1.92 | 0.453 | 55% |
| BTCUSD | 2 | 2024-06-02 to 2024-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | +30.46 | 37 | -25.58 | +56.03 | 0.050 | 95% |
| BTCUSD | 3 | 2024-12-02 to 2025-06-02 | swing_lookback=3 confirmation=none target_r=1.0 | +4.21 | 148 | -5.98 | +10.20 | 0.140 | 86% |
| BTCUSD | 4 | 2025-06-02 to 2025-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | +55.83 | 32 | -1.70 | +57.53 | 0.042 | 96% |
| BTCUSD | 5 | 2025-12-02 to 2026-06-02 | swing_lookback=5 confirmation=none target_r=2.0 | -21.99 | 87 | +2.07 | -24.07 | 0.968 | 3% |
| EURUSD | 0 | 2023-04-28 to 2023-10-27 | swing_lookback=5 confirmation=structure target_r=1.0 | -1.32 | 21 | -0.09 | -1.24 | 0.571 | 43% |
| EURUSD | 1 | 2023-10-29 to 2024-04-26 | swing_lookback=3 confirmation=none target_r=2.0 | -3.41 | 95 | -1.56 | -1.86 | 0.830 | 17% |
| EURUSD | 2 | 2024-04-28 to 2024-10-28 | swing_lookback=3 confirmation=none target_r=2.0 | -0.46 | 94 | -1.29 | +0.82 | 0.319 | 68% |
| EURUSD | 3 | 2024-10-28 to 2025-04-28 | swing_lookback=3 confirmation=none target_r=2.0 | -3.15 | 92 | -3.50 | +0.35 | 0.481 | 52% |
| EURUSD | 4 | 2025-04-28 to 2025-10-28 | swing_lookback=3 confirmation=none target_r=2.0 | -0.89 | 81 | -1.94 | +1.04 | 0.345 | 66% |
| EURUSD | 5 | 2025-10-28 to 2026-04-28 | swing_lookback=3 confirmation=structure target_r=1.0 | -0.84 | 36 | +1.55 | -2.39 | 0.713 | 29% |
| EURUSD | 6 | 2026-04-28 to 2026-09-04 | swing_lookback=3 confirmation=none target_r=2.0 | -1.84 | 63 | -0.95 | -0.89 | 0.695 | 31% |
| XAUUSD | 0 | 2023-04-23 to 2023-10-20 | swing_lookback=3 confirmation=none target_r=2.0 | +3.77 | 86 | -1.65 | +5.43 | 0.062 | 94% |
| XAUUSD | 1 | 2023-10-22 to 2024-04-22 | swing_lookback=5 confirmation=none target_r=1.0 | -7.32 | 50 | -4.65 | -2.67 | 0.703 | 30% |
| XAUUSD | 2 | 2024-04-22 to 2024-10-22 | swing_lookback=3 confirmation=none target_r=1.0 | -5.69 | 84 | -5.67 | -0.03 | 0.511 | 49% |
| XAUUSD | 3 | 2024-10-22 to 2025-04-22 | swing_lookback=5 confirmation=none target_r=1.0 | -5.31 | 58 | -5.58 | +0.27 | 0.473 | 53% |
| XAUUSD | 4 | 2025-04-22 to 2025-10-22 | swing_lookback=5 confirmation=none target_r=1.0 | -8.49 | 49 | -4.89 | -3.59 | 0.697 | 30% |
| XAUUSD | 5 | 2025-10-22 to 2026-04-22 | swing_lookback=3 confirmation=none target_r=1.0 | -3.73 | 79 | -3.34 | -0.39 | 0.529 | 47% |
| XAUUSD | 6 | 2026-04-22 to 2026-09-04 | swing_lookback=5 confirmation=none target_r=1.0 | +3.33 | 44 | +3.58 | -0.25 | 0.519 | 48% |
