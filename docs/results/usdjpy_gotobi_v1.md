# USDJPY Gotobi-Day Tokyo Fix v1

Specification (frozen before this run, version 2): `docs/hypotheses/usdjpy_gotobi_v1.md`. Long USDJPY 00:00-01:00 UTC (09:00-10:00 JST) on gotobi days; placebo = the same trade on non-gotobi Japanese bank business days. Days 2019-12-17 to 2020-03-29 (data gap) excluded. Both t-gates use t >= 2.28 (Bonferroni, family of 2).

## Primary outcome: **NOT QUALIFIED**

Failures: net -3.03 bps, t -5.07 (need > 0 and t >= 2.28); placebo difference -1.13 bps, Welch t -1.59 (need > 0 and t >= 2.28); positive years 0% < 60%; median year -3.10 <= 0; net at 2x costs -5.59 <= 0

| sample | period | calendar events | trades | gross bps | net bps | t | placebo days | placebo gross | gotobi - placebo (gross) | Welch t | net 2x costs | positive years | median year | achieved resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary (qualification) | 2019-06-10 to 2026-09-25 | 498 | 493 | -0.47 | -3.03 | -5.07 | 1217 | +0.66 | -1.13 | -1.59 | -5.59 | 0% | -3.10 | 1.86 |
| sub-period 1 (descriptive only) | 2019-06-10 to 2020-12-31 | 93 | 91 | -0.10 | -3.22 | -3.31 | 222 | -0.15 | +0.04 | +0.04 | -6.34 | 0% | -3.21 | 3.04 |
| sub-period 2 (descriptive only) | 2021-01-04 to 2026-09-25 | 405 | 402 | -0.55 | -2.99 | -4.27 | 995 | +0.84 | -1.40 | -1.68 | -5.42 | 0% | -2.88 | 2.18 |

Sub-period 1 (2019-06 to 2020) was untouched by any earlier test; sub-period 2 (2021-2026) was read by test 17 (other hours).
Achieved resolution = 3.1216 x SE of net bps; descriptive only (design MDE 1.68 bps central at t >= 2.28, assumption-based).

## Per year (primary; years with < 30 events are not counted)

| year | trades | net bps | counted |
|---|---|---|---|
| 2019 | 37 | -3.12 | yes |
| 2020 | 54 | -3.30 | yes |
| 2021 | 70 | -2.40 | yes |
| 2022 | 71 | -2.67 | yes |
| 2023 | 70 | -3.54 | yes |
| 2024 | 70 | -2.55 | yes |
| 2025 | 69 | -3.71 | yes |
| 2026 | 52 | -3.08 | yes |

Descriptive split (primary): 30th events 78 trades, -1.70 bps; 5th-25th events 415 trades, -3.28 bps.

Data: USDJPY.m 43675 bars, 2019-06-07 13:00 to 2026-09-25 20:00 UTC.
