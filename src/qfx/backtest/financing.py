"""Overnight financing (swap) for CFD positions, as a per-trade cost in bps.

Broker convention (JustMarkets crypto conditions page, 2026-09-27): swaps are
applied at 22:00 server time on weekdays only (Monday-Friday server date) and
tripled on Wednesday. A trade pays one charge (three on Wednesday) for every
rollover instant inside its holding interval.

The holding interval is taken conservatively as [entry, exit + 1 bar): exits
are recorded at the exit bar's timestamp even when the stop or target fills
inside that bar.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .types import Trade

SERVER_TZ = ZoneInfo("Europe/Athens")


@dataclass(frozen=True)
class SwapSpec:
    long_points: float  # per night, in points (negative = charge)
    point: float  # price units per point
    rollover_hour: int = 22
    triple_weekday: int = 2  # Monday = 0; Wednesday tripled
    tz: ZoneInfo = SERVER_TZ


def rollover_charges(entry_utc: datetime, exit_utc: datetime, spec: SwapSpec, bar: timedelta = timedelta(hours=1)) -> int:
    """Number of swap charges (Wednesday counts 3) in [entry, exit + bar)."""
    end = exit_utc + bar
    day = entry_utc.astimezone(spec.tz).date() - timedelta(days=1)
    last_day = end.astimezone(spec.tz).date()
    charges = 0
    while day <= last_day:
        if day.weekday() < 5:
            instant = datetime.combine(day, time(spec.rollover_hour), spec.tz).astimezone(timezone.utc)
            if entry_utc <= instant < end:
                charges += 3 if day.weekday() == spec.triple_weekday else 1
        day += timedelta(days=1)
    return charges


def financing_cost_bps(trade: Trade, spec: SwapSpec) -> float:
    """Financing cost of a long trade in bps of the mid entry price (positive = cost)."""
    if trade.mid_entry is None:
        raise ValueError("Trade has no mid entry price")
    charges = rollover_charges(trade.entry_time, trade.exit_time, spec)
    return -charges * spec.long_points * spec.point / trade.mid_entry * 1e4
