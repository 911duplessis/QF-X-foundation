# USDJPY Gotobi-Day Tokyo Fix v1

Status: **DRAFT**, awaiting the account owner's decisions G1-G6 below.
Nothing is frozen and no code exists. **No USDJPY price data before
2021-01-04 has been read** (see the intake record below).

Chosen from `next_candidates_2026-09.md` (candidate C) as the recommended
candidate. The account owner has confirmed the broker's history depth,
but has not yet formally chosen C: approving this draft is that choice.

## Mechanism (stated before data)

- **Who pays:** Japanese importers settle USD purchases at the Tokyo fix,
  which is set at 09:55 JST. These settlements concentrate on *gotobi* days,
  the customary settlement dates ending in 5 or 0.
- **Why the price moves:** the demand is price-insensitive and predictable
  in both date and time. Banks that fill the fix orders are compensated for
  the imbalance. The expected result is that USDJPY tends to rise into the
  fix on gotobi days.
- **Literature:** the effect has been studied academically, e.g. Ito &
  Yamada (2017) on Tokyo-fix order imbalances. That motivates the
  hypothesis, but it is **not** evidence here. Published effects may have
  been arbitraged away since.

## Hypothesis (one-sided, no parameters)

> On gotobi days, USDJPY rises between 09:00 and 10:00 JST by more than
> round-trip costs.

Direction, days and hour are all fixed by the mechanism. **There is no
grid, no parameter selection and no walk-forward selection.**

## Definitions

- **Calendar:** Japan has no DST, so JST = UTC + 9 all year and 09:00 JST is
  always 00:00 UTC. Bars are identified by their UTC open time, after the
  existing loader converts server time (Europe/Athens).
- **Japanese bank business day:** Monday-Friday and not in
  `assets/jp_bank_holidays_2013_2026.json`.
  - That file is generated from python-holidays 0.62 `holidays.Japan`, plus
    the Dec 31 and Jan 1-3 bank closures. It holds 293 dates, sha256
    `3fc1131a9d7ea4ea7f02325b43c289cb161fa773695f96c5282814621ee400be`.
  - The calendar is fixed by that file, not by any library at run time.
- **Gotobi day (G2):** each month's 5th, 10th, 15th, 20th and 25th, plus the
  30th (or the last calendar day of February).
  - A date that is not a Japanese bank business day rolls back to the
    preceding business day.
  - If two dates roll to the same day, that day counts once.
- **Trade (G1):** long USDJPY.
  - Market entry at the open of the 00:00 UTC bar (09:00 JST).
  - Exit at the open of the 01:00 UTC bar (10:00 JST).
  - No stop and no target. It is a one-hour hold that contains the 09:55 fix.
  - The trade needs both the 00:00 and 01:00 bars to exist, else the day is
    skipped. Skipping depends on data availability only, never on price.
- **Costs:**
  - spread floor 0.025 (captured 2026-09-27, the FX Session v1 cost table);
  - the per-bar spread is used when wider;
  - slippage = floor / 6 per side;
  - commission 0 (D6 evidence, FX Session v1).
- **Swap:** entry and exit are at 02:00-04:00 server time, far from the 22:00
  server rollover, so no swap applies.
- **Placebo days:** Japanese bank business days that are not gotobi days,
  same trade and same hour.

## Samples

| sample | period | role |
|---|---|---|
| **Primary (untouched)** | 2013-08-26 to 2020-12-31 (UTC dates; first full week of the export onward) | qualification |
| Secondary (already used by test 17) | 2021-01-04 to 2026-09-25 | descriptive only, no qualification weight |

Test 17 used USDJPY.m from 2021-01-04 onward, and only traded London hours.
**No test in this project has read any USDJPY bar before 2021-01-04.**

## Primary outcome: qualified only if every rule holds on the primary sample

1. **Mean net bps per gotobi-day trade > 0**, with a t-statistic >= 2.
   - One trade per day, so clusters = trades and the t is the same as a
     day-clustered t.
2. **The placebo rules out a generic hour effect:** the mean *gross* return on
   gotobi days minus the mean gross return on placebo days must be > 0, with
   Welch t >= 2.
