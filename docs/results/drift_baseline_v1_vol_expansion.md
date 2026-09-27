# Drift Baseline v1: timing-shuffled control for Volatility Expansion v1

Specification (frozen before implementation): `docs/hypotheses/drift_baseline_v1.md`. One-sided empirical randomization test, 500 hour-matched repetitions per window and segment, forced-track parameters. Statistic: mean net bps/trade; effect = observed - control mean; p = (1 + #{control >= observed}) / (N + 1). Total net bps is the secondary statistic. Long and short are separate hypotheses.

## Pre-registered answers

| direction | symbol | Q1 train (drift?) | Q2 test (timing edge?) | Q3 drift line: control test mean bps |
|---|---|---|---|---|
| long | BTCUSD | above band: timing had in-sample value | timing edge demonstrated (p <= 0.05; walk-forward rules still apply) | -3.41 |
| long | EURUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -0.98 |
| long | XAUUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | +13.64 |
| short | BTCUSD | above band: timing had in-sample value | no demonstrated timing edge | -6.21 |
| short | EURUSD | above band: timing had in-sample value | no demonstrated timing edge | -1.44 |
| short | XAUUSD | inside band: attributed to drift and geometry, not timing | no demonstrated timing edge | -6.09 |

## Pooled comparisons

| direction | symbol | segment | observed mean | trades | control mean | ctrl trades | difference | p | p (total) | ctrl p5 / p50 / p95 | observed pctl | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | BTCUSD | train | +32.54 | 257 | +4.05 | 297 | +28.49 | 0.020 | 0.034 | -18.87 / +4.47 / +25.01 | 98% | 1.6/358 |
| long | BTCUSD | validation | +21.38 | 170 | -1.06 | 189 | +22.45 | 0.040 | 0.048 | -22.34 / -1.59 / +18.63 | 96% | 0.0/237 |
| long | BTCUSD | test | +15.85 | 211 | -3.41 | 236 | +19.26 | 0.044 | 0.058 | -21.96 / -3.08 / +14.44 | 96% | 0.0/293 |
| long | EURUSD | train | -1.07 | 863 | -1.29 | 1033 | +0.22 | 0.445 | 0.369 | -3.46 / -1.30 / +0.61 | 56% | 0.0/1341 |
| long | EURUSD | validation | +0.37 | 220 | -0.74 | 254 | +1.12 | 0.325 | 0.337 | -4.31 / -0.72 / +2.95 | 68% | 0.0/324 |
| long | EURUSD | test | +0.67 | 225 | -0.98 | 261 | +1.64 | 0.200 | 0.228 | -4.19 / -1.06 / +2.41 | 80% | 0.0/337 |
| long | XAUUSD | train | +9.23 | 637 | +6.73 | 774 | +2.50 | 0.204 | 0.383 | +1.84 / +6.75 / +11.77 | 80% | 0.0/1032 |
| long | XAUUSD | validation | +23.98 | 164 | +17.34 | 206 | +6.63 | 0.184 | 0.417 | +5.87 / +17.86 / +29.48 | 82% | 0.0/285 |
| long | XAUUSD | test | +21.51 | 159 | +13.64 | 202 | +7.86 | 0.174 | 0.341 | -0.08 / +13.80 / +27.21 | 83% | 0.0/280 |
| short | BTCUSD | train | +12.13 | 227 | -23.89 | 269 | +36.01 | 0.006 | 0.008 | -45.06 / -23.94 / -0.82 | 100% | 1.0/309 |
| short | BTCUSD | validation | +8.46 | 153 | -12.16 | 169 | +20.62 | 0.060 | 0.064 | -33.29 / -12.30 / +9.10 | 94% | 0.0/201 |
| short | BTCUSD | test | +7.12 | 189 | -6.21 | 209 | +13.33 | 0.132 | 0.144 | -26.46 / -6.10 / +15.77 | 87% | 0.0/246 |
| short | EURUSD | train | +1.89 | 797 | -1.23 | 955 | +3.13 | 0.012 | 0.016 | -3.09 / -1.37 / +0.92 | 99% | 0.0/1275 |
| short | EURUSD | validation | -0.48 | 207 | -2.00 | 239 | +1.52 | 0.236 | 0.234 | -5.54 / -1.93 / +1.51 | 77% | 0.0/315 |
| short | EURUSD | test | -1.53 | 207 | -1.44 | 250 | -0.09 | 0.539 | 0.487 | -4.67 / -1.33 / +2.06 | 46% | 0.0/339 |
| short | XAUUSD | train | -1.01 | 850 | -4.15 | 977 | +3.15 | 0.064 | 0.054 | -7.29 / -4.20 / -0.86 | 94% | 0.0/1230 |
| short | XAUUSD | validation | -9.52 | 181 | -8.48 | 207 | -1.04 | 0.587 | 0.483 | -17.43 / -8.48 / +0.36 | 41% | 0.0/257 |
| short | XAUUSD | test | -11.69 | 189 | -6.09 | 209 | -5.60 | 0.836 | 0.784 | -16.91 / -5.89 / +3.44 | 16% | 0.0/255 |

## vol_expansion_long: per window (test segment)

| symbol | # | test period | params | observed mean | trades | control mean | difference | p | observed pctl |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 2023-06-02 to 2023-12-02 | box_bars=12 stop=box_mid target_r=2.0 | +8.31 | 29 | -3.24 | +11.56 | 0.295 | 71% |
| BTCUSD | 1 | 2023-12-02 to 2024-06-02 | box_bars=24 stop=box_mid target_r=1.0 | +38.06 | 30 | -1.05 | +39.11 | 0.144 | 86% |
| BTCUSD | 2 | 2024-06-02 to 2024-12-02 | box_bars=12 stop=box_mid target_r=1.0 | -4.72 | 55 | +5.97 | -10.70 | 0.735 | 27% |
| BTCUSD | 3 | 2024-12-02 to 2025-06-02 | box_bars=24 stop=box_mid target_r=2.0 | +28.83 | 27 | -2.61 | +31.44 | 0.204 | 80% |
| BTCUSD | 4 | 2025-06-02 to 2025-12-02 | box_bars=24 stop=box_mid target_r=2.0 | +27.73 | 39 | -4.27 | +31.99 | 0.074 | 93% |
| BTCUSD | 5 | 2025-12-02 to 2026-06-02 | box_bars=24 stop=box_opposite target_r=2.0 | +11.65 | 31 | -18.79 | +30.44 | 0.208 | 79% |
| EURUSD | 0 | 2023-04-28 to 2023-10-27 | box_bars=12 stop=box_mid target_r=1.0 | -1.49 | 64 | -2.15 | +0.66 | 0.383 | 62% |
| EURUSD | 1 | 2023-10-29 to 2024-04-26 | box_bars=24 stop=box_opposite target_r=2.0 | +7.08 | 20 | -0.79 | +7.87 | 0.136 | 87% |
| EURUSD | 2 | 2024-04-28 to 2024-10-28 | box_bars=12 stop=box_mid target_r=1.0 | -2.14 | 65 | -1.79 | -0.35 | 0.609 | 39% |
| EURUSD | 3 | 2024-10-28 to 2025-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | -2.89 | 16 | +4.95 | -7.84 | 0.739 | 26% |
| EURUSD | 4 | 2025-04-28 to 2025-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | +7.44 | 24 | +2.10 | +5.34 | 0.281 | 72% |
| EURUSD | 5 | 2025-10-28 to 2026-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | +23.46 | 14 | -2.42 | +25.88 | 0.004 | 100% |
| EURUSD | 6 | 2026-04-28 to 2026-09-04 | box_bars=24 stop=box_opposite target_r=2.0 | -9.90 | 22 | -3.20 | -6.70 | 0.844 | 16% |
| XAUUSD | 0 | 2023-04-23 to 2023-10-20 | box_bars=24 stop=box_mid target_r=2.0 | -17.62 | 20 | -4.03 | -13.59 | 0.850 | 15% |
| XAUUSD | 1 | 2023-10-22 to 2024-04-22 | box_bars=24 stop=box_mid target_r=2.0 | +10.90 | 17 | +13.84 | -2.93 | 0.563 | 44% |
| XAUUSD | 2 | 2024-04-22 to 2024-10-22 | box_bars=12 stop=box_mid target_r=2.0 | +10.91 | 51 | +5.96 | +4.94 | 0.218 | 78% |
| XAUUSD | 3 | 2024-10-22 to 2025-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | +50.07 | 21 | +34.45 | +15.62 | 0.216 | 79% |
| XAUUSD | 4 | 2025-04-22 to 2025-10-22 | box_bars=24 stop=box_opposite target_r=2.0 | +31.30 | 20 | +23.95 | +7.35 | 0.385 | 62% |
| XAUUSD | 5 | 2025-10-22 to 2026-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | +88.32 | 18 | +32.11 | +56.21 | 0.066 | 94% |
| XAUUSD | 6 | 2026-04-22 to 2026-09-04 | box_bars=24 stop=box_opposite target_r=2.0 | -19.72 | 12 | -16.03 | -3.68 | 0.529 | 47% |

## vol_expansion_short: per window (test segment)

| symbol | # | test period | params | observed mean | trades | control mean | difference | p | observed pctl |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 2023-06-02 to 2023-12-02 | box_bars=12 stop=box_mid target_r=2.0 | -21.77 | 16 | -27.99 | +6.23 | 0.437 | 56% |
| BTCUSD | 1 | 2023-12-02 to 2024-06-02 | box_bars=24 stop=box_mid target_r=2.0 | +23.43 | 21 | -14.99 | +38.42 | 0.200 | 80% |
| BTCUSD | 2 | 2024-06-02 to 2024-12-02 | box_bars=12 stop=box_mid target_r=1.0 | +5.36 | 49 | -16.04 | +21.40 | 0.120 | 88% |
| BTCUSD | 3 | 2024-12-02 to 2025-06-02 | box_bars=24 stop=box_mid target_r=1.0 | +5.92 | 43 | -0.05 | +5.97 | 0.425 | 58% |
| BTCUSD | 4 | 2025-06-02 to 2025-12-02 | box_bars=24 stop=box_mid target_r=2.0 | +35.51 | 28 | +0.35 | +35.16 | 0.154 | 85% |
| BTCUSD | 5 | 2025-12-02 to 2026-06-02 | box_bars=24 stop=box_mid target_r=2.0 | -9.70 | 32 | +11.52 | -21.22 | 0.741 | 26% |
| EURUSD | 0 | 2023-04-28 to 2023-10-27 | box_bars=12 stop=box_opposite target_r=1.0 | +3.87 | 48 | -0.18 | +4.06 | 0.144 | 86% |
| EURUSD | 1 | 2023-10-29 to 2024-04-26 | box_bars=12 stop=box_opposite target_r=1.0 | -8.44 | 48 | -1.65 | -6.79 | 0.992 | 1% |
| EURUSD | 2 | 2024-04-28 to 2024-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | +5.63 | 17 | -2.38 | +8.01 | 0.112 | 89% |
| EURUSD | 3 | 2024-10-28 to 2025-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | -3.49 | 17 | -2.10 | -1.39 | 0.537 | 46% |
| EURUSD | 4 | 2025-04-28 to 2025-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | -10.13 | 26 | -6.03 | -4.09 | 0.717 | 28% |
| EURUSD | 5 | 2025-10-28 to 2026-04-28 | box_bars=24 stop=box_mid target_r=2.0 | -0.54 | 23 | +2.93 | -3.47 | 0.737 | 26% |
| EURUSD | 6 | 2026-04-28 to 2026-09-04 | box_bars=24 stop=box_mid target_r=1.0 | +5.07 | 28 | -1.16 | +6.23 | 0.036 | 97% |
| XAUUSD | 0 | 2023-04-23 to 2023-10-20 | box_bars=12 stop=box_opposite target_r=1.0 | +0.34 | 43 | -0.05 | +0.39 | 0.493 | 51% |
| XAUUSD | 1 | 2023-10-22 to 2024-04-22 | box_bars=12 stop=box_opposite target_r=1.0 | -12.63 | 34 | -10.36 | -2.27 | 0.613 | 39% |
| XAUUSD | 2 | 2024-04-22 to 2024-10-22 | box_bars=24 stop=box_opposite target_r=1.0 | -17.58 | 11 | -21.72 | +4.14 | 0.437 | 56% |
| XAUUSD | 3 | 2024-10-22 to 2025-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | -17.77 | 12 | -23.50 | +5.74 | 0.403 | 60% |
| XAUUSD | 4 | 2025-04-22 to 2025-10-22 | box_bars=24 stop=box_mid target_r=2.0 | -13.51 | 25 | -8.05 | -5.45 | 0.609 | 39% |
| XAUUSD | 5 | 2025-10-22 to 2026-04-22 | box_bars=12 stop=box_mid target_r=2.0 | -51.08 | 25 | -3.89 | -47.19 | 0.966 | 3% |
| XAUUSD | 6 | 2026-04-22 to 2026-09-04 | box_bars=12 stop=box_mid target_r=1.0 | +5.82 | 39 | +2.97 | +2.85 | 0.425 | 58% |
