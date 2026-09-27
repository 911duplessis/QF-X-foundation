from datetime import datetime, timedelta, timezone

from qfx.data_quality import check_candles
from qfx.models import Candle


def bar(minute, o=1.0, h=1.2, l=0.9, c=1.1):
    return Candle(f"2026-01-01T00:{minute:02d}:00Z", o, h, l, c)


def test_clean_series_passes():
    report = check_candles([bar(0), bar(5), bar(10)], expected_interval=timedelta(minutes=5))
    assert report.passed


def test_empty_series_fails():
    assert not check_candles([]).passed


def test_duplicate_and_out_of_order():
    report = check_candles([bar(5), bar(5), bar(0)])
    assert "duplicate_timestamp@1" in report.issues
    assert "out_of_order@2" in report.issues


def test_invalid_ohlc_detected():
    report = check_candles([bar(0), Candle("2026-01-01T00:05:00Z", 1.0, 0.9, 0.8, 1.1)])
    assert "invalid_ohlc@1" in report.issues


def test_naive_timestamp_rejected():
    report = check_candles([Candle("2026-01-01T00:00:00", 1, 1.2, 0.9, 1.1)])
    assert "invalid_timestamp@0" in report.issues


def test_gaps_counted_and_bounded():
    candles = [bar(0), bar(5), bar(20)]
    assert not check_candles(candles, expected_interval=timedelta(minutes=5)).passed
    tolerant = check_candles(candles, expected_interval=timedelta(minutes=5), max_gaps=1)
    assert tolerant.passed and tolerant.gap_count == 1


def test_frozen_prices_flagged():
    candles = [bar(i, 1, 1, 1, 1) for i in range(10)]
    assert "stale_prices" in check_candles(candles, max_stale_run=5).issues


def test_stale_feed_flagged():
    now = datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)
    report = check_candles([bar(0)], now=now, max_age=timedelta(minutes=30))
    assert "stale_feed" in report.issues
