"""Stop/target/time-stop execution for hypotheses with predefined risk.

Timing contract (no look-ahead, pessimistic fills):
- ``signal`` sees only bars ``0..i`` and returns a ``BracketOrder`` or None.
  It is called on every bar so hypotheses can track state; orders are ignored
  while a position is open or an entry is pending.
- An order from bar ``i`` fills at the open of bar ``i + delay_bars``. If that
  fill is at or beyond the stop, the trade is skipped.
- From the entry bar onward, each bar is checked in this order:
  time stop (exit at the open of bar ``entry + max_hold_bars``), stop, target.
  If one bar's range touches both stop and target, the stop is taken.
- A stop fills at the stop price, or at the open when the bar gaps through it.
  A target fills at the target price. Every fill pays half spread + slippage
  against the trade (per-bar spread as a floor, as in ``engine``).
- A position open at the end of the data exits at the last close.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .costs import execution_price, trade_cost
from .engine import _PrefixView, _opposite, _spread
from .types import Bar, ExecutionCosts, Side, Trade


@dataclass(frozen=True)
class BracketOrder:
    side: Side
    stop: float
    target_r: float
    max_hold_bars: int

    def __post_init__(self) -> None:
        if self.target_r <= 0:
            raise ValueError("target_r must be positive")
        if self.max_hold_bars < 1:
            raise ValueError("max_hold_bars must be at least 1")


BracketSignal = Callable[[Sequence[Bar], int], BracketOrder | None]


@dataclass
class _Position:
    side: Side
    entry_index: int
    fill: float
    mid: float
    stop: float
    target: float
    risk: float
    deadline: int


def _exit(pos: _Position, bars: Sequence[Bar], index: int, exit_mid: float, reason: str, costs: ExecutionCosts) -> Trade:
    bar = bars[index]
    fill = execution_price(exit_mid, _opposite(pos.side), _spread(bar, costs), costs.slippage)
    gross = (fill - pos.fill) if pos.side is Side.LONG else (pos.fill - fill)
    cost = trade_cost(pos.fill, fill, costs)
    net = gross - cost
    return Trade(
        pos.side, bars[pos.entry_index].timestamp, bar.timestamp, pos.fill, fill, gross, cost, net,
        mid_entry=pos.mid, mid_exit=exit_mid, stop_price=pos.stop, exit_reason=reason, r_multiple=net / pos.risk,
    )


def _open(order: BracketOrder, bars: Sequence[Bar], index: int, costs: ExecutionCosts) -> _Position | None:
    bar = bars[index]
    fill = execution_price(bar.open, order.side, _spread(bar, costs), costs.slippage)
    risk = fill - order.stop if order.side is Side.LONG else order.stop - fill
    if risk <= 0:
        return None  # fill already at or beyond the stop
    target = fill + order.target_r * risk if order.side is Side.LONG else fill - order.target_r * risk
    return _Position(order.side, index, fill, bar.open, order.stop, target, risk, index + order.max_hold_bars)


def _check(pos: _Position, bar: Bar, index: int) -> tuple[float, str] | None:
    if index >= pos.deadline:
        return bar.open, "time"
    if pos.side is Side.LONG:
        if bar.low <= pos.stop:
            return min(bar.open, pos.stop), "stop"
        if bar.high >= pos.target:
            return pos.target, "target"
    else:
        if bar.high >= pos.stop:
            return max(bar.open, pos.stop), "stop"
        if bar.low <= pos.target:
            return pos.target, "target"
    return None


def run_bracket_backtest(bars: Sequence[Bar], signal: BracketSignal, *, costs: ExecutionCosts | None = None) -> list[Trade]:
    costs = costs or ExecutionCosts()
    trades: list[Trade] = []
    pending: tuple[int, BracketOrder] | None = None
    pos: _Position | None = None

    for i, bar in enumerate(bars):
        if pending is not None and pending[0] == i:
            pos = _open(pending[1], bars, i, costs)
            pending = None
        if pos is not None:
            hit = _check(pos, bar, i)
            if hit is not None:
                trades.append(_exit(pos, bars, i, hit[0], hit[1], costs))
                pos = None
        order = signal(_PrefixView(bars, i + 1), i)
        if order is not None and pos is None and pending is None and i + costs.delay_bars < len(bars):
            pending = (i + costs.delay_bars, order)

    if pos is not None:
        trades.append(_exit(pos, bars, len(bars) - 1, bars[-1].close, "end_of_data", costs))
    return trades
