from collections.abc import Sequence
from math import sqrt


def true_ranges(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> list[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("OHLC series must have equal length")
    if not highs:
        return []
    result = [highs[0] - lows[0]]
    for high, low, previous_close in zip(highs[1:], lows[1:], closes[:-1]):
        result.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return result


def realized_volatility(closes: Sequence[float], annualization: float = 1.0) -> float:
    if len(closes) < 2:
        raise ValueError("At least two closes are required")
    if annualization <= 0:
        raise ValueError("Annualization must be positive")
    returns = [(current / previous) - 1.0 for previous, current in zip(closes, closes[1:])]
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    return sqrt(variance * annualization)
