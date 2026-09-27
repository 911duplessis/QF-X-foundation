"""Integration checks on the committed MT5 exports (skipped when absent)."""
from collections import Counter
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from qfx.backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5

DATA = Path(__file__).resolve().parents[1] / "data" / "mt5"
FILES = sorted(DATA.glob("*.csv"))
NY = ZoneInfo("America/New_York")

pytestmark = pytest.mark.skipif(not FILES, reason="no MT5 exports in data/mt5")


@pytest.fixture(scope="module")
def loaded():
    return {r.symbol: r for r in (load_mt5(f, ZoneInfo(DEFAULT_SERVER_TZ)) for f in FILES)}


def test_all_exports_pass_gate_0(loaded):
    for result in loaded.values():
        assert result.report.passed, result.report.issues
        assert result.report.trimmed_prefix > 0  # each export starts with D1 history


@pytest.mark.parametrize("symbol,open_hour", [("EURUSD", 17), ("XAUUSD", 18)])
def test_fx_week_opens_at_new_york_session_time(loaded, symbol, open_hour):
    if symbol not in loaded:
        pytest.skip(f"{symbol} export missing")
    bars = loaded[symbol].bars
    opens = Counter(
        (b.timestamp.astimezone(NY).weekday(), b.timestamp.astimezone(NY).hour)
        for a, b in zip(bars, bars[1:])
        if b.timestamp - a.timestamp > timedelta(hours=40)
    )
    aligned = opens[(6, open_hour)] / sum(opens.values())
    assert aligned > 0.95, opens.most_common(5)
