# QF-X Risk Specification

Risk is a separate subsystem. Strategy logic cannot choose account risk or bypass a rejection.

## Initial research limits

- Baseline risk: 0.25% of account equity
- Maximum normal risk: 0.35%
- Abnormal-volatility risk: 0.10%
- Marginal setup: 0%
- Aggregate open risk limit: 1%
- Initial daily loss limit: 1.5%

These are research defaults, not a promise of safety or profitability.

## Position sizing

Conceptually:

account risk / monetary loss per unit stop distance = position size

Production sizing must use the exact contract, tick, point, lot and currency economics of each instrument and broker.

## Stops

Stops should represent thesis invalidation and volatility conditions rather than arbitrary fixed distances.

## Portfolio controls

The risk engine must account for:

- Per-trade risk
- Aggregate open risk
- Correlated exposure
- Daily loss
- Drawdown
- Consecutive losses
- Abnormal volatility
- Spread/slippage anomalies
- Data integrity

## Prohibited defaults

- No martingale
- No uncontrolled averaging down
- No unbounded pyramiding

## Kill switches

Trading research should halt when feed/data integrity fails, spread or slippage becomes anomalous, volatility experiences an unvalidated shock, drawdown limits are breached, correlation risk becomes abnormal, or model integrity fails.
