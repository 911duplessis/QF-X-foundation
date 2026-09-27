"""Research decision pipeline.

DATA QUALITY -> REGIME -> VOLATILITY -> EDGE -> RISK -> DECISION

Every stage can only move the decision toward NO_TRADE. There is no order
placement here; the output is a research decision.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from .data_quality import check_candles
from .expectancy import EdgeEstimate, passes_ev_gate
from .models import Candle, DecisionState, MarketState, Regime, RiskDecision
from .regime import classify_regime
from .risk import RiskEngine
from .volatility import realized_volatility


@dataclass(frozen=True)
class AccountState:
    open_risk_fraction: float = 0.0
    daily_loss_fraction: float = 0.0
    drawdown_fraction: float = 0.0
    consecutive_losses: int = 0
    correlated_open_risk: float = 0.0


@dataclass(frozen=True)
class ResearchDecision:
    state: MarketState
    risk: RiskDecision


def percentile_rank(value: float, history: Sequence[float]) -> float:
    if not history:
        return 0.0
    return sum(1 for h in history if h <= value) / len(history)


def decide(
    symbol: str,
    candles: Sequence[Candle],
    edge: EdgeEstimate | None,
    account: AccountState = AccountState(),
    vol_history: Sequence[float] = (),
    abnormal_vol_percentile: float = 0.95,
    expected_interval: timedelta | None = None,
    spread_anomaly: bool = False,
    risk_engine: RiskEngine | None = None,
) -> ResearchDecision:
    engine = risk_engine or RiskEngine()

    def reject(regime: Regime, reason: str, decision: DecisionState = DecisionState.NO_TRADE, vol_pct: float = 0.0):
        risk = RiskDecision(False, 0.0, reason)
        return ResearchDecision(MarketState(symbol, regime, vol_pct, decision=decision, reason=reason), risk)

    report = check_candles(candles, expected_interval=expected_interval)
    if not report.passed:
        return reject(Regime.UNKNOWN, "data_quality:" + ",".join(report.issues))

    closes = [c.close for c in candles]
    regime = classify_regime(closes)
    if regime is Regime.UNKNOWN:
        return reject(regime, "insufficient_history")

    vol = realized_volatility(closes) if len(closes) >= 3 else 0.0
    vol_pct = percentile_rank(vol, vol_history)
    abnormal = bool(vol_history) and vol_pct >= abnormal_vol_percentile
    if abnormal and vol_pct >= 0.99:
        return reject(Regime.ABNORMAL, "volatility_outside_validated_bounds", vol_pct=vol_pct)

    if edge is None:
        return reject(regime, "no_edge_estimate", DecisionState.WATCH, vol_pct)
    ok, edge_reason = passes_ev_gate(edge)
    if not ok:
        return reject(regime, edge_reason, DecisionState.WATCH, vol_pct)

    risk = engine.evaluate(
        True,
        abnormal,
        account.open_risk_fraction,
        account.daily_loss_fraction,
        spread_anomaly=spread_anomaly,
        drawdown_fraction=account.drawdown_fraction,
        consecutive_losses=account.consecutive_losses,
        correlated_open_risk=account.correlated_open_risk,
    )
    if not risk.allowed:
        return ResearchDecision(
            MarketState(symbol, regime, vol_pct, decision=DecisionState.NO_TRADE, reason=risk.reason), risk
        )
    return ResearchDecision(
        MarketState(symbol, regime, vol_pct, decision=DecisionState.QUALIFIED, reason=f"{edge_reason};{risk.reason}"),
        risk,
    )
