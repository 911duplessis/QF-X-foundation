# Walk-forward: sweep_reversal_short (H1)

Specification (frozen before this run): `docs/hypotheses/liquidity_sweep_reversal_v1.md`.

Windows: 24m train -> 6m validation -> 6m test, step 6m. Train screen: >= 30 trades and net > 0. Validation selects (>= 5 trades, net > 0, else abstain). Grid: 8 parameter sets. Machine-readable results in the matching `.json` file.

Qualification (deployed track): pooled validation > 0; pooled test > 0 with >= 30 trades and t >= 2.0; positive at 2x costs; >= 60% of traded test windows profitable; median window > 0; >= 60% of windows positive at 2x costs; no window > 50% of pooled P&L.

| symbol | deployed qualified | forced qualified | deployed failures |
|---|---|---|---|
| BTCUSD | NO | NO | no traded test windows |
| EURUSD | NO | NO | no traded test windows |
| XAUUSD | NO | NO | no traded test windows |

## BTCUSD

Data: 50058 bars, 2020-12-02 to 2026-08-24 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 6 | 0 | 6 | 0% | +0.0 | +0.0 | +0 | 0.0 | 0.0 | 0% | - | 0 | +0.0 | +0.00 | +0.0 | - |
| forced | 6 | 6 | 0 | 50% | -2.8 | -22.0 | -1913 | 27.6 | 53.6 | 50% | - | 498 | -1.7 | -0.30 | -3.6 | -0.08 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-06-02 to 2023-12-02 | swing_lookback=3 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | +0.0 | 107 | -15.1 | -0.20 | 45% | 79 | 92 | 0.70 | -1.67 | 1885 | 13.5 | -15.5 |
| 1 | 2023-12-02 to 2024-06-02 | swing_lookback=5 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | -21.0 | 87 | -9.8 | -0.06 | 48% | 91 | 104 | 0.82 | -0.75 | 1355 | 7.4 | -19.1 |
| 2 | 2024-06-02 to 2024-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | 0 | no (no candidate passed train screen) | -11.1 | 37 | +30.5 | +0.18 | 49% | 201 | 132 | 1.45 | +0.95 | 919 | 6.1 | +26.6 |
| 3 | 2024-12-02 to 2025-06-02 | swing_lookback=3 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | -12.5 | 148 | +4.2 | -0.03 | 50% | 100 | 92 | 1.09 | +0.45 | 1733 | 4.2 | +1.7 |
| 4 | 2025-06-02 to 2025-12-02 | swing_lookback=5 confirmation=structure target_r=2.0 | 0 | no (no candidate passed train screen) | -37.0 | 32 | +55.8 | +0.20 | 44% | 248 | 94 | 2.06 | +1.61 | 497 | 3.7 | +54.1 |
| 5 | 2025-12-02 to 2026-06-02 | swing_lookback=5 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | -3.1 | 87 | -22.0 | -0.23 | 29% | 152 | 92 | 0.67 | -1.63 | 2466 | 5.2 | -29.3 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 110 | +1.7 | +188 |
| session | late | 54 | -7.1 | -384 |
| session | london | 95 | -25.6 | -2437 |
| session | new_york | 120 | +9.4 | +1132 |
| session | overlap | 119 | +5.5 | +650 |
| vol_regime | high | 101 | +2.2 | +220 |
| vol_regime | low | 259 | -1.9 | -484 |
| vol_regime | normal | 138 | -4.3 | -587 |
| trend_regime | ranging | 399 | -2.5 | -1011 |
| trend_regime | trending | 99 | +1.6 | +161 |
| exit | end_of_data | 2 | -1.9 | -4 |
| exit | stop | 266 | -96.4 | -25634 |
| exit | target | 203 | +116.6 | +23670 |
| exit | time | 27 | +41.4 | +1117 |

## EURUSD

