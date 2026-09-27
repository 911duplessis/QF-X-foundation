"""Flexible CSV loader for common OHLC exports.

Expected semantic columns: timestamp, open, high, low, close, optional volume.
Column names are configurable so MT5/Dukascopy/vendor exports can be mapped
without changing the backtest engine.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .integrity import DataQualityError, check_bars
from .types import Bar


def _timestamp(value: str) -> datetime:
    value = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone information")
    return dt


def load_csv(
    path: str | Path,
    *,
    columns: dict[str, str] | None = None,
    interval: timedelta | None = None,
    max_gap: timedelta | None = None,
    validate: bool = True,
) -> list[Bar]:
    """Load bars and run Gate 0; raises ``DataQualityError`` on failure."""
    mapping = {"timestamp": "timestamp", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"}
    if columns:
        mapping.update(columns)
    bars: list[Bar] = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            bars.append(Bar(
                timestamp=_timestamp(row[mapping["timestamp"]]),
                open=float(row[mapping["open"]]),
                high=float(row[mapping["high"]]),
                low=float(row[mapping["low"]]),
                close=float(row[mapping["close"]]),
                volume=float(row[mapping["volume"]]) if mapping["volume"] in row and row[mapping["volume"]] else None,
            ))
    if validate:
        report = check_bars(bars, interval=interval, max_gap=max_gap)
        if not report.passed:
            raise DataQualityError(report, str(path))
    return bars


def bars_to_dicts(bars: Iterable[Bar]) -> list[dict[str, object]]:
    return [bar.__dict__.copy() for bar in bars]
