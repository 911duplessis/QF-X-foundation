from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Optional


class DecisionState(str, Enum):
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"
    QUALIFIED = "QUALIFIED"
    INVALIDATED = "INVALIDATED"


class Regime(str, Enum):
    UNKNOWN = "UNKNOWN"
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    COMPRESSION = "COMPRESSION"
    EXPANSION = "EXPANSION"
    ABNORMAL = "ABNORMAL"


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

    def validate(self) -> None:
        values = (self.open, self.high, self.low, self.close)
        if not all(isfinite(value) for value in values):
            raise ValueError("OHLC values must be finite")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC relationship")
        if self.high < self.low:
            raise ValueError("High cannot be below low")


@dataclass(frozen=True)
class MarketState:
    symbol: str
    regime: Regime
    volatility_percentile: float = 0.0
    trend_strength: float = 0.0
    liquidity_score: float = 0.0
    decision: DecisionState = DecisionState.NO_TRADE
    reason: str = ""


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    risk_fraction: float
    reason: str
