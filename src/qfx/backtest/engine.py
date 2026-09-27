"""Minimal event-driven research backtest harness.

The harness deliberately accepts a strategy callback rather than embedding a
strategy. This keeps execution accounting separate from alpha research.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

from .costs import execution_price, trade_cost
from .types import Bar, ExecutionCosts, Side, Trade

Signal = Callable[[Sequence[Bar], int], Side | None]


def run_backtest(bars: Sequence[Bar], signal: Signal, *, costs: ExecutionCosts | None = None) -> list[Trade]:
    costs = costs or ExecutionCosts()
    trades: list[Trade] = []
    position: tuple[Side, int, float] | None = None

    for i, bar in enumerate(bars):
        side = signal(bars, i)
        if position is None and side is not None:
            entry_index = i + costs.delay_bars
            if entry_index >= len(bars):
                break
            entry_bar = bars[entry_index]
            entry = execution_price(entry_bar.open, side, costs.spread, costs.slippage)
            position = (side, entry_index, entry)
            continue

        if position is not None and side is None:
            held_side, entry_index, entry = position
            exit = execution_price(bar.open, Side.SHORT if held_side is Side.LONG else Side.LONG, costs.spread, costs.slippage)
            gross = (exit - entry) if held_side is Side.LONG else (entry - exit)
            total_cost = trade_cost(entry, exit, costs)
            trades.append(Trade(held_side, bars[entry_index].timestamp, bar.timestamp, entry, exit, gross, total_cost, gross - total_cost))
            position = None

    return trades
