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

## Design principle

QF-X is not a single trading strategy. It is a market-state engine that decides when a strategy hypothesis is appropriate and when **NO_TRADE** is the correct decision.

The deterministic layer owns data integrity, structure, liquidity, volatility, risk and safety controls. A future statistical layer may estimate conditional expectancy, but it must never bypass deterministic risk controls.

## Safety boundary

No live-trading capability belongs in the foundation until the validation gates in docs/VALIDATION_PROTOCOL.md have been passed.