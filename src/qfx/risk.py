from dataclasses import dataclass

from .models import RiskDecision


@dataclass(frozen=True)
class RiskConfig:
    baseline_fraction: float = 0.0025
    maximum_fraction: float = 0.0035
    abnormal_fraction: float = 0.0010
    max_open_risk: float = 0.01
    max_daily_loss: float = 0.015
    max_drawdown: float = 0.06
    max_consecutive_losses: int = 4
    correlation_threshold: float = 0.7


class RiskEngine:
    """Hard rejections are evaluated before any sizing. Strategy logic may
    request risk but can never exceed the configured maximum."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()

    def evaluate(
        self,
        setup_valid: bool,
        abnormal_volatility: bool,
        open_risk_fraction: float,
        daily_loss_fraction: float,
        *,
        data_ok: bool = True,
        spread_anomaly: bool = False,
        drawdown_fraction: float = 0.0,
        consecutive_losses: int = 0,
        correlated_open_risk: float = 0.0,
        marginal_setup: bool = False,
        requested_fraction: float | None = None,
    ) -> RiskDecision:
        if not data_ok:
            return RiskDecision(False, 0.0, "data_integrity_failure")
        if not setup_valid:
            return RiskDecision(False, 0.0, "setup_invalid")
        if marginal_setup:
            return RiskDecision(False, 0.0, "marginal_setup")
        if spread_anomaly:
            return RiskDecision(False, 0.0, "spread_slippage_anomaly")
        if drawdown_fraction >= self.config.max_drawdown:
            return RiskDecision(False, 0.0, "drawdown_limit")
        if consecutive_losses >= self.config.max_consecutive_losses:
            return RiskDecision(False, 0.0, "consecutive_loss_limit")
        if daily_loss_fraction >= self.config.max_daily_loss:
            return RiskDecision(False, 0.0, "daily_loss_limit")
        if open_risk_fraction >= self.config.max_open_risk:
            return RiskDecision(False, 0.0, "aggregate_open_risk_limit")

        if abnormal_volatility:
            fraction, reason = self.config.abnormal_fraction, "abnormal_volatility_reduced_risk"
        elif requested_fraction is not None:
            if requested_fraction < 0:
                raise ValueError("Requested risk fraction must be non-negative")
            fraction = min(requested_fraction, self.config.maximum_fraction)
            reason = "requested_risk_capped" if fraction < requested_fraction else "requested_risk"
        else:
            fraction, reason = self.config.baseline_fraction, "baseline_risk"

        # Correlated exposure counts as shared risk against the aggregate limit.
        headroom = self.config.max_open_risk - open_risk_fraction - correlated_open_risk
        if headroom <= 0:
            return RiskDecision(False, 0.0, "correlated_exposure_limit")
        if fraction > headroom:
            return RiskDecision(True, headroom, "reduced_to_open_risk_headroom")
        return RiskDecision(True, fraction, reason)


def correlated_risk(
    symbol: str,
    open_positions: dict[str, float],
    correlations: dict[tuple[str, str], float],
    threshold: float = 0.7,
) -> float:
    """Sum open risk of positions whose |correlation| with ``symbol`` meets
    ``threshold``, weighted by |correlation|. The symbol's own open risk is
    excluded because it is already counted in aggregate open risk."""
    total = 0.0
    for other, risk in open_positions.items():
        if other == symbol:
            continue
        rho = correlations.get((symbol, other), correlations.get((other, symbol), 0.0))
        if abs(rho) >= threshold:
            total += abs(rho) * risk
    return total
