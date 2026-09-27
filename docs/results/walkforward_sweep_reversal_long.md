# Walk-forward: sweep_reversal_long (H1)

Specification (frozen before this run): `docs/hypotheses/liquidity_sweep_reversal_v1.md`.

Windows: 24m train -> 6m validation -> 6m test, step 6m. Train screen: >= 30 trades and net > 0. Validation selects (>= 5 trades, net > 0, else abstain). Grid: 8 parameter sets. Machine-readable results in the matching `.json` file.

Qualification (deployed track): pooled validation > 0; pooled test > 0 with >= 30 trades and t >= 2.0; positive at 2x costs; >= 60% of traded test windows profitable; median window > 0; >= 60% of windows positive at 2x costs; no window > 50% of pooled P&L.

| symbol | deployed qualified | forced qualified | deployed failures |
|---|---|---|---|
| BTCUSD | NO | NO | pooled test net <= 0; test t -1.84 < 2.0; negative at 2x costs; profitable windows 33% < 60%; median window net <= 0; windows surviving stress 0% < 60% |
| EURUSD | NO | NO | pooled test net <= 0; test t -1.30 < 2.0; negative at 2x costs; profitable windows 40% < 60%; median window net <= 0; windows surviving stress 20% < 60% |
| XAUUSD | NO | NO | pooled test net <= 0; test t -1.15 < 2.0; negative at 2x costs; profitable windows 0% < 60%; median window net <= 0; windows surviving stress 0% < 60% |

## BTCUSD

Data: 50058 bars, 2020-12-02 to 2026-08-24 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 3 | 3 | 33% | -24.5 | -35.7 | -2821 | 15.3 | 36.5 | 0% | - | 171 | -23.2 | -1.84 | -27.1 | -0.21 |
| forced | 6 | 6 | 0 | 33% | -12.3 | -35.7 | -2821 | 21.8 | 36.0 | 17% | - | 285 | -13.9 | -1.27 | -18.6 | -0.14 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-06-02 to 2023-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | 0 | no (no candidate passed train screen) | +0.0 | 34 | -7.1 | +0.01 | 41% | 166 | 128 | 0.91 | -0.24 | 1176 | 13.6 | -14.9 |
| 1 | 2023-12-02 to 2024-06-02 | swing_lookback=5 confirmation=structure target_r=2.0 | 0 | no (no candidate passed train screen) | -7.1 | 33 | +32.4 | +0.12 | 52% | 249 | 198 | 1.34 | +0.67 | 1248 | 7.5 | +23.8 |
| 2 | 2024-06-02 to 2024-12-02 | swing_lookback=5 confirmation=none target_r=2.0 | 2 | yes | +2.4 | 79 | -35.7 | -0.34 | 24% | 177 | 103 | 0.54 | -2.36 | 3232 | 6.4 | -42.1 |
| 3 | 2024-12-02 to 2025-06-02 | swing_lookback=3 confirmation=structure target_r=1.0 | 5 | no (validation net <= 0) | -5.1 | 47 | -17.5 | -0.18 | 43% | 156 | 146 | 0.79 | -0.69 | 1744 | 4.3 | -20.3 |
| 4 | 2025-06-02 to 2025-12-02 | swing_lookback=3 confirmation=structure target_r=2.0 | 3 | yes | +7.3 | 44 | +0.8 | -0.01 | 41% | 165 | 113 | 1.01 | +0.03 | 1633 | 3.7 | -1.6 |
| 5 | 2025-12-02 to 2026-06-02 | swing_lookback=3 confirmation=structure target_r=2.0 | 2 | yes | +0.8 | 48 | -24.5 | -0.15 | 38% | 189 | 153 | 0.74 | -0.81 | 2110 | 5.1 | -28.0 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 74 | +0.7 | +54 |
| session | late | 37 | -38.0 | -1405 |
| session | london | 38 | -20.1 | -762 |
| session | new_york | 84 | -25.3 | -2128 |
| session | overlap | 52 | +5.5 | +288 |
| vol_regime | high | 36 | +15.8 | +570 |
| vol_regime | low | 152 | -18.6 | -2823 |
| vol_regime | normal | 97 | -17.5 | -1700 |
| trend_regime | ranging | 222 | -17.2 | -3823 |
| trend_regime | trending | 63 | -2.1 | -130 |
| exit | end_of_data | 1 | +56.1 | +56 |
| exit | stop | 162 | -135.9 | -22010 |
| exit | target | 65 | +208.5 | +13553 |
| exit | time | 57 | +78.0 | +4447 |

## EURUSD

