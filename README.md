# QF-X Foundation

QF-X is a research-first market-state, opportunity, risk and validation platform for **EURUSD, XAUUSD and BTCUSD**.

> Observe -> classify state -> map structure/liquidity -> measure volatility -> test opportunity -> size risk -> validate -> only then consider execution.

## Status

**Foundation phase — research only.** This repository deliberately does not contain broker credentials, order placement or autonomous live execution.

## Initial horizons

- Macro: Daily / 4H
- Regime: 4H / 1H
- Setup: 15M / 5M
- Execution research: 5M initially

The objective is not maximum trade frequency. The objective is a repeatable conditional edge after costs, slippage, regime changes and realistic execution assumptions.

## Repository map

- docs/ — architecture, trading specification, risk specification and validation protocol
- config/ — instrument and risk configuration
- src/qfx/ — deterministic research engine foundations
- tests/ — executable invariants and regression tests
- data/ — local research datasets; ignored by default

## Implemented modules

| Module | Role |
|---|---|
| `data_quality` | Gate 0: OHLC validity, tz-aware timestamps, duplicates, ordering, gaps, frozen prices, stale feed |
| `regime` | Deterministic baseline regime classifier |
| `volatility` | True range, realized volatility |
| `structure` | Causal swings (with `confirmed_at`), break of structure, equal-level liquidity pools, sweeps |
| `expectancy` | EV gate after costs, with minimum sample size |
| `sizing` | Instrument-aware position sizing, always rounds down |
| `risk` | Hard limits and kill switches; correlated exposure shares the open-risk limit |
| `backtest.bracket` | Stop/target/time-stop execution: stop first on same-bar touch, gaps fill at the open, R per trade |
| `backtest` | Gate 2 harness: delayed fills, per-bar spread (floor), commission, slippage; no look-ahead |
| `backtest.mt5` | MT5 export loader: server time -> UTC, spread points -> price, D1 prefix trimming, Gate 0 |
| `research.sweep` | Liquidity Sweep Reversal v1, checked against its frozen specification by test |
| `research` | Causal features, hypotheses, chronological splits, rolling walk-forward with stability metrics, qualification rules, JSON + markdown reports |
| `pipeline` | DATA QUALITY -> REGIME -> VOLATILITY -> EDGE -> RISK -> research decision (default NO_TRADE) |

Run tests: `pip install -e .[test] && pytest`

## Data

`data/mt5/` holds MT5 H1 exports (EURUSD, XAUUSD, BTCUSD). Audit them with:

    python -m qfx.backtest.audit data/mt5/*.csv

Verified properties of these exports:

- Broker server time is `Europe/Athens` (EET/EEST, EU DST dates): the FX week opens at Sun 17:00 New York in all non-holiday weeks.
- Each file begins with ~7-10 months of D1 bars before H1 history starts; the loader trims and reports them.
- BTCUSD (24/7) has one ambiguous bar per spring DST switch; the loader drops it and reports the count.
- `<SPREAD>` is the bar's quoted spread in points; the engine uses it only as a floor above the configured spread.

## Research results

Interpretation lives in the [research log](docs/results/RESEARCH_LOG.md); generated reports sit next to it.

- Walk-forward: Liquidity Sweep Reversal v1 (H1), [long](docs/results/walkforward_sweep_reversal_long.md) / [short](docs/results/walkforward_sweep_reversal_short.md) (+ `.json`): **no demonstrated edge** in either direction on any instrument; EURUSD edge bounded at about +1 bps/trade. Pre-registered in [docs/hypotheses/](docs/hypotheses/liquidity_sweep_reversal_v1.md). Reproduce with `python -m qfx.research.walkforward --hypothesis sweep_reversal_long` (or `_short`) plus `--report`/`--json`.
- [Walk-forward: trend continuation (H1)](docs/results/walkforward_trend_continuation.md) (+ `.json`): **no demonstrated edge** on EURUSD, XAUUSD or BTCUSD across 6-7 rolling test windows each. Reproduce with `python -m qfx.research.walkforward --report docs/results/walkforward_trend_continuation.md --json docs/results/walkforward_trend_continuation.json`.
- [Baseline: trend continuation (H1)](docs/results/baseline_trend_continuation.md): single split, superseded by the walk-forward. Reproduce with `python -m qfx.research.baseline --report docs/results/baseline_trend_continuation.md`.

## Design principle

QF-X is not a single trading strategy. It is a market-state engine that decides when a strategy hypothesis is appropriate and when **NO_TRADE** is the correct decision.

The deterministic layer owns data integrity, structure, liquidity, volatility, risk and safety controls. A future statistical layer may estimate conditional expectancy, but it must never bypass deterministic risk controls.

## Safety boundary

No live-trading capability belongs in the foundation until the validation gates in docs/VALIDATION_PROTOCOL.md have been passed.