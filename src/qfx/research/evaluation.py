"""Trade statistics in basis points of entry price, comparable across instruments."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt
from statistics import mean, median, stdev

from ..backtest.types import Trade


@dataclass(frozen=True)
class Stats:
    trades: int
    net_bps: float  # mean net return per trade
    median_bps: float
    gross_bps: float  # mean mid-to-mid return per trade (no friction)
    cost_bps: float  # gross - net
    win_rate: float
    profit_factor: float
    t_stat: float
    max_drawdown_bps: float
    avg_hold_hours: float
    exposure: float  # fraction of segment time in a position


def _bps(t: Trade) -> float:
    return t.net_pnl / t.entry_price * 1e4


def trade_stats(trades: Sequence[Trade], frictionless: Sequence[Trade], segment_hours: float) -> Stats:
    if len(trades) != len(frictionless):
        raise ValueError("Frictionless run must produce the same trades")
    if not trades:
        return Stats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    net = [_bps(t) for t in trades]
    gross = [_bps(t) for t in frictionless]
    wins = sum(x for x in net if x > 0)
    losses = -sum(x for x in net if x < 0)
    sd = stdev(net) if len(net) > 1 else 0.0
    equity = peak = dd = 0.0
    for x in net:
        equity += x
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    hold = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
    return Stats(
        trades=len(net),
        net_bps=mean(net),
        median_bps=median(net),
        gross_bps=mean(gross),
        cost_bps=mean(gross) - mean(net),
        win_rate=sum(1 for x in net if x > 0) / len(net),
        profit_factor=wins / losses if losses else float("inf"),
        t_stat=mean(net) / (sd / sqrt(len(net))) if sd > 0 else 0.0,
        max_drawdown_bps=dd,
        avg_hold_hours=mean(hold),
        exposure=sum(hold) / segment_hours if segment_hours > 0 else 0.0,
    )
