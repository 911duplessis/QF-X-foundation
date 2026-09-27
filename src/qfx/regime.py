from collections.abc import Sequence

from .models import Regime


def classify_regime(closes: Sequence[float]) -> Regime:
    """Deterministic baseline classifier; not an alpha model."""
    if len(closes) < 2:
        return Regime.UNKNOWN
    start, end = closes[0], closes[-1]
    if start <= 0:
        raise ValueError("Prices must be positive")
    change = (end - start) / start
    if abs(change) <= 0.002:
        return Regime.COMPRESSION
    if change >= 0.005:
        return Regime.TREND_UP
    if change <= -0.005:
        return Regime.TREND_DOWN
    return Regime.RANGE
