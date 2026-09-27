# Walk-forward: vol_expansion_short (H1)

Specification (frozen before this run): `docs/hypotheses/volatility_expansion_v1.md`.

Windows: 24m train -> 6m validation -> 6m test, step 6m. Train screen: >= 30 trades and net > 0. Validation selects (>= 5 trades, net > 0, else abstain). Grid: 8 parameter sets. Machine-readable results in the matching `.json` file.

Qualification (deployed track): pooled validation > 0; pooled test > 0 with >= 30 trades and t >= 2.0; positive at 2x costs; >= 60% of traded test windows profitable; median window > 0; >= 60% of windows positive at 2x costs; no window > 50% of pooled P&L.

| symbol | deployed qualified | forced qualified | deployed failures |
|---|---|---|---|
| BTCUSD | NO | NO | test t +0.54 < 2.0; one window = 106% of pooled P&L |
| EURUSD | NO | NO | pooled test net <= 0; test t -1.28 < 2.0; negative at 2x costs; profitable windows 33% < 60%; median window net <= 0; windows surviving stress 33% < 60% |
| XAUUSD | NO | NO | pooled test net <= 0; test t -1.04 < 2.0; negative at 2x costs; profitable windows 50% < 60%; median window net <= 0; windows surviving stress 0% < 60% |

## BTCUSD

Data: 50058 bars, 2020-12-02 to 2026-08-24 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 3 | 3 | 67% | +5.9 | -9.7 | -310 | 18.7 | 45.2 | 67% | 106% | 103 | +9.1 | +0.54 | +7.1 | +0.08 |
| forced | 6 | 6 | 0 | 67% | +5.6 | -21.8 | -348 | 19.1 | 39.2 | 50% | 74% | 189 | +7.1 | +0.64 | +1.8 | +0.03 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-06-02 to 2023-12-02 | box_bars=12 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | +0.0 | 16 | -21.8 | -0.30 | 25% | 130 | 72 | 0.60 | -0.93 | 659 | 13.4 | -42.8 |
| 1 | 2023-12-02 to 2024-06-02 | box_bars=24 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | -71.5 | 21 | +23.4 | +0.10 | 38% | 247 | 114 | 1.33 | +0.56 | 546 | 7.8 | +4.3 |
| 2 | 2024-06-02 to 2024-12-02 | box_bars=12 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -5.7 | 49 | +5.4 | -0.02 | 51% | 96 | 90 | 1.12 | +0.34 | 863 | 6.2 | -7.2 |
| 3 | 2024-12-02 to 2025-06-02 | box_bars=24 stop=box_mid target_r=1.0 | 2 | yes | +20.7 | 43 | +5.9 | +0.09 | 56% | 126 | 146 | 1.09 | +0.26 | 683 | 4.3 | +3.9 |
| 4 | 2025-06-02 to 2025-12-02 | box_bars=24 stop=box_mid target_r=2.0 | 3 | yes | +28.4 | 28 | +35.5 | +0.22 | 46% | 193 | 101 | 1.66 | +1.10 | 679 | 3.7 | +36.1 |
| 5 | 2025-12-02 to 2026-06-02 | box_bars=24 stop=box_mid target_r=2.0 | 4 | yes | +35.5 | 32 | -9.7 | -0.04 | 38% | 216 | 145 | 0.89 | -0.28 | 1086 | 5.4 | -13.2 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 49 | +17.3 | +846 |
| session | late | 22 | -33.2 | -731 |
| session | london | 32 | -1.8 | -58 |
| session | new_york | 37 | -15.3 | -566 |
| session | overlap | 49 | +37.8 | +1853 |
| vol_regime | high | 35 | +0.2 | +7 |
| vol_regime | low | 85 | +7.7 | +652 |
| vol_regime | normal | 69 | +9.9 | +686 |
| trend_regime | ranging | 147 | +6.6 | +974 |
| trend_regime | trending | 42 | +8.8 | +371 |
| exit | end_of_data | 1 | +59.6 | +60 |
| exit | stop | 99 | -113.5 | -11241 |
| exit | target | 77 | +155.3 | +11958 |
| exit | time | 12 | +47.4 | +569 |

## EURUSD

