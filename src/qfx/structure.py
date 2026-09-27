"""Descriptive market structure and liquidity features.

Every feature here is causal: a swing at bar ``i`` is only reported once
``i + lookback`` bars exist, and ``confirmed_at`` records that bar so callers
can never use a swing before it was knowable.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class SwingKind(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"


@dataclass(frozen=True)
class Swing:
    index: int
    price: float
    kind: SwingKind
    confirmed_at: int


@dataclass(frozen=True)
class LiquidityPool:
    kind: SwingKind
    price: float
    indices: tuple[int, ...]


@dataclass(frozen=True)
class Sweep:
    index: int
    pool_price: float
    kind: SwingKind


def find_swings(highs: Sequence[float], lows: Sequence[float], lookback: int = 2) -> list[Swing]:
    if len(highs) != len(lows):
        raise ValueError("High and low series must have equal length")
    if lookback < 1:
        raise ValueError("Lookback must be at least 1")
    swings: list[Swing] = []
    for i in range(lookback, len(highs) - lookback):
        left_h, right_h = highs[i - lookback : i], highs[i + 1 : i + lookback + 1]
        left_l, right_l = lows[i - lookback : i], lows[i + 1 : i + lookback + 1]
        if highs[i] > max(left_h) and highs[i] >= max(right_h):
            swings.append(Swing(i, highs[i], SwingKind.HIGH, i + lookback))
        if lows[i] < min(left_l) and lows[i] <= min(right_l):
            swings.append(Swing(i, lows[i], SwingKind.LOW, i + lookback))
    return swings


def known_swings(swings: Sequence[Swing], as_of: int) -> list[Swing]:
    """Swings confirmed on or before bar ``as_of``."""
    return [swing for swing in swings if swing.confirmed_at <= as_of]


def break_of_structure(closes: Sequence[float], swings: Sequence[Swing], index: int) -> SwingKind | None:
    """Return HIGH if the close at ``index`` breaks the latest known swing high,
    LOW if it breaks the latest known swing low, else None."""
    known = known_swings(swings, index - 1)
    last_high = next((s for s in reversed(known) if s.kind is SwingKind.HIGH), None)
    last_low = next((s for s in reversed(known) if s.kind is SwingKind.LOW), None)
    close = closes[index]
    if last_high is not None and close > last_high.price:
        return SwingKind.HIGH
    if last_low is not None and close < last_low.price:
        return SwingKind.LOW
    return None


def equal_levels(swings: Sequence[Swing], tolerance: float) -> list[LiquidityPool]:
    """Cluster same-kind swings within ``tolerance`` (absolute price) into pools."""
    if tolerance < 0:
        raise ValueError("Tolerance must be non-negative")
    pools: list[LiquidityPool] = []
    for kind in SwingKind:
        group = sorted((s for s in swings if s.kind is kind), key=lambda s: s.price)
        cluster: list[Swing] = []
        for swing in group:
            if cluster and swing.price - cluster[0].price > tolerance:
                if len(cluster) > 1:
                    pools.append(_pool(kind, cluster))
                cluster = []
            cluster.append(swing)
        if len(cluster) > 1:
            pools.append(_pool(kind, cluster))
    return pools


def _pool(kind: SwingKind, cluster: list[Swing]) -> LiquidityPool:
    price = max(s.price for s in cluster) if kind is SwingKind.HIGH else min(s.price for s in cluster)
    return LiquidityPool(kind, price, tuple(sorted(s.index for s in cluster)))


def detect_sweep(
    high: float, low: float, close: float, index: int, pool: LiquidityPool
) -> Sweep | None:
    """A sweep trades through a pool but closes back inside it. It is an event,
    not a reversal signal."""
    if index <= max(pool.indices):
        return None
    if pool.kind is SwingKind.HIGH and high > pool.price and close < pool.price:
        return Sweep(index, pool.price, pool.kind)
    if pool.kind is SwingKind.LOW and low < pool.price and close > pool.price:
        return Sweep(index, pool.price, pool.kind)
    return None
