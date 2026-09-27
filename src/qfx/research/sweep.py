"""Liquidity Sweep Reversal v1, implemented to the frozen specification in
``docs/hypotheses/liquidity_sweep_reversal_v1.md``. Do not change a rule or a
value here without a new specification version; a test enforces the match.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from math import nan

from ..backtest.bracket import BracketOrder, BracketSignal
from ..backtest.types import Bar, ExecutionCosts, Side
from ..structure import SwingKind, find_swings
from ..volatility import true_ranges
from .features import ewma_vol, log_returns

SPEC_PATH = "docs/hypotheses/liquidity_sweep_reversal_v1.md"


@dataclass(frozen=True)
class SweepFixed:
    level_max_age_bars: int = 120
    confirmation_window_bars: int = 6
    atr_period: int = 24
    stop_atr_mult: float = 0.5
    max_hold_bars: int = 48
    vol_long_halflife: float = 240.0
    vol_shock_halflife: float = 6.0
    vol_shock_ratio: float = 2.5
    max_spread_to_stop: float = 0.25
    same_bar_stop_target: str = "stop_first"  # implemented in backtest.bracket
    delay_bars: int = 1  # ExecutionCosts default; enforced >= 1


FIXED = SweepFixed()
GRID_AXES = {"swing_lookback": (3, 5), "confirmation": ("none", "structure"), "target_r": (1.0, 2.0)}
HYPOTHESES = {"sweep_reversal_long": Side.LONG, "sweep_reversal_short": Side.SHORT}


def grid() -> tuple[dict, ...]:
    keys = list(GRID_AXES)
    return tuple(dict(zip(keys, values)) for values in product(*GRID_AXES.values()))


def atr(bars: Sequence[Bar], period: int) -> list[float]:
    """Simple mean of the last ``period`` true ranges ending at each bar."""
    tr = true_ranges([b.high for b in bars], [b.low for b in bars], [b.close for b in bars])
    out: list[float] = []
    total = 0.0
    for i, value in enumerate(tr):
        total += value
        if i >= period:
            total -= tr[i - period]
        out.append(total / period if i >= period - 1 else nan)
    return out


@dataclass(frozen=True)
class Setup:
    """A completed setup at its signal bar, before the cost gate."""

    stop: float
    signal_close: float


def find_setups(
    bars: Sequence[Bar], side: Side, swing_lookback: int, confirmation: str, fixed: SweepFixed = FIXED
) -> list[Setup | None]:
    """Setup (or None) per bar. ``side`` is the reversal direction: SHORT trades
    buy-side sweeps of swing highs, LONG trades sell-side sweeps of swing lows.
    Entry ``g`` depends only on bars ``0..g``."""
    if confirmation not in ("none", "structure"):
        raise ValueError("confirmation must be 'none' or 'structure'")
    short = side is Side.SHORT
    kind = SwingKind.HIGH if short else SwingKind.LOW
    highs, lows = [b.high for b in bars], [b.low for b in bars]
    swings = sorted((s for s in find_swings(highs, lows, swing_lookback) if s.kind is kind), key=lambda s: s.confirmed_at)
    atr_v = atr(bars, fixed.atr_period)
    rets = log_returns([b.close for b in bars])
    long_vol, shock_vol = ewma_vol(rets, fixed.vol_long_halflife), ewma_vol(rets, fixed.vol_shock_halflife)

    out: list[Setup | None] = [None] * len(bars)
    active: list[tuple[int, float]] = []  # (swing bar index, level price)
    next_swing = 0
    pending: tuple[int, float, float] | None = None  # (sweep bar, extreme, opposite extreme)

    for g, bar in enumerate(bars):
        # Levels confirmed on or before the previous bar become sweepable now.
        while next_swing < len(swings) and swings[next_swing].confirmed_at <= g - 1:
            s = swings[next_swing]
            active.append((s.index, s.price))
            next_swing += 1
        active = [(i, p) for i, p in active if g - i <= fixed.level_max_age_bars]

        signal_extreme: float | None = None
        # 1. A pending structure setup confirms, is cancelled, or expires.
        if pending is not None:
            sweep_bar, extreme, opposite = pending
            beyond = bar.high > extreme if short else bar.low < extreme
            confirmed = bar.close < opposite if short else bar.close > opposite
            if beyond:
                pending = None
            elif confirmed:
                signal_extreme, pending = extreme, None
            elif g - sweep_bar >= fixed.confirmation_window_bars:
                pending = None

        # 2. Sweeps and breakouts of active levels on this bar.
        if short:
            swept = [p for _, p in active if bar.high > p and bar.close < p]
            broken = [p for _, p in active if bar.close > p]
        else:
            swept = [p for _, p in active if bar.low < p and bar.close > p]
            broken = [p for _, p in active if bar.close < p]
        if swept or broken:
            gone = set(swept) | set(broken)
            active = [(i, p) for i, p in active if p not in gone]
        if swept:
            extreme, opposite = (bar.high, bar.low) if short else (bar.low, bar.high)
            if confirmation == "none":
                signal_extreme = extreme
            else:
                pending = (g, extreme, opposite)  # a newer sweep replaces a pending one

        if signal_extreme is None:
            continue
        a, lv, sv = atr_v[g], long_vol[g], shock_vol[g]
        if a != a or lv != lv or sv != sv:
            continue  # warm-up
        if sv > fixed.vol_shock_ratio * lv:
            continue  # volatility-shock gate
        stop = signal_extreme + fixed.stop_atr_mult * a if short else signal_extreme - fixed.stop_atr_mult * a
        out[g] = Setup(stop, bar.close)
    return out


def sweep_signal(
    bars: Sequence[Bar],
    setups: Sequence[Setup | None],
    side: Side,
    target_r: float,
    costs: ExecutionCosts,
    offset: int = 0,
    fixed: SweepFixed = FIXED,
) -> BracketSignal:
    """Applies the cost gate at the signal bar: spread (max of per-bar spread and
    the configured floor) must not exceed ``max_spread_to_stop`` x the distance
    from the signal close to the stop."""

    def signal(view: Sequence[Bar], i: int) -> BracketOrder | None:
        g = i + offset
        setup = setups[g]
        if setup is None:
            return None
        bar = bars[g]
        spread = max(bar.spread, costs.spread) if bar.spread is not None else costs.spread
        if spread > fixed.max_spread_to_stop * abs(setup.signal_close - setup.stop):
            return None
        return BracketOrder(side, setup.stop, target_r, fixed.max_hold_bars)

    return signal
