"""Gate 0: data integrity checks for candle series."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .models import Candle


@dataclass(frozen=True)
class DataQualityReport:
    passed: bool
    issues: tuple[str, ...] = field(default_factory=tuple)
    gap_count: int = 0


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp; timezone-naive values are rejected."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return parsed


def check_candles(
    candles: Sequence[Candle],
    expected_interval: timedelta | None = None,
    max_gaps: int = 0,
    max_stale_run: int = 5,
    now: datetime | None = None,
    max_age: timedelta | None = None,
) -> DataQualityReport:
    """Validate a candle series before any feature is computed from it.

    Checks: empty input, invalid OHLC, timezone awareness, duplicates,
    ordering, gaps against ``expected_interval``, stale (frozen) prices and
    feed age relative to ``now``. Gaps may be expected (weekends for FX), so
    they fail the report only when they exceed ``max_gaps``.
    """
    issues: list[str] = []
    if not candles:
        return DataQualityReport(False, ("empty_series",))

    timestamps: list[datetime] = []
    for index, candle in enumerate(candles):
        try:
            candle.validate()
        except ValueError:
            issues.append(f"invalid_ohlc@{index}")
        try:
            timestamps.append(parse_timestamp(candle.timestamp))
        except ValueError:
            issues.append(f"invalid_timestamp@{index}")

    if len(timestamps) != len(candles):
        return DataQualityReport(False, tuple(issues))

    gaps = 0
    for index in range(1, len(timestamps)):
        delta = timestamps[index] - timestamps[index - 1]
        if delta == timedelta(0):
            issues.append(f"duplicate_timestamp@{index}")
        elif delta < timedelta(0):
            issues.append(f"out_of_order@{index}")
        elif expected_interval is not None and delta > expected_interval:
            gaps += 1
    if gaps > max_gaps:
        issues.append(f"gaps_exceeded:{gaps}>{max_gaps}")

    run = 1
    for previous, current in zip(candles, candles[1:]):
        frozen = (previous.open, previous.high, previous.low, previous.close) == (
            current.open,
            current.high,
            current.low,
            current.close,
        ) and current.high == current.low
        run = run + 1 if frozen else 1
        if run > max_stale_run:
            issues.append("stale_prices")
            break

    if now is not None and max_age is not None and now - timestamps[-1] > max_age:
        issues.append("stale_feed")

    return DataQualityReport(not issues, tuple(issues), gaps)
