# Next-hypothesis shortlist (2026-09-27)

Status: **PROPOSAL for the account owner's choice.** This is not a
specification, and nothing here is frozen or coded. **No price data was
read to prepare it.** The power figures use only the formula and dispersion
figures already published in `power_analysis.json` and
`fx_session_persistence_v1.md`, plus the assumptions stated with each
candidate.

## Selection principles

These follow from the test ledger (17 tests, 0 qualified) and the power
analysis.

1. **Mechanism first.** Each candidate names who is on the other side and
   why they would pay. None of them came from inspecting data.
2. **No parameter search.** Every candidate's direction and timing are fixed
   by its mechanism. There is no grid and no walk-forward selection: one
   pre-registered test with no search inside it. The last 17 tests each
   searched 4-9 cells.
3. **Confirm on untouched data (ledger rule, option 2).** The seven FX majors
   are used for 2021-01 to 2026-09 (EURUSD back to 2020-10). **H1 history
   before 2020-10 has never been read in this project.**
   - If the broker provides it, it becomes the primary test sample.
   - 2021-2026 is then secondary: it is already contaminated, so it carries
     no qualification weight.
4. **Costs are the binding constraint.** Round trips are 0.9-3.3 bps
   (USDJPY 2.12). The mechanism must plausibly produce a **gross** move of
   several bps per event, not merely a positive one.

## Candidates

| | A. Month-end London-fix hedge rebalancing | B. Home-hours currency depreciation | C. USDJPY gotobi-day Tokyo fix |
|---|---|---|---|
| **Mechanism / counterparty** | Foreign holders of US equities (and US holders of foreign equities) who hedge FX re-balance their hedges at the month-end WM/Reuters 16:00 London fix. After a month of US equity outperformance, foreign hedgers must sell additional USD forward, and the reverse after underperformance. They trade for size and certainty at the benchmark, not for price, and dealers are paid to absorb the flow. | Local importers and investors buy foreign currency during their own business hours, so each currency tends to weaken while its home market is open and recover afterwards. Dealers absorbing the order flow are compensated. | Japanese importers settle USD purchases at the 09:55 JST Tokyo fix, concentrated on "gotobi" days (the 5th, 10th, 15th, 20th, 25th and month-end, rolled to the prior business day). Predictable, price-insensitive USD demand lifts USDJPY into the fix. |
| **Rule (fixed by the mechanism)** | On the last business day of each month, hold USD in the direction implied by the sign of month-to-date US-minus-foreign equity returns, from the 15:00 London bar open to the 16:00 bar open, in all 7 pairs. | Each day and pair, hold short the non-USD currency during its home hours, one fixed window per currency, set from the mechanism before any data. | Long USDJPY from the 00:00 UTC bar open (09:00 JST) to the 01:00 bar open (10:00 JST), on gotobi days only. Non-gotobi days are the built-in placebo. |
| **Extra data needed** | A US and a non-US equity index (broker CFDs such as US500 / GER40 / JP225), D1 is enough | none | none, plus a Japanese holiday list (public, fixed in advance) |
| **Events, pre-2021 (if 2010-2020 available)** | 132 month-ends x 7 pairs | ~2,600 days x 7 pairs | ~700 gotobi days x 1 pair |
| **Pre-data MDE, primary sample** | **2.1-4.9 bps** (sd 10-23, rho 0.7) | **0.6-1.3 bps** (sd 15-30, rho 0.5) | **0.9-1.6 bps** (sd 8-15) |
| **Pre-data MDE, 2021-2026 only** | 3.0-6.8 | - (contaminated, see below) | 1.2-2.2 |
| **Round-trip cost vs. MDE** | 1.9 bps average: MDE is above cost | 1.9 bps: MDE is below cost, so the risk is being well-measured but unprofitable | 2.12 bps: MDE is below cost |
| **Placebo / control** | Same window on non-month-end days, and on month-ends with the sign reversed | Same windows in the other currencies' home hours | The same hour on non-gotobi days (clean, and needs no new machinery) |
| **Ledger overlap** | Tests 2, 5, 8, 11, 14, 17 (EURUSD); 17 (other six) | Same, plus **direct contamination**: test 17's drift control replayed random-day London-session holds (control gross about 0) | Test 17 only (USDJPY, London hours; the Tokyo 00:00 UTC hour was never traded) |
| **Family size / adjustment** | 7 on EURUSD. Confirmatory on pre-2021, else Holm across the family | 7. Confirmatory on pre-2021 only; 2021-2026 unusable | 2. Confirmatory on pre-2021; 2021-2026 secondary |
| **Main risks** | Low event count; post-2015 fix reform (5-minute window) may have spread the flow out; equity-index data adds a second dataset | The effect is likely smaller than the retail spread; the London session overlaps what test 17 already saw | Effect may have been arbitraged since publication; a single pair; costs are close to the plausible effect |
| **Subjective prior of qualifying** (judgement, not a calculation) | ~10% | ~5% | ~15% |

## Recommendation: C (USDJPY gotobi-day Tokyo fix)

- **Cleanest test here:**
  - one pair and one fixed hour, with no parameters;
  - a built-in placebo (non-gotobi days at the same hour), which replaces the
    drift machinery with a direct difference-in-means;
  - the least ledger overlap: that hour of USDJPY was never traded;
  - no second dataset.
- **Its weakness is cost.** It pays only if the gross effect clears 2.12
  bps per trade. The primary outcome must therefore be **net** of costs, as
  always.
- **Alternative: A.** It has the strongest economics per event, but the
  fewest events, and it needs equity-index data.
- **B is not recommended.** The likely effect is below the retail spread,
  and the most relevant data is already contaminated by test 17.

## Blocking question before any draft

**How far back does the broker's H1 history go?** The whole
untouched-data design depends on it.

- Check it without reading prices: in MT5, set a USDJPY.m H1 export to start
  at 2010-01-01, and report **only the start date in the file name** it
  would produce. Do not upload the file.
- If H1 starts around 2021, there is no untouched pre-2021 sample. The design
  then needs a different confirmatory route: Holm-adjusted thresholds, or
  waiting for new data after 2026-09-25.
