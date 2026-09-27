# Walk-forward: trend_continuation (H1)

Windows: 24m train -> 6m validation -> 6m test, step 6m. Train screen: >= 30 trades and net > 0. Validation selects (>= 5 trades, net > 0, else abstain). Grid: 9 parameter sets. Machine-readable results in the matching `.json` file.

Qualification (deployed track): pooled validation > 0; pooled test > 0 with >= 30 trades and t >= 2.0; positive at 2x costs; >= 60% of traded test windows profitable; median window > 0; >= 60% of windows positive at 2x costs; no window > 50% of pooled P&L.

| symbol | deployed qualified | forced qualified | deployed failures |
|---|---|---|---|
| BTCUSD | NO | NO | pooled test net <= 0; test t -1.96 < 2.0; negative at 2x costs; profitable windows 0% < 60%; median window net <= 0; windows surviving stress 0% < 60% |
| EURUSD | NO | NO | no traded test windows |
| XAUUSD | NO | NO | test t +0.40 < 2.0; profitable windows 43% < 60%; median window net <= 0; windows surviving stress 43% < 60%; one window = 116% of pooled P&L |

## BTCUSD

Data: 50058 bars, 2020-12-02 to 2026-08-24 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 2 | 4 | 0% | -186.8 | -314.8 | -3463 | 128.0 | 384.1 | 0% | - | 31 | -149.6 | -1.96 | -154.6 | - |
| forced | 6 | 6 | 0 | 50% | -28.6 | -314.8 | -3463 | 181.9 | 349.2 | 33% | - | 117 | -13.2 | -0.34 | -18.8 | - |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-06-02 to 2023-12-02 | lookback=168 entry_z=1.5 | 1 | no (validation net <= 0) | -76.1 | 9 | +236.2 | - | 44% | 774 | 194 | 3.19 | +1.09 | 559 | 14.5 | +221.7 |
| 1 | 2023-12-02 to 2024-06-02 | lookback=72 entry_z=2.0 | 0 | no (no candidate passed train screen) | +298.3 | 13 | -113.4 | - | 31% | 557 | 412 | 0.60 | -0.69 | 2411 | 7.7 | -121.0 |
| 2 | 2024-06-02 to 2024-12-02 | lookback=72 entry_z=2.0 | 1 | no (validation net <= 0) | -113.4 | 14 | +168.6 | - | 57% | 521 | 301 | 2.31 | +1.28 | 777 | 6.5 | +162.1 |
| 3 | 2024-12-02 to 2025-06-02 | lookback=168 entry_z=1.5 | 1 | yes | +72.0 | 11 | -314.8 | - | 27% | 200 | 508 | 0.15 | -2.76 | 3463 | 4.3 | -319.1 |
| 4 | 2025-06-02 to 2025-12-02 | lookback=72 entry_z=1.0 | 5 | no (validation net <= 0) | -64.7 | 50 | +1.6 | - | 38% | 229 | 137 | 1.02 | +0.04 | 1603 | 3.7 | -2.1 |
| 5 | 2025-12-02 to 2026-06-02 | lookback=72 entry_z=1.5 | 5 | yes | +21.7 | 20 | -58.8 | - | 25% | 491 | 242 | 0.68 | -0.61 | 2691 | 5.3 | -64.1 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 36 | -29.3 | -1055 |
| session | late | 16 | +17.2 | +275 |
| session | london | 12 | -114.6 | -1375 |
| session | new_york | 30 | +5.7 | +171 |
| session | overlap | 23 | +19.0 | +437 |
| vol_regime | high | 16 | -221.0 | -3535 |
| vol_regime | low | 68 | +37.6 | +2554 |
| vol_regime | normal | 33 | -17.1 | -565 |
| trend_regime | ranging | 51 | -41.3 | -2105 |
| trend_regime | trending | 66 | +8.5 | +559 |
| exit | end_of_data | 1 | +28.0 | +28 |
| exit | signal | 116 | -13.6 | -1574 |

## EURUSD

