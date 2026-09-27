# QF-X Trading Specification

## Instruments

### EURUSD
Primary context: higher-timeframe structure, USD/rates context, London/NY sessions, prior-day/week extremes, volatility and spread.

### XAUUSD
Primary context: USD, real-yield proxy, session structure, prior extremes, volatility acceleration, liquidity events and post-event acceptance/rejection.

### BTCUSD
Primary context: 24/7 market segmentation, US/CME references, realized volatility, funding/open interest/basis/liquidations where available, and broader liquidity/risk context.

## Structure

The engine may measure:

- Swing highs/lows
- Protected highs/lows
- Break of structure
- Displacement
- Failed breaks
- Range boundaries
- Prior day/week extremes

These are descriptive market features, not automatic trade signals.

## Liquidity

Candidate liquidity pools include equal highs/lows, swing extremes, session extremes, prior day/week extremes and range extremes.

A sweep is an event. It does not guarantee reversal.

## Strategy hypotheses

Initial independent hypotheses:

1. Trend continuation
2. Liquidity reversal
3. Volatility expansion

Each hypothesis must be evaluated conditionally by market regime.

## Expected value gate

A setup must be evaluated using:

EV = P(win) * AvgWin - P(loss) * AvgLoss - Costs

Probability and payoff estimates must be derived from appropriately separated historical samples.

## No-trade conditions

The engine should reject new research opportunities when data quality is insufficient, spread or slippage is abnormal, major scheduled-event rules apply, volatility is outside validated bounds, correlated exposure is excessive, model confidence is uncalibrated, or the thesis is structurally invalidated.
