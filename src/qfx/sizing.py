"""Instrument-aware position sizing.

size = account risk / monetary loss per unit of stop distance
"""

from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    contract_size: float
    tick_size: float
    min_lot: float
    lot_step: float
    max_lot: float
    quote_to_account: float = 1.0

    def __post_init__(self) -> None:
        for name in ("contract_size", "tick_size", "min_lot", "lot_step", "max_lot", "quote_to_account"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


# Illustrative defaults. Production sizing must use the broker's exact specs.
DEFAULT_SPECS: dict[str, InstrumentSpec] = {
    "EURUSD": InstrumentSpec("EURUSD", 100_000, 0.00001, 0.01, 0.01, 100.0),
    "XAUUSD": InstrumentSpec("XAUUSD", 100, 0.01, 0.01, 0.01, 50.0),
    "BTCUSD": InstrumentSpec("BTCUSD", 1, 0.01, 0.01, 0.01, 10.0),
}


def position_size(
    equity: float,
    risk_fraction: float,
    entry: float,
    stop: float,
    spec: InstrumentSpec,
    cost_per_lot: float = 0.0,
) -> float:
    """Lots to trade so that a stop-out (plus round-trip costs) loses at most
    ``equity * risk_fraction``. Always rounds down; returns 0.0 when the
    minimum lot would exceed the risk budget."""
    if equity <= 0:
        raise ValueError("Equity must be positive")
    if not 0 <= risk_fraction < 1:
        raise ValueError("Risk fraction must be within [0, 1)")
    if cost_per_lot < 0:
        raise ValueError("Cost per lot must be non-negative")
    distance = abs(entry - stop)
    if distance < spec.tick_size:
        raise ValueError("Stop distance must be at least one tick")
    budget = equity * risk_fraction
    loss_per_lot = distance * spec.contract_size * spec.quote_to_account + cost_per_lot
    raw = budget / loss_per_lot
    steps = floor(round(raw / spec.lot_step, 9))
    lots = min(steps * spec.lot_step, spec.max_lot)
    if lots < spec.min_lot:
        return 0.0
    return round(lots, 8)
