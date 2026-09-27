"""Explicit transaction-cost model for historical research."""
from __future__ import annotations

from .types import ExecutionCosts, Side


def execution_price(mid: float, side: Side, spread: float, slippage: float) -> float:
    half = spread / 2.0
    slip = abs(slippage)
    if side is Side.LONG:
        return mid + half + slip
    return mid - half - slip


def trade_cost(entry_price: float, exit_price: float, costs: ExecutionCosts) -> float:
    # Costs are expressed in price units here. Instrument-specific monetary
    # conversion belongs in the sizing/contract-spec layer.
    return costs.commission + abs(costs.spread) + abs(costs.slippage) * 2.0