Data: 36445 bars, 2020-10-28 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 5 | 2 | 40% | -2.9 | -10.3 | -278 | 5.3 | 11.7 | 20% | - | 226 | -2.2 | -1.30 | -3.8 | -0.12 |
| forced | 7 | 7 | 0 | 43% | -2.9 | -10.3 | -278 | 4.9 | 12.0 | 29% | - | 329 | -1.6 | -1.21 | -3.0 | -0.10 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-28 to 2023-10-27 | swing_lookback=5 confirmation=structure target_r=2.0 | 2 | yes | +10.7 | 18 | -9.9 | -0.34 | 28% | 39 | 29 | 0.52 | -1.27 | 214 | 1.3 | -11.0 |
| 1 | 2023-10-29 to 2024-04-26 | swing_lookback=5 confirmation=none target_r=2.0 | 4 | no (validation net <= 0) | -4.6 | 58 | +2.1 | +0.16 | 41% | 25 | 14 | 1.25 | +0.73 | 155 | 1.3 | +1.4 |
| 2 | 2024-04-28 to 2024-10-28 | swing_lookback=5 confirmation=structure target_r=2.0 | 2 | yes | +12.3 | 27 | -10.3 | -0.41 | 22% | 38 | 24 | 0.45 | -1.90 | 278 | 1.3 | -11.4 |
| 3 | 2024-10-28 to 2025-04-28 | swing_lookback=5 confirmation=none target_r=2.0 | 3 | yes | +1.4 | 50 | +2.8 | +0.07 | 38% | 41 | 21 | 1.21 | +0.59 | 158 | 1.3 | +0.8 |
| 4 | 2025-04-28 to 2025-10-28 | swing_lookback=5 confirmation=none target_r=1.0 | 3 | yes | +6.0 | 64 | +0.3 | +0.02 | 53% | 17 | 18 | 1.04 | +0.15 | 158 | 1.2 | -1.2 |
| 5 | 2025-10-28 to 2026-04-28 | swing_lookback=5 confirmation=none target_r=2.0 | 3 | yes | +1.2 | 67 | -2.9 | -0.22 | 28% | 25 | 14 | 0.70 | -1.25 | 309 | 1.2 | -4.6 |
| 6 | 2026-04-28 to 2026-09-04 | swing_lookback=5 confirmation=none target_r=1.0 | 4 | no (validation net <= 0) | -2.6 | 45 | -3.0 | -0.31 | 38% | 11 | 11 | 0.57 | -1.69 | 148 | 1.2 | -3.8 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 57 | -2.1 | -119 |
| session | late | 26 | +0.0 | +1 |
| session | london | 101 | -4.5 | -452 |
| session | new_york | 57 | -2.8 | -160 |
| session | overlap | 88 | +2.5 | +218 |
| vol_regime | high | 62 | -0.0 | -2 |
| vol_regime | low | 145 | -2.1 | -303 |
| vol_regime | normal | 122 | -1.7 | -207 |
| trend_regime | ranging | 242 | -1.0 | -235 |
| trend_regime | trending | 87 | -3.2 | -277 |
| exit | stop | 201 | -17.3 | -3473 |
| exit | target | 114 | +24.1 | +2748 |
| exit | time | 14 | +15.3 | +214 |

## XAUUSD

Data: 34708 bars, 2020-10-22 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 3 | 4 | 0% | -0.7 | -49.4 | -1037 | 23.1 | 49.3 | 0% | - | 82 | -13.0 | -1.15 | -13.8 | -0.13 |
| forced | 7 | 7 | 0 | 29% | -0.7 | -49.4 | -1037 | 24.8 | 21.5 | 29% | - | 255 | -0.2 | -0.03 | -2.0 | +0.06 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-23 to 2023-10-20 | swing_lookback=5 confirmation=none target_r=1.0 | 1 | no (validation net <= 0) | -4.0 | 55 | -6.2 | -0.10 | 47% | 24 | 33 | 0.64 | -1.44 | 533 | 1.8 | -9.2 |
| 1 | 2023-10-22 to 2024-04-22 | swing_lookback=5 confirmation=structure target_r=2.0 | 1 | no (validation net <= 0) | -3.1 | 21 | -11.9 | -0.15 | 38% | 61 | 57 | 0.66 | -0.84 | 473 | 1.7 | -22.8 |
| 2 | 2024-04-22 to 2024-10-22 | swing_lookback=3 confirmation=structure target_r=2.0 | 2 | yes | +11.4 | 33 | -0.7 | +0.03 | 39% | 99 | 65 | 0.98 | -0.05 | 431 | 1.4 | -1.6 |
| 3 | 2024-10-22 to 2025-04-22 | swing_lookback=3 confirmation=structure target_r=2.0 | 2 | no (validation net <= 0) | -0.7 | 22 | +40.6 | +0.74 | 64% | 106 | 74 | 2.52 | +1.81 | 185 | 1.2 | +40.4 |
| 4 | 2025-04-22 to 2025-10-22 | swing_lookback=3 confirmation=structure target_r=2.0 | 6 | yes | +40.6 | 28 | -0.1 | +0.03 | 36% | 144 | 80 | 1.00 | -0.01 | 598 | 1.0 | -0.8 |
| 5 | 2025-10-22 to 2026-04-22 | swing_lookback=3 confirmation=none target_r=2.0 | 4 | no (validation net <= 0) | -0.0 | 75 | +9.5 | +0.22 | 43% | 119 | 72 | 1.23 | +0.77 | 1000 | 0.8 | +9.2 |
| 6 | 2026-04-22 to 2026-09-04 | swing_lookback=3 confirmation=structure target_r=2.0 | 3 | yes | +10.0 | 21 | -49.4 | -0.59 | 19% | 131 | 92 | 0.34 | -2.38 | 1037 | 0.9 | -50.2 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 62 | +1.2 | +76 |
| session | late | 11 | -15.2 | -167 |
| session | london | 52 | +3.7 | +192 |
| session | new_york | 50 | +20.2 | +1011 |
| session | overlap | 80 | -14.5 | -1162 |
| vol_regime | high | 144 | -1.9 | -270 |
| vol_regime | low | 68 | -3.6 | -244 |
| vol_regime | normal | 43 | +10.8 | +465 |
| trend_regime | ranging | 198 | -2.3 | -449 |
| trend_regime | trending | 57 | +7.0 | +400 |
| exit | end_of_data | 1 | -38.2 | -38 |
| exit | stop | 144 | -66.1 | -9515 |
| exit | target | 88 | +90.5 | +7965 |
| exit | time | 22 | +70.0 | +1540 |