Data: 36445 bars, 2020-10-28 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 0 | 7 | 0% | +0.0 | +0.0 | +0 | 0.0 | 0.0 | 0% | - | 0 | +0.0 | +0.00 | +0.0 | - |
| forced | 7 | 7 | 0 | 0% | -1.3 | -3.4 | -324 | 1.1 | 2.3 | 0% | - | 482 | -1.9 | -1.70 | -3.0 | -0.14 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-28 to 2023-10-27 | swing_lookback=5 confirmation=structure target_r=1.0 | 1 | no (validation net <= 0) | -13.1 | 21 | -1.3 | -0.14 | 43% | 26 | 22 | 0.90 | -0.21 | 148 | 1.3 | -2.1 |
| 1 | 2023-10-29 to 2024-04-26 | swing_lookback=3 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | -1.2 | 95 | -3.4 | -0.23 | 27% | 25 | 14 | 0.67 | -1.64 | 352 | 1.3 | -4.6 |
| 2 | 2024-04-28 to 2024-10-28 | swing_lookback=3 confirmation=none target_r=2.0 | 1 | no (validation net <= 0) | -3.4 | 94 | -0.5 | -0.11 | 32% | 23 | 11 | 0.94 | -0.25 | 170 | 1.3 | -0.1 |
| 3 | 2024-10-28 to 2025-04-28 | swing_lookback=3 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | -0.5 | 92 | -3.2 | -0.11 | 33% | 36 | 22 | 0.79 | -0.97 | 411 | 1.3 | -6.2 |
| 4 | 2025-04-28 to 2025-10-28 | swing_lookback=3 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | -3.2 | 81 | -0.9 | -0.09 | 32% | 34 | 18 | 0.92 | -0.30 | 211 | 1.2 | -1.2 |
| 5 | 2025-10-28 to 2026-04-28 | swing_lookback=3 confirmation=structure target_r=1.0 | 0 | no (no candidate passed train screen) | +3.7 | 36 | -0.8 | -0.06 | 47% | 28 | 26 | 0.94 | -0.17 | 171 | 1.2 | -1.5 |
| 6 | 2026-04-28 to 2026-09-04 | swing_lookback=3 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | +0.8 | 63 | -1.8 | -0.22 | 30% | 23 | 13 | 0.79 | -0.80 | 172 | 1.2 | -2.7 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 116 | -1.9 | -221 |
| session | late | 22 | -9.4 | -207 |
| session | london | 137 | -1.6 | -213 |
| session | new_york | 76 | -0.7 | -52 |
| session | overlap | 131 | -1.6 | -211 |
| vol_regime | high | 75 | +1.3 | +99 |
| vol_regime | low | 226 | -0.8 | -177 |
| vol_regime | normal | 181 | -4.6 | -826 |
| trend_regime | ranging | 367 | -1.4 | -506 |
| trend_regime | trending | 115 | -3.5 | -398 |
| exit | end_of_data | 1 | +0.8 | +1 |
| exit | stop | 318 | -16.6 | -5283 |
| exit | target | 149 | +28.6 | +4263 |
| exit | time | 14 | +8.2 | +115 |

## XAUUSD

Data: 34708 bars, 2020-10-22 to 2026-09-04 UTC.

### Stability across test windows

| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deployed | 7 | 0 | 7 | 0% | +0.0 | +0.0 | +0 | 0.0 | 0.0 | 0% | - | 0 | +0.0 | +0.00 | +0.0 | - |
| forced | 7 | 7 | 0 | 29% | -5.3 | -8.5 | -478 | 4.6 | 10.6 | 29% | - | 450 | -3.1 | -1.41 | -4.0 | -0.10 |

### Windows (test segment of the selected parameters; forced track)

| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2023-04-23 to 2023-10-20 | swing_lookback=3 confirmation=none target_r=2.0 | 0 | no (no candidate passed train screen) | -5.0 | 86 | +3.8 | +0.15 | 42% | 44 | 25 | 1.26 | +0.90 | 241 | 1.8 | +3.2 |
| 1 | 2023-10-22 to 2024-04-22 | swing_lookback=5 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | +3.4 | 50 | -7.3 | -0.27 | 38% | 26 | 28 | 0.57 | -1.69 | 380 | 1.7 | -10.9 |
| 2 | 2024-04-22 to 2024-10-22 | swing_lookback=3 confirmation=none target_r=1.0 | 4 | no (validation net <= 0) | -6.3 | 84 | -5.7 | -0.27 | 38% | 35 | 31 | 0.70 | -1.40 | 593 | 1.4 | -6.5 |
| 3 | 2024-10-22 to 2025-04-22 | swing_lookback=5 confirmation=none target_r=1.0 | 2 | no (validation net <= 0) | -7.1 | 58 | -5.3 | -0.27 | 38% | 36 | 30 | 0.72 | -1.09 | 399 | 1.2 | -6.1 |
| 4 | 2025-04-22 to 2025-10-22 | swing_lookback=5 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | -5.3 | 49 | -8.5 | -0.13 | 43% | 36 | 42 | 0.65 | -1.35 | 452 | 1.0 | -9.1 |
| 5 | 2025-10-22 to 2026-04-22 | swing_lookback=3 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | -12.0 | 79 | -3.7 | -0.00 | 51% | 54 | 63 | 0.88 | -0.48 | 1013 | 0.8 | -4.1 |
| 6 | 2026-04-22 to 2026-09-04 | swing_lookback=5 confirmation=none target_r=1.0 | 0 | no (no candidate passed train screen) | -13.0 | 44 | +3.3 | -0.00 | 50% | 55 | 48 | 1.14 | +0.39 | 426 | 0.9 | +2.9 |

### Context breakdown (all forced test trades; descriptive only)

| dimension | label | trades | net bps | total bps |
|---|---|---|---|---|
| session | asia | 102 | -5.2 | -529 |
| session | late | 13 | +30.3 | +394 |
| session | london | 103 | -2.2 | -226 |
| session | new_york | 78 | -12.4 | -970 |
| session | overlap | 154 | -0.4 | -59 |
| vol_regime | high | 217 | -2.1 | -460 |
| vol_regime | low | 122 | -1.9 | -230 |
| vol_regime | normal | 111 | -6.3 | -701 |
| trend_regime | ranging | 323 | -2.7 | -880 |
| trend_regime | trending | 127 | -4.0 | -511 |
| exit | stop | 253 | -36.8 | -9313 |
| exit | target | 190 | +42.5 | +8071 |
| exit | time | 7 | -21.4 | -150 |

