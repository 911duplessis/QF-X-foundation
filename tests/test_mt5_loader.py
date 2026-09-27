from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from qfx.backtest.engine import run_backtest
from qfx.backtest.integrity import DataQualityError, check_bars
from qfx.backtest.mt5 import load_mt5, symbol_from_path
from qfx.backtest.types import Bar, ExecutionCosts, Side

HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\r\n"
ATHENS = ZoneInfo("Europe/Athens")


def row(date, time, o=1.1, h=1.2, l=1.0, c=1.15, spread=8):
    return f"{date}\t{time}\t{o}\t{h}\t{l}\t{c}\t100\t0\t{spread}\r\n"


def write(tmp_path, rows, name="EURUSD.m_H1_test.csv"):
    path = tmp_path / name
    path.write_text(HEADER + "".join(rows), encoding="utf-8")
    return path


def hourly(date, hours):
    return [row(date, f"{h:02d}:00:00") for h in hours]


def test_symbol_from_path():
    assert symbol_from_path("data/mt5/XAUUSD.m_H1_2020_2026.csv") == "XAUUSD"


def test_converts_server_time_to_utc_and_spread_to_price(tmp_path):
    result = load_mt5(write(tmp_path, hourly("2026.01.05", range(3))), ATHENS)
    first = result.bars[0]
    assert first.timestamp == datetime(2026, 1, 4, 22, tzinfo=timezone.utc)  # EET = UTC+2 in winter
    assert first.spread == pytest.approx(8 * 0.00001)


def test_daily_prefix_is_trimmed_and_reported(tmp_path):
    rows = [row("2026.01.05", "00:00:00"), row("2026.01.06", "00:00:00"), row("2026.01.07", "00:00:00")]
    rows += hourly("2026.01.08", range(4))
    result = load_mt5(write(tmp_path, rows), ATHENS)
    assert result.report.trimmed_prefix == 3
    assert len(result.bars) == 4


def test_untrimmed_mixed_resolution_fails(tmp_path):
    rows = [row(f"2026.01.{d:02d}", "00:00:00") for d in (5, 6, 7, 8)] + hourly("2026.01.09", range(3))
    with pytest.raises(DataQualityError, match="resolution_change"):
        load_mt5(write(tmp_path, rows), ATHENS, trim_prefix=False)


def test_real_duplicate_fails_gate(tmp_path):
    rows = hourly("2026.01.05", range(3)) + [row("2026.01.05", "02:00:00")]
    with pytest.raises(DataQualityError, match="duplicate_timestamp"):
        load_mt5(write(tmp_path, rows), ATHENS)


def test_malformed_row_names_line(tmp_path):
    rows = hourly("2026.01.05", range(2)) + ["2026.01.05\t02:00:00\tx\t1\t1\t1\t1\t0\t0\r\n"]
    with pytest.raises(ValueError, match=":4: malformed"):
        load_mt5(write(tmp_path, rows), ATHENS)


def test_dst_collision_on_24_7_symbol_is_dropped_and_counted(tmp_path):
    # EU DST starts 2026-03-29 03:00 local; server 03:00 and 04:00 both map to 01:00 UTC.
    rows = hourly("2026.03.29", range(1, 7))
    result = load_mt5(write(tmp_path, rows, "BTCUSD.m_H1_test.csv"), ATHENS)
    assert result.dst_collisions_dropped == 1
    assert result.report.passed
    stamps = [b.timestamp for b in result.bars]
    assert stamps == sorted(set(stamps))


def _bars(deltas_h):
    t = datetime(2026, 1, 5, tzinfo=timezone.utc)
    out = [Bar(t, 1.1, 1.2, 1.0, 1.15)]
    for d in deltas_h:
        t += timedelta(hours=d)
        out.append(Bar(t, 1.1, 1.2, 1.0, 1.15))
    return out


def test_gap_limit_and_off_interval():
    report = check_bars(_bars([1, 100, 1]), interval=timedelta(hours=1), max_gap=timedelta(days=4))
    assert any(i.startswith("gap_exceeds_max") for i in report.issues)
    report = check_bars(_bars([1, 1.5, 1]), interval=timedelta(hours=1))
    assert any(i.startswith("off_interval") for i in report.issues)


def test_weekend_gap_is_allowed():
    report = check_bars(_bars([1, 49, 1]), interval=timedelta(hours=1), max_gap=timedelta(days=4))
    assert report.passed and report.gap_count == 1


def test_per_bar_spread_is_a_floor_not_a_discount():
    bars = _bars([1, 1, 1])
    wide = [Bar(b.timestamp, b.open, b.high, b.low, b.close, spread=0.02) for b in bars]
    narrow = [Bar(b.timestamp, b.open, b.high, b.low, b.close, spread=0.0) for b in bars]
    signal = lambda v, i: Side.LONG if i == 0 else None
    costs = ExecutionCosts(spread=0.01)
    wide_trade = run_backtest(wide, signal, costs=costs)[0]
    narrow_trade = run_backtest(narrow, signal, costs=costs)[0]
    base_trade = run_backtest(bars, signal, costs=costs)[0]
    assert wide_trade.gross_pnl == pytest.approx(-0.02)
    assert narrow_trade.gross_pnl == pytest.approx(base_trade.gross_pnl) == pytest.approx(-0.01)