3. **Stable over time:** net positive in >= 60% of calendar years
   (2014-2020 are full years; the 2013 stub counts only if it has >= 30
   events), and a median year > 0.
4. **Survives 2x costs:** net mean > 0 at double spread and slippage.
5. **Sample size:** at least 400 trades.

Rules 1 and 2 together replace the drift control. The placebo is the natural
control for a calendar effect: the same hour, same instrument and same
execution, differing only in the mechanism's trigger.

Descriptive only:
- the secondary sample, with the same statistics;
- month-end-only versus the 5/10/15/20/25 dates;
- gross versus net;
- per-year table;
- achieved resolution.

## Ledger section (required by the test-ledger rule)

1. **Overlap:** the primary sample overlaps no ledger test. The secondary
   sample overlaps test 17 (USDJPY.m, 2021-2026, 07:00-16:00 London only;
   the 00:00 UTC hour was never traded).
2. **Family size on the primary data:** 1 (this test).
3. **Adjustment:** option 2, a confirmatory test on untouched data. The
   threshold is unadjusted, t >= 2 on the primary sample. The contaminated
   secondary sample carries no qualification weight.
4. The ledger row will be added in the same commit as the result.

## Pre-data power

- **Events (calendar only, no prices):** 526 gotobi days in the primary
  sample and 411 in the secondary.
- **MDE formula:** MDE = 2.8416 x sd / sqrt(n), the one used for all prior
  power figures.
- **Per-trade sd (assumption):** no USDJPY dispersion has been published in
  this project. The assumption is 8-15 bps for a 1-hour hold. That is the
  published EURUSD multi-hour sd of 23-34 bps, scaled to one hour, with a
  margin for JPY volatility.

| sd (bps) | MDE primary (n = 526) | MDE secondary (n = 411) |
|---|---|---|
| 8 | 0.99 | 1.12 |
| 12 | 1.49 | 1.68 |
| 15 | 1.86 | 2.10 |

- **Design requirement (proposed, G5):** the central MDE (sd 12) must be
  <= 2 bps. It is 1.49 bps, so the requirement passes.
- **Economic hurdle:** a net edge of about 1.5 bps needs a gross move of
  about 3.6 bps per event, because the round trip is about 2.1 bps.
  - The placebo rule is powered similarly: there are about 3x as many
    placebo days, so the difference test is nearly as precise as the
    gotobi mean.

## Intake record: quarantined early upload (2026-09-27)

The account owner was asked to report only the start date of a USDJPY H1
export. The full file was uploaded instead. It is **quarantined unread**:

| item | value |
|---|---|
| file (as uploaded) | `USDJPY.m_H1_201308230000_202609252300.csv` |
| sha256 | `578b734606f674bfef3ca6c8758a11335fecf2258ea550c9c15bef0f9633d05f` |
| size | 2,837,179 bytes |
| inspected | only the file name (start 2013-08-23 00:00, end 2026-09-25 23:00 server time), sha256 and size |

At freeze, the file used must be byte-identical to this hash.

## Decisions for the account owner

| # | decision | recommendation |
|---|---|---|
| G1 | Window 00:00-01:00 UTC (09:00-10:00 JST), which contains the 09:55 fix plus 5 minutes after it. Alternative: 23:00-01:00 UTC (08:00-10:00 JST). | **00:00-01:00**. H1 cannot isolate 09:55. The one-hour bar is closest to the fix, and adding 08:00 JST dilutes it with pre-open drift. |
| G2 | Gotobi set: 5/10/15/20/25/30 (Feb: last day), rolled back to the prior bank business day | **approve**, the standard market convention |
| G3 | Primary = untouched 2013-08-26 to 2020-12-31; 2021-2026 descriptive only | **approve**, as required by the ledger rule |
| G4 | Qualification rules 1-5 above, with the placebo difference t >= 2 replacing the drift control | **approve** |
| G5 | Power requirement: central MDE <= 2 bps; sd 8-15 reported as sensitivity | **approve** |
| G6 | Formally choose candidate C over A | **C** |

## Explicitly excluded

- No other pairs; no other hours; no short side; no "post-fix reversal"
  variant (that would be a separate hypothesis).
- No volatility, trend or day-of-week filters.
- No change of window, day set or sample after any data is read.
