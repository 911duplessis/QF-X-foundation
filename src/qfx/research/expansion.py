"""Volatility Expansion v1, implemented to the frozen specification in
``docs/hypotheses/volatility_expansion_v1.md``. Do not change a rule or a
value here without a new specification version; a test enforces the match.

Contamination disclosure (from the specification): compression is a
low-volatility condition, and a post-hoc low-volatility observation on the
same test windows is recorded in the research log. The compression threshold
and lookback are therefore fixed here and are not grid parameters.
"""
from __future__ import annotations

from bisect import bisect_left, insort
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from math import nan

from ..backtest.bracket import BracketSignal
from ..backtest.types import Bar, ExecutionCosts, Side
from .features import ewma_vol, log_returns
from .sweep import Setup, sweep_signal

SPEC_PATH = "docs/hypotheses/volatility_expansion_v1.md"


@dataclass(frozen=True)
class ExpansionFixed:
    compression_percentile: float = 0.2
    compression_lookback_bars: int = 500
    compression_rule: str = "count(reference_width < width) / lookback <= compression_percentile"
    max_hold_bars: int = 48
    vol_long_halflife: float = 240.0
    vol_shock_halflife: float = 6.0
    vol_shock_ratio: float = 2.5
    max_spread_to_stop: float = 0.25
    same_bar_stop_target: str = "stop_first"  # implemented in backtest.bracket
    delay_bars: int = 1  # ExecutionCosts default; enforced >= 1


FIXED = ExpansionFixed()
GRID_AXES = {"box_bars": (12, 24), "stop": ("box_opposite", "box_mid"), "target_r": (1.0, 2.0)}
HYPOTHESES = {"vol_expansion_long": Side.LONG, "vol_expansion_short": Side.SHORT}


def grid() -> tuple[dict, ...]:
    keys = list(GRID_AXES)
    return tuple(dict(zip(keys, values)) for values in product(*GRID_AXES.values()))


def box_series(bars: Sequence[Bar], n: int) -> tuple[list[float], list[float]]:
    """Box high/low over bars e-n+1 .. e for each end bar e (NaN until complete)."""
    if n < 1:
        raise ValueError("box_bars must be at least 1")
    highs, lows = [nan] * len(bars), [nan] * len(bars)
    for e in range(n - 1, len(bars)):
        window = bars[e - n + 1 : e + 1]
        highs[e] = max(b.high for b in window)
        lows[e] = min(b.low for b in window)
    return highs, lows


def compression_flags(bars: Sequence[Bar], n: int, fixed: ExpansionFixed = FIXED) -> list[bool]:
    """``flags[j]``: the box ending at j-1 is compressed relative to the L boxes
    ending at j-2 .. j-1-L. Uses a sliding sorted window; equivalent to the
    brute-force rank (tested)."""
    L = fixed.compression_lookback_bars
    highs, lows = box_series(bars, n)
    width = [h - l for h, l in zip(highs, lows)]
    flags = [False] * len(bars)
    j0 = n - 1 + L + 1  # first j whose reference set (ends j-1-L .. j-2) is complete
    if j0 >= len(bars):
        return flags
    window = sorted(width[n - 1 : j0 - 1])
    for j in range(j0, len(bars)):
        if j > j0:
            insort(window, width[j - 2])
            del window[bisect_left(window, width[j - 2 - L])]
        flags[j] = bisect_left(window, width[j - 1]) / L <= fixed.compression_percentile
    return flags


def find_setups(
    bars: Sequence[Bar],
    side: Side,
    box_bars: int,
    stop: str,
    fixed: ExpansionFixed = FIXED,
    flags: Sequence[bool] | None = None,
) -> list[Setup | None]:
    """Setup (or None) per signal bar j; depends only on bars 0..j."""
    if stop not in ("box_opposite", "box_mid"):
        raise ValueError("stop must be 'box_opposite' or 'box_mid'")
    flags = flags if flags is not None else compression_flags(bars, box_bars, fixed)
    highs, lows = box_series(bars, box_bars)
    rets = log_returns([b.close for b in bars])
    long_vol, shock_vol = ewma_vol(rets, fixed.vol_long_halflife), ewma_vol(rets, fixed.vol_shock_halflife)
    out: list[Setup | None] = [None] * len(bars)
    for j in range(1, len(bars)):
        if not flags[j]:
            continue
        bh, bl, close = highs[j - 1], lows[j - 1], bars[j].close
        if side is Side.LONG and not close > bh:
            continue
        if side is Side.SHORT and not close < bl:
            continue
        lv, sv = long_vol[j], shock_vol[j]
        if lv != lv or sv != sv or sv > fixed.vol_shock_ratio * lv:
            continue  # warm-up or volatility-shock gate
        if stop == "box_mid":
            level = (bh + bl) / 2
        else:
            level = bl if side is Side.LONG else bh
        out[j] = Setup(level, close)
    return out


def expansion_signal(
    bars: Sequence[Bar], setups: Sequence[Setup | None], side: Side, target_r: float, costs: ExecutionCosts, offset: int = 0
) -> BracketSignal:
    """Same cost gate and bracket order construction as the sweep hypothesis,
    with this hypothesis's frozen values."""
    return sweep_signal(bars, setups, side, target_r, costs, offset, FIXED)  # type: ignore[arg-type]
