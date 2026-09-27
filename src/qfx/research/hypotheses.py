"""Strategy hypotheses as backtest signals. Descriptive, not recommendations."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..backtest.engine import Signal
from ..backtest.types import Bar, Side
from .features import ewma_vol, log_returns, trend_z


@dataclass(frozen=True)
class TrendParams:
    lookback: int = 72
    entry_z: float = 1.5
    exit_z: float = 0.5
    vol_halflife: float = 240.0
    shock_halflife: float = 6.0
    shock_ratio: float = 2.5  # short-term vol / long-term vol treated as abnormal

    def __post_init__(self) -> None:
        if not 0 <= self.exit_z < self.entry_z:
            raise ValueError("Require 0 <= exit_z < entry_z")


def trend_continuation(bars: Sequence[Bar], params: TrendParams, offset: int = 0) -> Signal:
    """Hypothesis 1: persistent, volatility-normalised moves continue.

    Enter when |z| >= entry_z; hold while z stays beyond exit_z in the same
    direction; stand aside (NO_TRADE) during volatility shocks.
    ``offset`` maps segment-local indices to positions in ``bars`` so that
    features can warm up on earlier history without leaking later data.
    """
    closes = [b.close for b in bars]
    rets = log_returns(closes)
    long_vol = ewma_vol(rets, params.vol_halflife)
    short_vol = ewma_vol(rets, params.shock_halflife)
    z = trend_z(closes, params.lookback, long_vol)
    state: dict[str, Side | None] = {"side": None}

    def signal(view: Sequence[Bar], i: int) -> Side | None:
        g = i + offset
        zi, lv, sv = z[g], long_vol[g], short_vol[g]
        if zi != zi or lv != lv or sv != sv or sv > params.shock_ratio * lv:
            # Warm-up or volatility shock: stand aside; no entry on this bar.
            state["side"] = None
            return None
        side = state["side"]
        if side is Side.LONG and zi <= params.exit_z:
            side = None
        elif side is Side.SHORT and zi >= -params.exit_z:
            side = None
        if side is None:
            if zi >= params.entry_z:
                side = Side.LONG
            elif zi <= -params.entry_z:
                side = Side.SHORT
        state["side"] = side
        return side

    return signal
