"""Causal feature series: value ``i`` uses only bars ``0..i``.

Computed once over a whole series for speed. Causality is enforced by test:
recomputing on a truncated series must reproduce the same prefix.
"""
from __future__ import annotations

from collections.abc import Sequence
from math import log, nan, sqrt


def log_returns(closes: Sequence[float]) -> list[float]:
    out = [0.0]
    for prev, cur in zip(closes, closes[1:]):
        if prev <= 0 or cur <= 0:
            raise ValueError("Prices must be positive")
        out.append(log(cur / prev))
    return out


def ewma_vol(returns: Sequence[float], halflife: float) -> list[float]:
    """EWMA standard deviation of per-bar log returns (zero-mean)."""
    if halflife <= 0:
        raise ValueError("Half-life must be positive")
    alpha = 1.0 - 0.5 ** (1.0 / halflife)
    var = nan
    out: list[float] = []
    for i, r in enumerate(returns):
        if i == 0:
            out.append(nan)
            continue
        var = r * r if var != var else (1 - alpha) * var + alpha * r * r
        out.append(sqrt(var))
    return out


def trend_z(closes: Sequence[float], lookback: int, vol: Sequence[float]) -> list[float]:
    """Log move over ``lookback`` bars divided by expected move
    ``vol * sqrt(lookback)``. Instrument-agnostic trend strength."""
    if lookback < 1:
        raise ValueError("Lookback must be at least 1")
    out: list[float] = []
    for i, c in enumerate(closes):
        v = vol[i]
        if i < lookback or v != v or v <= 0:
            out.append(nan)
        else:
            out.append(log(c / closes[i - lookback]) / (v * sqrt(lookback)))
    return out
