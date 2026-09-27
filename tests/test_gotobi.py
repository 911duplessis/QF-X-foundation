"""USDJPY Gotobi v1. Synthetic data only: no test reads the quarantined CSV."""
import json
import random
import re
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from qfx.backtest.types import Bar
from qfx.research import gotobi as g

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def frozen():
    text = (ROOT / g.SPEC_PATH).read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


@pytest.fixture(scope="module")
def closures():
    return g.load_closures(ROOT / g.CALENDAR_PATH)


def test_constants_match_frozen_spec():
    s = frozen()
    assert s["status"] == "frozen" and s["version"] == 1 and s["symbol"] == g.SYMBOL
    assert s["data"]["file"] == g.CSV_NAME and s["data"]["sha256"] == g.CSV_SHA256
    c = s["calendar"]
    assert c["file"] == g.CALENDAR_PATH and c["sha256"] == g.CALENDAR_SHA256
    assert tuple(c["gotobi_days"]) == g.GOTOBI_DAYS and c["february_month_end_event"] is False
    assert s["trade"]["entry_bar_utc"] == g.ENTRY_UTC.strftime("%H:%M") and s["trade"]["exit_bar_utc"] == g.EXIT_UTC.strftime("%H:%M")
    k = s["costs"]
    assert (g.SPREAD_FLOOR, g.COMMISSION, g.STRESS) == (k["spread_floor"], k["commission"], k["stress_multiplier"])
    assert g.SLIPPAGE_RATIO == pytest.approx(k["slippage_ratio_of_floor"])
    assert [str(d) for d in g.PRIMARY] == s["samples"]["primary"] and [str(d) for d in g.SECONDARY] == s["samples"]["secondary"]
    q = s["primary"]
    assert (g.MIN_T, g.PLACEBO_MIN_T, g.MIN_YEAR_SHARE, g.MIN_YEAR_EVENTS, g.MIN_TRADES) == (
        q["min_t"], q["placebo_welch_t_min"], q["min_year_share"], q["min_year_events"], q["min_trades"])


def test_calendar_hash_is_enforced(tmp_path):
    bad = tmp_path / "c.json"
    bad.write_text('{"dates": []}')
    with pytest.raises(ValueError, match="sha256"):
        g.load_closures(bad)


def test_event_counts_match_frozen_calendar_only(closures):
    s = frozen()["power"]
    assert len(g.gotobi_days(*g.PRIMARY, closures)) == s["calendar_events_primary"] == 519
    assert len(g.gotobi_days(*g.SECONDARY, closures)) == s["calendar_events_secondary"] == 405


def test_gotobi_rules(closures):
    feb = [d for d in g.gotobi_days(date(2019, 2, 1), date(2019, 2, 28), closures)]
    assert [d.day for d in feb] == [5, 8, 15, 20, 25]  # Feb 10 2019 is a Sunday -> Friday 8th; no month-end event
    assert date(2019, 2, 28) not in feb
    # 2016-02-29 (leap) is not an event either.
    assert date(2016, 2, 29) not in g.gotobi_days(date(2016, 2, 1), date(2016, 2, 29), closures)
    # A 30th on a Saturday rolls to Friday 29th.
    assert date(2019, 11, 29) in g.gotobi_days(date(2019, 11, 1), date(2019, 11, 30), closures)
    # Holiday roll: 2020-02-24 (substitute holiday) is not a business day; 2020-02-25 is a Tuesday event.
    days = g.gotobi_days(date(2020, 1, 1), date(2020, 12, 31), closures)
    assert all(g.is_business_day(d, closures) for d in days)
    # Jan 5 2020 (Sunday) rolls past the Dec 31 - Jan 3 bank closures to Monday Dec 30, which is also that month's 30th.
    jan = g.gotobi_days(date(2019, 12, 1), date(2020, 1, 31), closures)
    assert date(2019, 12, 30) in jan and not any(date(2019, 12, 31) <= d <= date(2020, 1, 3) for d in jan)
    assert len(days) == len(set(days))


def test_placebo_excludes_gotobi(closures):
    gd = g.gotobi_days(date(2018, 1, 1), date(2018, 12, 31), closures)
    pd = g.placebo_days(date(2018, 1, 1), date(2018, 12, 31), closures, gd)
    assert not set(gd) & set(pd) and all(g.is_business_day(d, closures) for d in pd)


