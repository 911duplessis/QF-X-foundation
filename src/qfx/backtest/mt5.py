"""Loader for MetaTrader 5 history exports (tab-separated, ``<DATE>``/``<TIME>``).

MT5 timestamps are broker *server* time with no timezone marker, so the
caller must state the server timezone; bars are converted to UTC. The
``<SPREAD>`` column is in points and is converted to price units.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

from ..sizing import DEFAULT_SPECS
from .integrity import BarQualityReport, DataQualityError, check_bars, resolution_start
from .types import Bar


# Verified against the committed exports: with this zone the FX week opens at
# Sun 17:00 New York (gold 18:00) in all non-holiday weeks, including the
# weeks when US and EU DST dates differ. A fixed UTC+2 offset or NY+7 clock
# misplaces those weeks by one hour.
DEFAULT_SERVER_TZ = "Europe/Athens"


@dataclass(frozen=True)
class LoadResult:
    symbol: str
    bars: list[Bar]
    report: BarQualityReport
    dst_collisions_dropped: int = 0


def symbol_from_path(path: str | Path) -> str:
    """``EURUSD.m_H1_2020...csv`` -> ``EURUSD``."""
    return Path(path).name.split("_")[0].split(".")[0].upper()


def _parse_local(date: str, time: str | None, tz: tzinfo) -> datetime:
    text = date.strip() + " " + (time.strip() if time else "00:00:00")
    return datetime.strptime(text, "%Y.%m.%d %H:%M:%S").replace(tzinfo=tz)


def _drop_dst_collisions(bars: list[Bar], offsets: list[timedelta]) -> tuple[list[Bar], int]:
    """Drop a bar whose UTC time does not advance *only* where the server
    offset changed between it and the previous kept bar. MT5 exports of 24/7
    symbols keep an unbroken server-clock sequence across DST switches, so one
    bar per spring switch lands on an already-used UTC hour. Any other
    non-advancing timestamp is kept so Gate 0 still rejects it."""
    kept: list[Bar] = []
    kept_offsets: list[timedelta] = []
    dropped = 0
    for bar, offset in zip(bars, offsets):
        if kept and bar.timestamp <= kept[-1].timestamp and offset != kept_offsets[-1]:
            dropped += 1
            continue
        kept.append(bar)
        kept_offsets.append(offset)
    return kept, dropped


def load_mt5(
    path: str | Path,
    tz: tzinfo,
    *,
    point: float | None = None,
    interval: timedelta | None = timedelta(hours=1),
    max_gap: timedelta | None = timedelta(days=4),
    trim_prefix: bool = True,
    validate: bool = True,
) -> LoadResult:
    """Load, convert to UTC, trim any coarser-resolution prefix and run Gate 0.

    Raises ``DataQualityError`` when ``validate`` is set and the gate fails.
    ``point`` defaults to the instrument's tick size in ``DEFAULT_SPECS``;
    without it, per-bar spread is left as ``None``.
    """
    symbol = symbol_from_path(path)
    if point is None and symbol in DEFAULT_SPECS:
        point = DEFAULT_SPECS[symbol].tick_size

    bars: list[Bar] = []
    offsets: list[timedelta] = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for line, row in enumerate(reader, start=2):
            try:
                spread_points = row.get("<SPREAD>")
                local = _parse_local(row["<DATE>"], row.get("<TIME>"), tz)
                offsets.append(local.utcoffset() or timedelta(0))
                bars.append(
                    Bar(
                        timestamp=local.astimezone(timezone.utc),
                        open=float(row["<OPEN>"]),
                        high=float(row["<HIGH>"]),
                        low=float(row["<LOW>"]),
                        close=float(row["<CLOSE>"]),
                        volume=float(row["<TICKVOL>"]) if row.get("<TICKVOL>") else None,
                        spread=float(spread_points) * point if spread_points and point else None,
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line}: malformed MT5 row: {exc}") from exc

    bars, dst_dropped = _drop_dst_collisions(bars, offsets)

    trimmed = 0
    if trim_prefix and interval is not None:
        trimmed = resolution_start(bars, interval)
        bars = bars[trimmed:]

    report = check_bars(bars, interval=interval, max_gap=max_gap, trimmed_prefix=trimmed)
    if validate and not report.passed:
        raise DataQualityError(report, str(path))
    return LoadResult(symbol, bars, report, dst_dropped)
