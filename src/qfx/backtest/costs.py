"""Explicit transaction-cost model for historical research."""
from __future__ import annotations

from .types import ExecutionCosts, Side


def execution_price(mid: float, side: Side, spread: float, slippage: float) -> float:
    """Return an executable price including half-spread and slippage."""
    half = abs(spread) / 2.0
    slip = abs(slippage)
    if side is Side.LONG:
        return mid + half + slip
    return mid - half - slip


def trade_cost(entry_price: float, exit_price: float, costs: ExecutionCosts) -> float:
    """Return explicit monetary/price-unit costs not already in fill prices.

    Spread and slippage are already represented in the executable entry/exit
    prices, so charging them again would double-count friction. Commission is
    kept explicit here; instrument-specific monetary conversion belongs in the
    contract-spec layer.
    """
    return abs(costs.commission)