def bars_for(days, move_bps=0.0, placebo_move=0.0, gotobi=()):
    """Hourly bars around 00:00-01:00 UTC for each day; the 00:00->01:00 open-to-open move is set per day."""
    rng, out = random.Random(3), []
    for d in days:
        px = 110 + rng.gauss(0, 0.5)
        mv = move_bps if d in gotobi else placebo_move
        for h, o in ((23, px), (0, px), (1, px * (1 + mv / 1e4)), (2, px * (1 + mv / 1e4))):
            ts = datetime.combine(d, datetime.min.time(), UTC) + timedelta(hours=h) - (timedelta(days=1) if h == 23 else timedelta())
            out.append(Bar(ts, o, o + 0.01, o - 0.01, o))
    return sorted(out, key=lambda b: b.timestamp)


def test_trade_fills_and_costs():
    d = date(2019, 3, 5)
    bars = bars_for([d], move_bps=10, gotobi={d})
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    t = g.day_trade(bars, idx, d, g.COSTS)
    o0 = [b for b in bars if b.timestamp == datetime(2019, 3, 5, 0, tzinfo=UTC)][0].open
    assert t.entry_time == datetime(2019, 3, 5, 0, tzinfo=UTC) and t.exit_time == datetime(2019, 3, 5, 1, tzinfo=UTC)
    assert t.entry_price == pytest.approx(o0 + 0.0125 + 0.025 / 6)
    assert g.gross_bps(t) == pytest.approx(10)
    assert g.net_bps(t) < 10
    missing = [b for b in bars if b.timestamp != datetime(2019, 3, 5, 1, tzinfo=UTC)]
    assert g.day_trade(missing, {b.timestamp: i for i, b in enumerate(missing)}, d, g.COSTS) is None


def test_per_bar_spread_floor_and_stress():
    d = date(2019, 3, 5)
    bars = [replace(b, spread=0.05) for b in bars_for([d], gotobi={d})]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    t = g.day_trade(bars, idx, d, g.COSTS)
    assert t.entry_price - t.mid_entry == pytest.approx(0.025 + 0.025 / 6)  # wider per-bar spread wins
    sb, sc = g.stressed(bars, g.COSTS)
    ts = g.day_trade(sb, idx, d, sc)
    assert ts.entry_price - ts.mid_entry == pytest.approx(0.05 + 2 * 0.025 / 6)


def _all_days(closures, a, b):
    out, d = [], a
    while d <= b:
        if g.is_business_day(d, closures):
            out.append(d)
        d += timedelta(days=1)
    return out


def test_evaluate_qualifies_true_effect_and_rejects_hour_drift(closures):
    period = (date(2014, 1, 1), date(2020, 12, 31))
    days = _all_days(closures, *period)
    gd = set(g.gotobi_days(*period, closures))
    rng = random.Random(9)
    # Genuine gotobi effect: +8 bps on gotobi days, 0 otherwise, plus noise.
    def make(effect, drift):
        out = []
        for d in days:
            mv = (effect if d in gd else 0.0) + drift + rng.gauss(0, 6)
            out += bars_for([d], move_bps=mv, gotobi={d})
        return sorted(out, key=lambda b: b.timestamp)
    good = g.evaluate(make(8.0, 0.0), period, closures)
    assert good.qualified, good.failures
    assert good.net.n == len(gd) and good.placebo_gross.n == len(days) - len(gd)
    # Same-hour drift on every day, no gotobi difference: placebo rule must fail.
    drift = g.evaluate(make(0.0, 8.0), period, closures)
    assert not drift.qualified and any("placebo" in f for f in drift.failures)


def test_year_rule_ignores_short_stub(closures):
    period = (date(2013, 8, 26), date(2014, 12, 31))
    days = _all_days(closures, *period)
    ev = g.evaluate(sorted([b for d in days for b in bars_for([d], move_bps=5, gotobi={d})], key=lambda b: b.timestamp), period, closures)
    assert 2013 in ev.years and 2013 not in ev.counted_years and ev.counted_years == [2014]


def test_csv_hash_is_enforced(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("x")
    with pytest.raises(ValueError, match="sha256"):
        g.install_csv(f, tmp_path / "out")
    assert not (tmp_path / "out").exists()
    assert g.install_csv(f, tmp_path / "out", expected=g.sha256_file(f)).read_text() == "x"
