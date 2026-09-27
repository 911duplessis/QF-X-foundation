# Walk-forward: vol_expansion_long (H1)

Specification (frozen before this run): `docs/hypotheses/volatility_expansion_v1.md`.

Windows: 24m train -> 6m validation -> 6m test, step 6m. Train screen: >= 30 trades and net > 0. Validation selects (>= 5 trades, net > 0, else abstain). Grid: 8 parameter sets. Machine-readable results in the matching `.json` file.

Qualification (deployed track): pooled validation > 0; pooled test > 0 with >= 30 trades and t >= 2.0; positive at 2x costs; >= 60% of traded test windows profitable; median window > 0; >= 60% of windows positive at 2x costs; no window > 50% of pooled P&L.

| symbol | deployed qualified | forced qualified | deployed failures |
|---|---|---|---|
| BTCUSD | NO | NO | test t +1.07 < 2.0; one window = 55% of pooled P&L |
| EURUSD | NO | NO | test t +0.42 < 2.0; negative at 2x costs; profitable windows 50% < 60%; windows surviving stress 50% < 60%; one window = 297% of pooled P&L |
| XAUUSD | NO | YES | one window = 52% of pooled P&L |

## BTCUSD

Data: 50058 bars, 2020-12-02 to 2026-08-24 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 4 | 2 | 75% | +19.7 | -4.7 | -260 | 13.7 | 29.2 | 75% | 55% | 152 | +12.9 | +1.07 | +8.9 | +0.06 |
| forced | 6 | 6 | 0 | 83% | +19.7 | -4.7 | -260 | 14.5 | 26.1 | 67% | 34% | 211 | +15.8 | +1.61 | +11.9 | +0.10 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-06-02 to 2023-12-02 | box_bars=12 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | +0.0 | 29 | +8.3 | +0.15 | 41% | 145 | 88 | 1.16 | +0.37 | 566 | 13.1 | -8.1 |
| 1 | 2023-12-02 to 2024-06-02 | box_bars=24 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -0.8 | 30 | +38.1 | +0.24 | 63% | 139 | 137 | 1.76 | +1.47 | 544 | 7.4 | +34.9 |
| 2 | 2024-06-02 to 2024-12-02 | box_bars=12 stop=box_mid target_r=1.0 | 1 | yes | +7.5 | 55 | -4.7 | -0.11 | 47% | 90 | 90 | 0.90 | -0.35 | 997 | 6.1 | -10.5 |
| 3 | 2024-12-02 to 2025-06-02 | box_bars=24 stop=box_mid target_r=2.0 | 8 | yes | +46.2 | 27 | +28.8 | +0.15 | 41% | 219 | 102 | 1.48 | +0.84 | 719 | 4.2 | +26.5 |
| 4 | 2025-06-02 to 2025-12-02 | box_bars=24 stop=box_mid target_r=2.0 | 8 | yes | +28.8 | 39 | +27.7 | +0.28 | 51% | 135 | 86 | 1.66 | +1.38 | 367 | 3.7 | +23.1 |
| 5 | 2025-12-02 to 2026-06-02 | box_bars=24 stop=box_opposite target_r=2.0 | 8 | yes | +39.5 | 31 | +11.7 | +0.02 | 42% | 226 | 144 | 1.14 | +0.31 | 712 | 5.1 | +7.7 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 39 | +30.0 | +1171 |
| session | late | 19 | +73.1 | +1390 |
| session | london | 43 | -5.3 | -227 |
| session | new_york | 54 | +9.2 | +499 |
| session | overlap | 56 | +9.1 | +511 |
| vol_regime | high | 19 | +31.7 | +603 |
| vol_regime | low | 115 | +10.0 | +1151 |
| vol_regime | normal | 77 | +20.7 | +1590 |
| trend_regime | ranging | 169 | +16.0 | +2700 |
| trend_regime | trending | 42 | +15.3 | +644 |
| exit | end_of_data | 2 | +31.9 | +64 |
| exit | stop | 103 | -106.6 | -10976 |
| exit | target | 82 | +148.8 | +12201 |
| exit | time | 24 | +85.6 | +2055 |

## EURUSD