Data: 36445 bars, 2020-10-28 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 0 | 7 | 0% | +0.0 | +0.0 | +0 | 0.0 | 0.0 | 0% | - | 0 | +0.0 | +0.00 | +0.0 | - |
| forced | 7 | 7 | 0 | 29% | -14.6 | -39.1 | -315 | 22.6 | 28.7 | 29% | - | 89 | -7.6 | -1.25 | -8.9 | - |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-28 to 2023-10-27 | lookback=72 entry_z=1.0 | 1 | no (validation net <= 0) | -28.0 | 37 | -8.5 | - | 30% | 47 | 32 | 0.62 | -0.97 | 380 | 1.3 | -9.8 |
| 1 | 2023-10-29 to 2024-04-26 | lookback=168 entry_z=1.5 | 0 | no (no candidate passed train screen) | +4.2 | 9 | -18.5 | - | 33% | 15 | 36 | 0.22 | -1.91 | 167 | 1.3 | -19.8 |
| 2 | 2024-04-28 to 2024-10-28 | lookback=168 entry_z=1.5 | 0 | no (no candidate passed train screen) | -18.5 | 10 | +10.1 | - | 60% | 53 | 54 | 1.46 | +0.50 | 135 | 1.3 | +8.8 |
| 3 | 2024-10-28 to 2025-04-28 | lookback=72 entry_z=2.0 | 0 | no (no candidate passed train screen) | -10.1 | 6 | +37.6 | - | 67% | 86 | 59 | 2.92 | +0.87 | 104 | 1.3 | +36.3 |
| 4 | 2025-04-28 to 2025-10-28 | lookback=168 entry_z=1.5 | 0 | no (no candidate passed train screen) | +83.8 | 5 | -39.1 | - | 20% | 25 | 55 | 0.12 | -2.17 | 221 | 1.2 | -40.3 |
| 5 | 2025-10-28 to 2026-04-28 | lookback=168 entry_z=1.0 | 2 | no (validation net <= 0) | -37.8 | 18 | -14.8 | - | 39% | 39 | 49 | 0.51 | -1.11 | 319 | 1.2 | -16.0 |
| 6 | 2026-04-28 to 2026-09-04 | lookback=168 entry_z=1.5 | 1 | no (validation net <= 0) | -37.3 | 4 | -14.6 | - | 25% | 9 | 23 | 0.14 | -1.34 | 59 | 1.2 | -15.9 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 14 | -10.3 | -144 |
| session | late | 3 | -16.1 | -48 |
| session | london | 20 | -16.5 | -330 |
| session | new_york | 29 | -0.4 | -11 |
| session | overlap | 23 | -6.2 | -142 |
| vol_regime | high | 8 | -14.5 | -116 |
| vol_regime | low | 30 | -5.5 | -166 |
| vol_regime | normal | 51 | -7.7 | -393 |
| trend_regime | ranging | 28 | -0.7 | -21 |
| trend_regime | trending | 61 | -10.7 | -654 |
| exit | end_of_data | 1 | +4.3 | +4 |
| exit | signal | 88 | -7.7 | -680 |

## XAUUSD

Data: 34708 bars, 2020-10-22 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 7 | 0 | 43% | -5.5 | -178.8 | -894 | 84.4 | 65.7 | 43% | 116% | 104 | +9.2 | +0.40 | +8.0 | - |
| forced | 7 | 7 | 0 | 43% | -5.5 | -178.8 | -894 | 84.4 | 65.7 | 43% | 116% | 104 | +9.2 | +0.40 | +8.0 | - |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-23 to 2023-10-20 | lookback=24 entry_z=2.0 | 4 | yes | +16.2 | 16 | -5.5 | - | 31% | 51 | 31 | 0.74 | -0.47 | 281 | 1.8 | -7.3 |
| 1 | 2023-10-22 to 2024-04-22 | lookback=168 entry_z=1.5 | 4 | yes | +140.0 | 9 | +123.4 | - | 67% | 286 | 202 | 2.84 | +1.23 | 402 | 1.7 | +121.7 |
| 2 | 2024-04-22 to 2024-10-22 | lookback=168 entry_z=1.5 | 6 | yes | +123.4 | 8 | -9.9 | - | 50% | 111 | 131 | 0.85 | -0.17 | 486 | 1.4 | -11.4 |
| 3 | 2024-10-22 to 2025-04-22 | lookback=168 entry_z=1.0 | 5 | yes | +35.9 | 18 | +43.2 | - | 50% | 186 | 99 | 1.87 | +0.82 | 364 | 1.3 | +42.0 |
| 4 | 2025-04-22 to 2025-10-22 | lookback=72 entry_z=1.0 | 6 | yes | +66.6 | 31 | +16.6 | - | 48% | 122 | 82 | 1.39 | +0.54 | 557 | 1.0 | +15.6 |
| 5 | 2025-10-22 to 2026-04-22 | lookback=72 entry_z=1.5 | 7 | yes | +40.0 | 17 | -22.5 | - | 35% | 346 | 223 | 0.84 | -0.23 | 941 | 0.8 | -23.3 |
| 6 | 2026-04-22 to 2026-09-04 | lookback=168 entry_z=1.5 | 8 | yes | +95.1 | 5 | -178.8 | - | 20% | 204 | 275 | 0.19 | -1.73 | 894 | 0.9 | -179.7 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 27 | +10.2 | +276 |
| session | late | 9 | +112.6 | +1014 |
| session | london | 13 | -28.1 | -366 |
| session | new_york | 23 | +34.7 | +799 |
| session | overlap | 32 | -23.9 | -764 |
| vol_regime | high | 52 | -17.1 | -889 |
| vol_regime | low | 25 | +83.8 | +2094 |
| vol_regime | normal | 27 | -9.1 | -247 |
| trend_regime | ranging | 41 | -16.2 | -663 |
| trend_regime | trending | 63 | +25.7 | +1621 |
| exit | end_of_data | 4 | +148.8 | +595 |
| exit | signal | 100 | +3.6 | +363 |

