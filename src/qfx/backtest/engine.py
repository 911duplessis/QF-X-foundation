"""Minimal event-driven research backtest harness.

The harness deliberately accepts a strategy callback rather than embedding a
strategy. This keeps execution accounting separate from alpha research.

Timing contract (no look-ahead):
- ``signal`` sees only bars ``0..i``; it cannot index future bars.
- A signal on bar ``i`` fills at the open of bar ``i + delay_bars``.
- The signal returns the desired side; ``None`` (or the opposite side) while
  holding a position requests an exit.
- A position still open at the end of the data is closed at the last close so
  unfinished trades are never silently dropped.
- Spread per fill is ``max(bar.spread, costs.spread)``: the configured spread
  is a floor, so per-bar data can only make costs more realistic, never lower.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import overload

from .costs import execution_price, trade_cost
from .types import Bar, ExecutionCosts, Side, Trade

Signal = Callable[[Sequence[Bar], int], Side | None]


class _PrefixView(Sequence[Bar]):
    """Read-only view of ``bars[:end]`` without copying."""

    def __init__(self, bars: Sequence[Bar], end: int) -> None:
        self._bars = bars
        self._end = end

    def __len__(self) -> int:
        return self._end

    @overload
    def __getitem__(self, index: int) -> Bar: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[Bar]: ...
    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self._bars[j] for j in range(*index.indices(self._end))]
        if index < 0:
            index += self._end
        if not 0 <= index < self._end:
            raise IndexError("bar is not yet observable")
        return self._bars[index]


def _opposite(side: Side) -> Side:
    return Side.SHORT if side is Side.LONG else Side.LONG


def _spread(bar: Bar, costs: ExecutionCosts) -> float:
    return max(bar.spread, costs.spread) if bar.spread is not None else costs.spread


def _close(held_side: Side, entry_bar: Bar, entry: float, exit_bar: Bar, exit_mid: float, costs: ExecutionCosts, reason: str = "signal") -> Trade:
    exit = execution_price(exit_mid, _opposite(held_side), _spread(exit_bar, costs), costs.slippage)
    gross = (exit - entry) if held_side is Side.LONG else (entry - exit)
    total_cost = trade_cost(entry, exit, costs)
    return Trade(
        held_side, entry_bar.timestamp, exit_bar.timestamp, entry, exit, gross, total_cost, gross - total_cost,
        mid_entry=entry_bar.open, mid_exit=exit_mid, exit_reason=reason,
    )


def run_backtest(bars: Sequence[Bar], signal: Signal, *, costs: ExecutionCosts | None = None) -> list[Trade]:
    costs = costs or ExecutionCosts()
    delay = costs.delay_bars
    trades: list[Trade] = []
    # (side, entry_index, entry_price); entry_index may be a pending future fill.
    position: tuple[Side, int, float] | None = None

    for i in range(len(bars)):
        if position is not None and i < position[1]:
            continue  # entry order is still pending
        side = signal(_PrefixView(bars, i + 1), i)

        if position is None:
            if side is None:
                continue
            entry_index = i + delay
            if entry_index >= len(bars):
                break
            entry_bar = bars[entry_index]
            entry = execution_price(entry_bar.open, side, _spread(entry_bar, costs), costs.slippage)
            position = (side, entry_index, entry)
            continue

        held_side, entry_index, entry = position
        if side is held_side:
            continue
        exit_index = i + delay
        if exit_index >= len(bars):
            break
        exit_bar = bars[exit_index]
        trades.append(_close(held_side, bars[entry_index], entry, exit_bar, exit_bar.open, costs))
        position = None

    if position is not None:
        held_side, entry_index, entry = position
        last = bars[-1]
        trades.append(_close(held_side, bars[entry_index], entry, last, last.close, costs, "end_of_data"))

    return trades
