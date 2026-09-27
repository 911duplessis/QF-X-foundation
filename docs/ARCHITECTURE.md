# QF-X Architecture

QF-X is a research-first market-state, opportunity, risk and validation platform for EURUSD, XAUUSD and BTCUSD.

## Decision order

1. Market state
2. Structure and liquidity
3. Volatility and session context
4. Valid strategy hypotheses
5. Expected edge after costs
6. Smallest defensible risk
7. Research decision

A valid outcome is **NO TRADE**.

## Pipeline

MARKET DATA -> DATA QUALITY -> REGIME -> STRUCTURE/LIQUIDITY/VOLATILITY -> SESSION/CORRELATION/MACRO -> OPPORTUNITY -> STRATEGY HYPOTHESES -> RISK -> RESEARCH DECISION -> JOURNAL/METRICS -> VALIDATION

## Safety boundary

The foundation contains no broker credentials, order placement, or autonomous live execution. Any future execution adapter must pass the validation gates before deployment.

## Core invariants

- No look-ahead bias.
- No future candle information.
- Explicit thesis invalidation.
- Risk is evaluated before reward.
- Spread, commission, slippage and execution delay are modelled.
- Correlated exposure counts as shared risk.
- Backtest performance is not treated as proof of future profitability.