Data: 36445 bars, 2020-10-28 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 3 | 4 | 33% | -3.5 | -8.4 | -405 | 5.8 | 14.1 | 33% | - | 82 | -4.5 | -1.28 | -5.5 | -0.20 |
| forced | 7 | 7 | 0 | 43% | -0.5 | -10.1 | -405 | 6.0 | 13.5 | 43% | - | 207 | -1.5 | -0.64 | -2.8 | -0.04 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-28 to 2023-10-27 | box_bars=12 stop=box_opposite target_r=1.0 | 4 | no (validation net <= 0) | -1.4 | 48 | +3.9 | +0.11 | 58% | 27 | 29 | 1.32 | +0.90 | 208 | 1.3 | +2.4 |
| 1 | 2023-10-29 to 2024-04-26 | box_bars=12 stop=box_opposite target_r=1.0 | 3 | yes | +3.9 | 48 | -8.4 | -0.35 | 33% | 25 | 25 | 0.50 | -2.30 | 425 | 1.3 | -9.3 |
| 2 | 2024-04-28 to 2024-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | 4 | yes | +6.5 | 17 | +5.6 | +0.12 | 65% | 24 | 29 | 1.55 | +0.77 | 96 | 1.3 | +4.3 |
| 3 | 2024-10-28 to 2025-04-28 | box_bars=24 stop=box_opposite target_r=2.0 | 3 | yes | +5.6 | 17 | -3.5 | -0.09 | 41% | 44 | 37 | 0.84 | -0.31 | 204 | 1.3 | -4.6 |
| 4 | 2025-04-28 to 2025-10-28 | box_bars=24 stop=box_opposite target_r=2.0 | 1 | no (validation net <= 0) | -3.5 | 26 | -10.1 | -0.04 | 35% | 57 | 46 | 0.66 | -0.89 | 470 | 1.2 | -11.1 |
| 5 | 2025-10-28 to 2026-04-28 | box_bars=24 stop=box_mid target_r=2.0 | 3 | no (validation net <= 0) | -7.9 | 23 | -0.5 | -0.03 | 35% | 34 | 19 | 0.96 | -0.09 | 126 | 1.2 | -1.2 |
| 6 | 2026-04-28 to 2026-09-04 | box_bars=24 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -4.0 | 28 | +5.1 | +0.15 | 61% | 20 | 19 | 1.69 | +1.26 | 51 | 1.3 | +3.3 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 32 | -5.3 | -169 |
| session | late | 8 | -7.5 | -60 |
| session | london | 91 | +1.8 | +166 |
| session | new_york | 22 | -5.7 | -124 |
| session | overlap | 54 | -2.4 | -129 |
| vol_regime | high | 27 | -16.5 | -445 |
| vol_regime | low | 82 | +0.9 | +70 |
| vol_regime | normal | 98 | +0.6 | +59 |
| trend_regime | ranging | 159 | +0.5 | +83 |
| trend_regime | trending | 48 | -8.3 | -400 |
| exit | end_of_data | 2 | -4.6 | -9 |
| exit | stop | 99 | -30.1 | -2984 |
| exit | target | 71 | +31.6 | +2241 |
| exit | time | 35 | +12.4 | +435 |

## XAUUSD

Data: 34708 bars, 2020-10-22 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 2 | 5 | 50% | -6.1 | -12.6 | -429 | 6.5 | 19.5 | 0% | - | 77 | -5.4 | -1.04 | -7.4 | -0.14 |
| forced | 7 | 7 | 0 | 29% | -13.5 | -51.1 | -1277 | 16.9 | 18.1 | 14% | - | 189 | -11.7 | -2.23 | -12.9 | -0.14 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-23 to 2023-10-20 | box_bars=12 stop=box_opposite target_r=1.0 | 5 | yes | +3.5 | 43 | +0.3 | +0.02 | 51% | 43 | 45 | 1.02 | +0.05 | 335 | 1.8 | -1.7 |
| 1 | 2023-10-22 to 2024-04-22 | box_bars=12 stop=box_opposite target_r=1.0 | 2 | yes | +0.3 | 34 | -12.6 | -0.35 | 32% | 48 | 42 | 0.55 | -1.68 | 543 | 1.7 | -14.4 |
| 2 | 2024-04-22 to 2024-10-22 | box_bars=24 stop=box_opposite target_r=1.0 | 3 | no (validation net <= 0) | -2.3 | 11 | -17.6 | -0.20 | 36% | 101 | 85 | 0.68 | -0.61 | 393 | 1.4 | -18.5 |
| 3 | 2024-10-22 to 2025-04-22 | box_bars=24 stop=box_opposite target_r=2.0 | 4 | no (validation net <= 0) | -10.5 | 12 | -17.8 | -0.23 | 25% | 139 | 70 | 0.66 | -0.62 | 213 | 1.3 | -18.7 |
| 4 | 2025-04-22 to 2025-10-22 | box_bars=24 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | -31.9 | 25 | -13.5 | -0.19 | 24% | 134 | 60 | 0.70 | -0.75 | 708 | 1.0 | -14.2 |
| 5 | 2025-10-22 to 2026-04-22 | box_bars=12 stop=box_mid target_r=2.0 | 0 | no (no candidate passed train screen) | -9.5 | 25 | -51.1 | -0.47 | 20% | 89 | 86 | 0.26 | -3.01 | 1383 | 0.8 | -51.7 |
| 6 | 2026-04-22 to 2026-09-04 | box_bars=12 stop=box_mid target_r=1.0 | 0 | no (no candidate passed train screen) | -31.3 | 39 | +5.8 | +0.15 | 56% | 64 | 69 | 1.19 | +0.51 | 364 | 0.9 | +5.4 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 41 | -1.5 | -62 |
| session | late | 6 | -41.4 | -249 |
| session | london | 63 | -4.9 | -309 |
| session | new_york | 19 | -44.0 | -836 |
| session | overlap | 60 | -12.6 | -753 |
| vol_regime | high | 91 | -13.6 | -1235 |
| vol_regime | low | 63 | -13.4 | -845 |
| vol_regime | normal | 35 | -3.7 | -129 |
| trend_regime | ranging | 160 | -10.5 | -1676 |
| trend_regime | trending | 29 | -18.4 | -533 |
| exit | end_of_data | 2 | -59.4 | -119 |
| exit | stop | 102 | -64.5 | -6576 |
| exit | target | 71 | +68.1 | +4836 |
| exit | time | 14 | -25.0 | -350 |

