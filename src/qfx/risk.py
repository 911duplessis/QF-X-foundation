from dataclasses import dataclass

from .models import RiskDecision


@dataclass(frozen=True)
class RiskConfig:
    baseline_fraction: float = 0.0025
    maximum_fraction: float = 0.0035
    abnormal_fraction: float = 0.0010
    max_open_risk: float = 0.01
    max_daily_loss: float = 0.015


class RiskEngine:
    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()

    def evaluate(
        self,
        setup_valid: bool,
        abnormal_volatility: bool,
        open_risk_fraction: float,
        daily_loss_fraction: float,
    ) -> RiskDecision:
        if not setup_valid:
            return RiskDecision(False, 0.0, "setup_invalid")
        if open_risk_fraction >= self.config.max_open_risk:
            return RiskDecision(False, 0.0, "aggregate_open_risk_limit")
        if daily_loss_fraction >= self.config.max_daily_loss:
            return RiskDecision(False, 0.0, "daily_loss_limit")
        if abnormal_volatility:
            return RiskDecision(True, self.config.abnormal_fraction, "abnormal_volatility_reduced_risk")
        return RiskDecision(True, self.config.baseline_fraction, "baseline_risk")
