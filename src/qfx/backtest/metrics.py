"""Backtest metrics with explicit no-trade handling."""
from __future__ import annotations

from math import inf
from statistics import mean

from .types import Trade


def summarize(trades: list[Trade]) -> dict[str, float | int]:
    if not trades:
        return {"trades": 0, "net_pnl": 0.0, "win_rate": 0.0, "profit_factor": 0.0, "max_drawdown": 0.0, "expectancy": 0.0}
    pnls = [t.net_pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    equity = peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    gross_loss = abs(sum(losses))
    return {
        "trades": len(trades),
        "net_pnl": sum(pnls),
        "win_rate": len(wins) / len(pnls),
        "profit_factor": sum(wins) / gross_loss if gross_loss else inf if wins else 0.0,
        "max_drawdown": max_dd,
        "expectancy": mean(pnls),
    }
