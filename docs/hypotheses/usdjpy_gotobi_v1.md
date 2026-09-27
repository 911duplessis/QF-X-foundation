# USDJPY Gotobi-Day Tokyo Fix v1

Status: **FROZEN, version 1** (2026-09-27): **blocked at Gate 0, see below; v2 amendment needed.**
- Decisions: G1 and G3-G6 approved; **G2 amended** by the account owner (no
  February month-end event).
- This freeze commit contains no code for this hypothesis. **No USDJPY price
  data before 2021-01-04 has been read** (see the intake record below).
- Chosen by the account owner from `next_candidates_2026-09.md` (candidate C).

The sequence from here, one commit (or more) per step:
1. this freeze;
2. implementation and synthetic-data tests;
3. verify the quarantined CSV's sha256, then read it;
4. run once;
5. commit the result, the ledger row and the research log together;
6. PR.

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
- **Gotobi day (G2, as amended):** the 5th, 10th, 15th, 20th, 25th and 30th
  of each calendar month.
  - A date that is not a Japanese bank business day rolls back to the
    preceding bank business day. The rolled day is still an event (for
    example, a 25th that falls on a holiday becomes an event on the
    preceding business day).
  - **February has no 30th and so no sixth event.** Its last day is not an
    event unless it is itself one of the listed dates, or one of them rolls
    back onto it. No month-end rule exists.
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
3. **Stable over time:** net positive in >= 60% of calendar years, and a
   median year > 0.
   - The 2013 stub counts only if it has >= 30 events. By the calendar alone
     it has 25, so it is excluded, leaving 2014-2020 (7 years).
   - 60% of 7 years therefore means **at least 5 positive years**.
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

- **Events (calendar only, no prices):** 519 gotobi days in the primary
  sample and 405 in the secondary.
  - These counts come **only** from the frozen holiday calendar and the G2
    rule. They are not performance data.
  - The run reports realized trade counts, which can be lower where bars
    are missing.
- **MDE formula:** MDE = 2.8416 x sd / sqrt(n), the one used for all prior
  power figures.
- **Per-trade sd (assumption):** no USDJPY dispersion has been published in
  this project. The assumption is 8-15 bps for a 1-hour hold. That is the
  published EURUSD multi-hour sd of 23-34 bps, scaled to one hour, with a
  margin for JPY volatility.

| sd (bps) | MDE primary (n = 519) | MDE secondary (n = 405) |
|---|---|---|
| 8 | 1.00 | 1.13 |
| 12 | 1.50 | 1.69 |
| 15 | 1.87 | 2.12 |

- **Design requirement (G5):** the central MDE (sd 12) must be <= 2 bps. It
  is 1.50 bps, so the requirement passes.
  - This is an **assumption-based design estimate**, not an empirical
    USDJPY volatility figure.
  - Achieved resolution is reported after the run, descriptively only.
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

## Decisions (account owner, 2026-09-27)

| # | decision | status |
|---|---|---|
| G1 | Window 00:00-01:00 UTC (09:00-10:00 JST) | **approved** |
| G2 | Gotobi = 5/10/15/20/25/30, rolled back to the preceding bank business day; no February month-end event | **amended and approved** |
| G3 | Primary = untouched 2013-08-26 to 2020-12-31; 2021-2026 descriptive only | **approved** |
| G4 | Qualification rules 1-5 (placebo difference replaces the drift control) | **approved** |
| G5 | Central MDE <= 2 bps (assumption-based); sd 8-15 as sensitivity | **approved** |
| G6 | Candidate C chosen over A | **approved** |

**Subjective prior (~15%, from the shortlist) has zero role.** It is a
documented judgement from before the freeze. It is not an input to
qualification, reporting or interpretation.

## Frozen parameters

```json
{
  "name": "usdjpy_gotobi",
  "version": 1,
  "status": "frozen",
  "symbol": "USDJPY.m",
  "data": {"file": "USDJPY.m_H1_201308230000_202609252300.csv",
           "sha256": "578b734606f674bfef3ca6c8758a11335fecf2258ea550c9c15bef0f9633d05f",
           "loader": {"tz": "Europe/Athens", "interval_hours": 1, "max_gap_days": 4, "trim_d1_prefix": true}},
  "calendar": {"file": "docs/hypotheses/assets/jp_bank_holidays_2013_2026.json",
               "sha256": "3fc1131a9d7ea4ea7f02325b43c289cb161fa773695f96c5282814621ee400be",
               "gotobi_days": [5, 10, 15, 20, 25, 30], "roll": "preceding_bank_business_day",
               "february_month_end_event": false, "dedupe": true},
  "trade": {"side": "long", "entry_bar_utc": "00:00", "exit_bar_utc": "01:00", "fill": "bar_open",
            "stop": null, "target": null, "requires_both_bars": true},
  "costs": {"spread_floor": 0.025, "slippage_ratio_of_floor": 0.16666666666666666, "commission": 0.0,
            "per_bar_spread_floor": true, "stress_multiplier": 2.0},
  "samples": {"primary": ["2013-08-26", "2020-12-31"], "secondary": ["2021-01-04", "2026-09-25"],
              "secondary_role": "descriptive_only"},
  "primary": {"min_t": 2.0, "placebo_welch_t_min": 2.0, "placebo_statistic": "gross_gotobi_minus_gross_placebo",
              "min_year_share": 0.6, "min_year_events": 30, "median_year_positive": true,
              "stress_net_positive": true, "min_trades": 400},
  "power": {"calendar_events_primary": 519, "calendar_events_secondary": 405, "design_mde_bps_central": 1.5,
            "sd_assumption_bps": [8, 12, 15], "requirement_bps": 2.0},
  "ledger": {"family_size_primary": 1, "adjustment": "confirmatory_untouched_data"}
}
```

## Gate 0 stop (2026-09-27): design infeasible as frozen, no result exists

What happened after the freeze (`6c4135d`), the code (`22931f9`) and the
verified data install (`5809637`):
- The **frozen loader's Gate 0 rejected the file**: gap_exceeds_max, a
  104-day gap. The run stopped before any trade or statistic was computed.
- To diagnose it, **only the date and time columns** were read. No price
  column was read.
- **Findings:**
  - Before **2019-06-07 16:00 server time** the export contains **daily
    bars, not H1**. The 2013 start in the file name covers daily history
    only.
  - There is one gap of more than 4 days: **2019-12-16 15:00 to 2020-03-30
    00:00** server time (104 days).
- **Consequence:** the untouched H1 sample (2019-06-10 to 2020-12-31,
  excluding the gap) has **92** gotobi events by the calendar. That is below
  the frozen minimum of 400 trades, and its central MDE of 3.56 bps is above
  the 2 bps requirement.
  - The v1 primary sample cannot be run as frozen.
  - v1 is **not** reported as a result.
  - Any continuation requires an approved **version 2** amendment, made
    before any USDJPY price is read.

## Explicitly excluded

- No other pairs; no other hours; no short side; no "post-fix reversal"
  variant (that would be a separate hypothesis).
- No volatility, trend or day-of-week filters.
- No change of window, day set or sample after any data is read.
