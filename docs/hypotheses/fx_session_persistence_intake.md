# FX Session Directional Persistence: universe capture and data intake log

Status: **intake record**. No specification is frozen, and no code exists
for this hypothesis. This file records what was received, and what was and
was not inspected, before the specification is drafted.

## Candidate universe (7 USD majors, no crosses)

EURUSD.m, GBPUSD.m, USDJPY.m, USDCHF.m, AUDUSD.m, USDCAD.m, NZDUSD.m.

**Evidence:** the MT5 terminal's own H1 export filenames (below) establish
that the broker offers all seven `.m` symbols with H1 history from at least
2021-01-04 00:00 server time to 2026-09-25 23:00 server time. The Market Watch
screenshot referred to by the account owner did not arrive, so it is not used.

## Early export received (2026-09-27): QUARANTINED, UNREAD

The account owner uploaded a single archive containing H1 price history for
all seven pairs **before** the specification was drafted. That is out of the
agreed order ("do not export H1 history yet").

Handling:
- only the archive's file list and sizes were read;
- **no file inside was extracted or opened**; no prices, returns, sessions or
  signals have been examined;
- the archive is kept outside the repository until the specification is frozen;
- at freeze, the files used must be byte-identical to this archive.

| item | value |
|---|---|
| archive (as uploaded) | `GBPUSD.m_H1_202101040000_202609252300.zip` |
| archive sha256 | `507058426d86f359097f438a7837b3ff55e115954d9569b441623b51cf10d3ab` |
| size | 4,038,665 bytes |

| entry | uncompressed bytes |
|---|---|
| AUDUSD.m_H1_202101040000_202609252300.csv | 2,230,456 |
| EURUSD.m_H1_202101040000_202609252300.csv | 2,221,913 |
| GBPUSD.m_H1_202101040000_202609252300.csv | 2,231,098 |
| NZDUSD.m_H1_202101040000_202609252300.csv | 2,243,273 |
| USDCAD.m_H1_202101040000_202609252300.csv | 2,243,426 |
| USDCHF.m_H1_202101040000_202609252300.csv | 2,230,408 |
| USDJPY.m_H1_202101040000_202609252300.csv | 2,242,959 |

Note: the export start (2021-01-04, the first Monday of 2021) appears to be a
chosen export setting, not the broker's earliest history. Any
history-length rule in the specification will be evaluated against these
files as exported.

## Prior information already in this project (for disclosure and power only)

- **EURUSD.m** H1 data (2020-2026) is already in `data/mt5/`. It was used in the
  trend, sweep and volatility-expansion walk-forwards, including coarse
  **session breakdowns of EURUSD trend-continuation trades**. This is a
  contamination disclosure for EURUSD; the other six pairs have not been
  analysed in this project.
- The pre-data power calculation will use only **already-published**
  per-trade dispersion figures (`docs/results/power_analysis.json`), not new
  computations on any FX data.

## Capture completed (2026-09-27)

- MT5 Specification windows for all seven pairs, each with the full Market
  Watch panel showing bid/ask for all seven, stored as
  `assets/fx_spec_<PAIR>_2026-09-27.png` (hashes in the draft spec).
- Quotes are identical across the seven screenshots (13:05-13:08 server,
  Sunday): these are Friday-close quotes.

## Still required before freeze

- Account-owner decisions D1-D7 in `fx_session_persistence_v1.md`.
