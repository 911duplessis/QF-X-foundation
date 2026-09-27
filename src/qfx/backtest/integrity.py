"""Gate 0 for backtest bars: nothing reaches the engine without passing this.

Reuses the candle checks in ``qfx.data_quality`` (OHLC validity, duplicates,
ordering, frozen prices) and adds resolution checks that matter for vendor
exports: mixed timeframes, sub-interval bars and oversized gaps.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta

from ..data_quality import check_candles
from ..models import Candle
from .types import Bar


class DataQualityError(ValueError):
    def __init__(self, report: "BarQualityReport", source: str = "") -> None:
        self.report = report
        prefix = f"{source}: " if source else ""
        super().__init__(prefix + "data quality gate failed: " + ", ".join(report.issues[:10]))


@dataclass(frozen=True)
class BarQualityReport:
    passed: bool
    bars: int
    issues: tuple[str, ...] = field(default_factory=tuple)
    gap_count: int = 0
    max_gap: timedelta = timedelta(0)
    trimmed_prefix: int = 0


def resolution_start(bars: Sequence[Bar], interval: timedelta) -> int:
    """Index of the first bar that is followed by a bar exactly ``interval``
    later. Exports often prepend coarser history (e.g. D1 bars before H1)."""
    for i in range(len(bars) - 1):
        if bars[i + 1].timestamp - bars[i].timestamp == interval:
            return i
    return len(bars)


def check_bars(
    bars: Sequence[Bar],
    interval: timedelta | None = None,
    max_gap: timedelta | None = None,
    max_coarse_run: int = 3,
    trimmed_prefix: int = 0,
) -> BarQualityReport:
    """``max_gap`` bounds any single gap (weekends/holidays are expected for FX).
    ``max_coarse_run`` consecutive gaps indicate a change of resolution, not a
    market closure."""
    if not bars:
        return BarQualityReport(False, 0, ("empty_series",), trimmed_prefix=trimmed_prefix)

    candles = [Candle(b.timestamp.isoformat(), b.open, b.high, b.low, b.close, b.volume) for b in bars]
    base = check_candles(candles)
    issues = list(base.issues)

    gaps = 0
    widest = timedelta(0)
    run = 0
    flagged_run = False
    for i in range(1, len(bars)):
        delta = bars[i].timestamp - bars[i - 1].timestamp
        if interval is None or delta <= timedelta(0):
            continue
        if delta < interval or delta % interval:
            issues.append(f"off_interval@{i}:{delta}")
        if delta > interval:
            gaps += 1
            widest = max(widest, delta)
            run += 1
            if run >= max_coarse_run and not flagged_run:
                issues.append(f"resolution_change@{i - run + 1}")
                flagged_run = True
            if max_gap is not None and delta > max_gap:
                issues.append(f"gap_exceeds_max@{i}:{delta}")
        else:
            run = 0

    return BarQualityReport(not issues, len(bars), tuple(issues), gaps, widest, trimmed_prefix)
