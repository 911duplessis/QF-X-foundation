"""Typed records used by the research backtester."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class ExecutionCosts:
    spread: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    delay_bars: int = 1

    def __post_init__(self) -> None:
        # A signal computed on bar i can only be filled on bar i + 1 or later.
        if self.delay_bars < 1:
            raise ValueError("delay_bars must be at least 1 to avoid look-ahead fills")


@dataclass(frozen=True)
class Trade:
    side: Side
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    gross_pnl: float
    costs: float
    net_pnl: float

    @property
    def return_fraction(self) -> float:
        return self.net_pnl