Data: 36445 bars, 2020-10-28 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 2 | 5 | 50% | +6.8 | -9.9 | -218 | 16.7 | 50.0 | 50% | 297% | 36 | +3.1 | +0.42 | -0.3 | +0.05 |
| forced | 7 | 7 | 0 | 43% | -1.5 | -9.9 | -218 | 10.0 | 10.3 | 43% | 219% | 225 | +0.7 | +0.30 | -0.9 | -0.04 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-28 to 2023-10-27 | box_bars=12 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -1.6 | 64 | -1.5 | -0.18 | 44% | 17 | 16 | 0.83 | -0.70 | 121 | 1.3 | -2.7 |
| 1 | 2023-10-29 to 2024-04-26 | box_bars=24 stop=box_opposite target_r=2.0 | 0 | no (no candidate passed train screen) | -14.4 | 20 | +7.1 | +0.20 | 50% | 41 | 27 | 1.52 | +0.77 | 75 | 1.3 | +6.2 |
| 2 | 2024-04-28 to 2024-10-28 | box_bars=12 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -3.4 | 65 | -2.1 | -0.12 | 46% | 11 | 14 | 0.71 | -1.26 | 191 | 1.3 | -3.2 |
| 3 | 2024-10-28 to 2025-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | 0 | no (no candidate passed train screen) | +10.2 | 16 | -2.9 | +0.03 | 31% | 86 | 43 | 0.90 | -0.18 | 323 | 1.3 | -6.6 |
| 4 | 2025-04-28 to 2025-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | 3 | no (validation net <= 0) | -2.9 | 24 | +7.4 | +0.18 | 46% | 49 | 28 | 1.49 | +0.77 | 175 | 1.2 | +6.5 |
| 5 | 2025-10-28 to 2026-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | 3 | yes | +7.4 | 14 | +23.5 | +0.56 | 71% | 47 | 35 | 3.31 | +1.73 | 98 | 1.2 | +16.4 |
| 6 | 2026-04-28 to 2026-09-04 | box_bars=24 stop=box_opposite target_r=2.0 | 7 | yes | +23.5 | 22 | -9.9 | -0.28 | 27% | 39 | 28 | 0.52 | -1.37 | 329 | 1.3 | -10.9 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 58 | -2.0 | -117 |
| session | late | 5 | -4.9 | -25 |
| session | london | 86 | +1.1 | +98 |
| session | new_york | 25 | +1.1 | +27 |
| session | overlap | 51 | +3.3 | +167 |
| vol_regime | high | 21 | +18.8 | +395 |
| vol_regime | low | 107 | -1.4 | -148 |
| vol_regime | normal | 97 | -1.0 | -97 |
| trend_regime | ranging | 163 | +1.5 | +250 |
| trend_regime | trending | 62 | -1.6 | -100 |
| exit | end_of_data | 1 | +14.4 | +14 |
| exit | stop | 105 | -23.3 | -2445 |
| exit | target | 77 | +30.3 | +2337 |
| exit | time | 42 | +5.8 | +243 |

## XAUUSD

Data: 34708 bars, 2020-10-22 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 4 | 3 | 75% | +40.7 | -19.7 | -237 | 38.9 | 85.7 | 75% | 52% | 71 | +42.7 | +2.24 | +39.1 | +0.39 |
| forced | 7 | 7 | 0 | 71% | +10.9 | -19.7 | -352 | 35.5 | 67.7 | 71% | 46% | 159 | +21.5 | +2.31 | +18.8 | +0.26 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-23 to 2023-10-20 | box_bars=24 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | +25.4 | 20 | -17.6 | -0.31 | 25% | 76 | 49 | 0.52 | -1.35 | 461 | 1.8 | -18.9 |
| 1 | 2023-10-22 to 2024-04-22 | box_bars=24 stop=box_mid target_r=2.0 | 1 | no (validation net <= 0) | -17.6 | 17 | +10.9 | +0.20 | 41% | 79 | 37 | 1.51 | +0.64 | 219 | 1.7 | +9.8 |
| 2 | 2024-04-22 to 2024-10-22 | box_bars=12 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | -1.3 | 51 | +10.9 | +0.33 | 45% | 72 | 39 | 1.51 | +1.34 | 195 | 1.4 | +8.3 |
| 3 | 2024-10-22 to 2025-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | 2 | yes | +25.6 | 21 | +50.1 | +0.57 | 62% | 131 | 81 | 2.63 | +1.97 | 407 | 1.2 | +47.9 |
| 4 | 2025-04-22 to 2025-10-22 | box_bars=24 stop=box_opposite target_r=2.0 | 6 | yes | +50.1 | 20 | +31.3 | +0.25 | 55% | 151 | 114 | 1.61 | +0.92 | 628 | 1.0 | +30.6 |
| 5 | 2025-10-22 to 2026-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | 6 | yes | +31.3 | 18 | +88.3 | +0.70 | 67% | 203 | 141 | 2.87 | +2.02 | 203 | 0.8 | +78.1 |
| 6 | 2026-04-22 to 2026-09-04 | box_bars=24 stop=box_opposite target_r=2.0 | 8 | yes | +88.3 | 12 | -19.7 | -0.13 | 33% | 229 | 144 | 0.79 | -0.35 | 915 | 0.9 | -20.4 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 34 | +40.9 | +1391 |
| session | late | 8 | +91.2 | +729 |
| session | london | 44 | +1.9 | +84 |
| session | new_york | 25 | +16.4 | +411 |
| session | overlap | 48 | +16.8 | +804 |
| vol_regime | high | 74 | +21.0 | +1552 |
| vol_regime | low | 37 | +17.1 | +633 |
| vol_regime | normal | 48 | +25.7 | +1235 |
| trend_regime | ranging | 126 | +22.5 | +2836 |
| trend_regime | trending | 33 | +17.7 | +584 |
| exit | stop | 77 | -72.2 | -5559 |
| exit | target | 52 | +136.2 | +7082 |
| exit | time | 30 | +63.2 | +1897 |

