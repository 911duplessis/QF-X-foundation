"""FX Session Directional Persistence v1. Synthetic data only: no test reads
the quarantined FX archive or any FX export."""
import json
import math
import random
import re
import zipfile
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from qfx.backtest.types import Bar, ExecutionCosts, Side
from qfx.research import fx_session as fx
from qfx.research.drift import CONFIG as DRIFT_CONFIG
from qfx.research.splits import Segment
from qfx.research.walkforward import WalkForwardConfig, run_segment

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
ATHENS = ZoneInfo("Europe/Athens")


def frozen():
    text = (ROOT / fx.SPEC_PATH).read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


def make_bars(end: datetime, seed: int = 1, start: datetime = fx.ORIGIN, sigma: float = 0.0008) -> list[Bar]:
    """FX-like hourly bars: no Saturday, Sunday only from 22:00 UTC."""
    rng = random.Random(seed)
    out, px, ts = [], 1.1, start
    while ts < end:
        wd = ts.weekday()
        if not (wd == 5 or (wd == 6 and ts.hour < 22)):
            o = px
            c = o + rng.gauss(0, sigma)
            out.append(Bar(ts, o, max(o, c) + abs(rng.gauss(0, sigma / 2)), min(o, c) - abs(rng.gauss(0, sigma / 2)), c))
            px = c
        ts += timedelta(hours=1)
    return out


def pair(bars, symbol="EURUSD.m", costs=None):
    return fx.Pair(symbol, bars, costs or ExecutionCosts(spread=0.0001, slippage=0.00002))


def set_close(bars, i, close):
    b = bars[i]
    bars[i] = replace(b, close=close, high=max(b.high, close), low=min(b.low, close))


# --- frozen constants ---------------------------------------------------------------


def test_constants_match_frozen_spec():
    s = frozen()
    assert s["status"] == "frozen" and s["version"] == 1
    assert list(fx.UNIVERSE) == s["universe"]
    assert fx.ARCHIVE_SHA256 == s["data"]["archive_sha256"]
    assert fx.ORIGIN.isoformat().replace("+00:00", "Z") == s["data"]["origin"]
    assert s["session"] == {"tz": "Europe/London", "open": "08:00", "time_exit_bar_open": "16:00", "days": "mon-fri"}
    assert str(fx.LONDON) == "Europe/London" and fx.SESSION_OPEN.isoformat() == "08:00:00" and fx.TIME_EXIT.isoformat() == "16:00:00"
    assert [g["window_hours"] for g in fx.GRID] == [1, 1, 2, 2] and sorted({g["theta"] for g in fx.GRID}) == s["grid"]["theta"]
    assert sorted({g["window_hours"] for g in fx.GRID}) == s["grid"]["window_hours"]
    f = s["fixed"]
    assert (fx.ATR_PERIOD, fx.MIN_HISTORY_BARS, fx.STOP_ATR) == (f["atr_period"], f["min_history_bars"], f["stop_atr"])
    assert f["target"] is None and f["delay_bars"] == 1 == fx.costs_for("EURUSD.m").delay_bars
    c = s["costs"]
    assert fx.SPREAD_FLOORS == pytest.approx(c["spread_floor_values"])
    assert fx.SLIPPAGE_RATIO == pytest.approx(c["slippage_ratio_of_floor"]) and fx.COMMISSION == c["commission"] == 0.0
    wf, cfg = s["walkforward"], WalkForwardConfig()
    assert (cfg.train_months, cfg.validation_months, cfg.test_months, cfg.step_months) == (24, 6, 6, 6) == (
        wf["train_months"], wf["validation_months"], wf["test_months"], wf["step_months"])
    assert (cfg.min_train_trades, cfg.min_validation_trades, cfg.min_partial_test_fraction, cfg.stress_multiplier) == (
        wf["min_train_trades"], wf["min_validation_trades"], wf["min_partial_test_fraction"], c["stress_multiplier"])
    assert fx.MIN_CLUSTERED_T == s["primary"]["clustered_t_min"] and fx.DRIFT_MAX_P == s["primary"]["drift_max_p"]
    d = s["drift"]
    assert DRIFT_CONFIG.repetitions == d["repetitions"] == 500 and d["p_denominator"] == 501
    assert DRIFT_CONFIG.max_redraws == d["max_redraws"] and fx.NAME == d["seed_label"]


def test_costs_follow_frozen_rule():
    c = fx.costs_for("NZDUSD.m")
    assert c.spread == 0.00014 and c.slippage == pytest.approx(0.00014 / 6) and c.commission == 0.0


# --- session clock -------------------------------------------------------------------


def test_london_anchor_is_dst_aware():
    assert fx.london_utc(date(2024, 1, 15), fx.SESSION_OPEN) == datetime(2024, 1, 15, 8, tzinfo=UTC)
    assert fx.london_utc(date(2024, 7, 15), fx.SESSION_OPEN) == datetime(2024, 7, 15, 7, tzinfo=UTC)
    # Either side of the 2024-03-31 and 2024-10-27 switches.
    assert fx.london_utc(date(2024, 3, 29), fx.SESSION_OPEN).hour == 8
    assert fx.london_utc(date(2024, 4, 1), fx.SESSION_OPEN).hour == 7
    assert fx.london_utc(date(2024, 10, 25), fx.TIME_EXIT).hour == 15
    assert fx.london_utc(date(2024, 10, 28), fx.TIME_EXIT).hour == 16


def test_session_open_is_always_10_server():
    d = date(2021, 1, 4)
    while d < date(2027, 1, 1):
        assert fx.london_utc(d, fx.SESSION_OPEN).astimezone(ATHENS).hour == 10
        assert fx.london_utc(d, fx.TIME_EXIT).astimezone(ATHENS).hour == 18
        d += timedelta(days=1)


@pytest.mark.parametrize("day", [date(2021, 3, 26), date(2021, 3, 29), date(2021, 11, 1)])
@pytest.mark.parametrize("k", [1, 2])
def test_timeline_bars(day, k):
    p = pair(make_bars(datetime(2021, 12, 1, tzinfo=UTC)))
    plan = p.plan(day, k)
    t0 = fx.london_utc(day, fx.SESSION_OPEN)
    ts = p.timestamps
    assert ts[plan.first] == t0 and plan.signal == plan.first + k - 1
    assert ts[plan.entry] == t0 + timedelta(hours=k)
    assert ts[plan.exit] == fx.london_utc(day, fx.TIME_EXIT) and not plan.late_exit


# --- causality and signal ---------------------------------------------------------------


def test_atr_excludes_window_and_later_bars():
    bars = make_bars(datetime(2021, 3, 1, tzinfo=UTC))
    day = date(2021, 2, 10)
    base = pair(bars).plan(day, 2)
    a0 = pair(bars).scale_atr(base)
    for i in range(base.first, base.exit + 1):  # window, entry and later bars
        bars[i] = replace(bars[i], high=bars[i].high + 1.0, low=bars[i].low - 1.0)
    assert pair(bars).scale_atr(pair(bars).plan(day, 2)) == a0
    bars[base.first - 1] = replace(bars[base.first - 1], high=bars[base.first - 1].high + 0.01)
    assert pair(bars).scale_atr(pair(bars).plan(day, 2)) > a0


@pytest.mark.parametrize("mult,theta,expected", [(3.0, 1.0, Side.LONG), (-3.0, 1.0, Side.SHORT), (0.4, 0.5, None), (0.0, 0.5, None)])
def test_signal_direction_and_threshold(mult, theta, expected):
    bars = make_bars(datetime(2021, 3, 1, tzinfo=UTC))
    day, k = date(2021, 2, 10), 2
    plan = pair(bars).plan(day, k)
    a = pair(bars).scale_atr(plan)
    set_close(bars, plan.signal, bars[plan.first].open + mult * a * math.sqrt(k))
    setups = fx.find_setups(pair(bars), k, theta)
    s = setups.get(plan.signal)
    assert (s.side if s else None) is expected


def test_missing_bars_skip_day_and_late_exit():
    bars = make_bars(datetime(2021, 3, 1, tzinfo=UTC))
    day = date(2021, 2, 10)
    plan = pair(bars).plan(day, 2)
    t = bars[plan.first].timestamp
    assert pair([b for b in bars if b.timestamp != t + timedelta(hours=1)]).plan(day, 2) is None  # window bar
    assert pair([b for b in bars if b.timestamp != t + timedelta(hours=2)]).plan(day, 2) is None  # entry bar
    assert pair([b for b in bars if b.timestamp != t]).plan(day, 1) is None  # 08:00 bar
    t16 = bars[plan.exit].timestamp
    late = pair([b for b in bars if b.timestamp != t16])
    lp = late.plan(day, 2)
    assert lp.late_exit and late.timestamps[lp.exit] == t16 + timedelta(hours=1)
    assert pair(bars[plan.first - 24 :]).plan(day, 2) is None  # 24 bars of history < 25


# --- execution ---------------------------------------------------------------------------------


def one_day(bars, day, k, side):
    p = pair(bars)
    plan = p.plan(day, k)
    order = p.order(plan, side)
    seg = Segment("test", 0, len(bars))
    return p, plan, order, fx.replay_trade(p, plan, side, seg)


def test_entry_and_time_exit_fills():
    bars = make_bars(datetime(2021, 3, 1, tzinfo=UTC), sigma=0.00001)
    p, plan, order, t = one_day(bars, date(2021, 2, 10), 2, Side.LONG)
    c = p.costs
    assert t.exit_reason == "time" and t.mid_entry == bars[plan.entry].open and t.mid_exit == bars[plan.exit].open
    assert t.entry_time == bars[plan.entry].timestamp and t.exit_time == bars[plan.exit].timestamp
    assert t.entry_price == pytest.approx(bars[plan.entry].open + c.spread / 2 + c.slippage)
    assert order.stop == pytest.approx(bars[plan.signal].close - 2 * p.scale_atr(plan))


def test_stop_exit_short():
    bars = make_bars(datetime(2021, 3, 1, tzinfo=UTC))
    day = date(2021, 2, 10)
    p, plan, order, _ = one_day(bars, day, 1, Side.SHORT)
    j = plan.entry + 2
    bars[j] = replace(bars[j], high=order.stop + 0.001)
    t = one_day(bars, day, 1, Side.SHORT)[3]
    assert t.exit_reason == "stop" and t.exit_time == bars[j].timestamp and t.mid_exit == max(bars[j].open, order.stop)


def test_no_position_crosses_rollover():
    p = pair(make_bars(datetime(2021, 12, 1, tzinfo=UTC)))
    seg = Segment("all", 0, len(p.bars))
    trades = run_segment(p.bars, seg, fx.session_spec(p), fx.session_spec(p).bind(p.bars), {"window_hours": 1, "theta": 0.5}, p.costs).trades
    assert len(trades) > 50
    for t in trades:
        e, x = t.entry_time.astimezone(ATHENS), t.exit_time.astimezone(ATHENS)
        assert e.date() == x.date() and x.hour < 22 and t.exit_reason in ("time", "stop")


def test_replay_matches_full_segment_run():
    p = pair(make_bars(datetime(2021, 9, 1, tzinfo=UTC)))
    seg = Segment("test", 3000, 5000)
    params = {"window_hours": 2, "theta": 0.5}
    full = run_segment(p.bars, seg, fx.session_spec(p), fx.session_spec(p).bind(p.bars), params, p.costs).trades
    replay = [fx.replay_trade(p, s.plan, s.side, seg) for s in sorted(fx.find_setups(p, 2, 0.5).values(), key=lambda s: s.plan.signal)]
    replay = [t for t in replay if t is not None]
    assert [(t.entry_time, t.exit_time, t.net_pnl) for t in full] == [(t.entry_time, t.exit_time, t.net_pnl) for t in replay]


# --- joint walk-forward and drift --------------------------------------------------------------


@pytest.fixture(scope="module")
def small_run():
    end = datetime(2024, 5, 1, tzinfo=UTC)
    pairs = [fx.Pair(s, make_bars(end, seed=i), fx.costs_for("EURUSD.m")) for i, s in enumerate(("AAA", "BBB", "CCC"))]
    return pairs, fx.run(pairs, repetitions=7)


def test_joint_selection_one_cell_for_all_pairs(small_run):
    pairs, res = small_run
    assert len(res["windows"]) >= 1
    for jw in res["windows"]:
        w = jw.result
        assert w.params in fx.GRID
        assert set(jw.per_pair) == {"AAA", "BBB", "CCC"}
        assert w.test.trades == sum(len(v["test"].trades) for v in jw.per_pair.values())
    assert res["clustered_forced"].trades == res["drift"]["test"]["pooled"].observed_trades


def test_run_is_deterministic(small_run):
    pairs, res = small_run
    again = fx.run(pairs, repetitions=7)
    assert again["drift"]["test"]["pooled"] == res["drift"]["test"]["pooled"]
    assert fx.render(again) == fx.render(res)


def _two_pair_ctxs(holes: bool):
    end = datetime(2024, 1, 10, tzinfo=UTC)
    a = make_bars(end, seed=5)
    pa, pb = pair(a, "AAA"), pair(list(a), "BBB")
    setup_days = {s.plan.day for s in fx.find_setups(pb, 1, 0.5).values()}
    if holes:  # B is ineligible (as if bars were missing) on many non-signal days
        for d in pb.days():
            if d not in setup_days and d.toordinal() % 3:
                pb._plans[(d, 1)] = None
    return fx.build_contexts([pa, pb], WalkForwardConfig())


@pytest.mark.parametrize("holes", [False, True])
def test_block_drift_keeps_or_drops_whole_groups(holes):
    ctxs = _two_pair_ctxs(holes)
    obs, ctrl, dropped, groups = fx.block_drift_segment(ctxs, {"window_hours": 1, "theta": 0.5}, 0, "test", 20, 1, fx.ReplayCache())
    assert groups > 10 and len(obs) == 2 * groups  # identical prices: every group has both pairs
    for rep, d in zip(ctrl, dropped):
        assert len(rep) == 2 * (groups - d)  # never one member without the other
    assert (sum(dropped) > 0) == holes


def test_control_replays_on_days_without_a_signal():
    ctxs = _two_pair_ctxs(False)
    pa = ctxs[0].pair
    signal_days = {s.plan.day for s in fx.find_setups(pa, 1, 0.5).values()}
    used: list = []

    class Spy(fx.ReplayCache):
        def get(self, p, plan, side, seg):
            v = super().get(p, plan, side, seg)
            if v is not None:
                used.append(plan.day)
            return v

    fx.block_drift_segment(ctxs, {"window_hours": 1, "theta": 0.5}, 0, "test", 5, 20, Spy())
    assert set(used) - signal_days  # signals are replayed, never re-detected


def test_control_keeps_each_members_side():
    ctxs = _two_pair_ctxs(False)
    got: list = []

    class Spy(fx.ReplayCache):
        def get(self, p, plan, side, seg):
            v = super().get(p, plan, side, seg)
            if v is not None:
                got.append(side)
            return v

    reps = 4
    obs, _, dropped, _ = fx.block_drift_segment(ctxs, {"window_hours": 1, "theta": 0.5}, 0, "test", reps, 20, Spy())
    assert sum(dropped) == 0
    n_obs = len(obs)
    obs_sides, ctrl_sides = got[:n_obs], got[n_obs:]
    assert Side.LONG in obs_sides and Side.SHORT in obs_sides
    for s in Side:  # every repetition replays exactly the observed side mix
        assert ctrl_sides.count(s) == reps * obs_sides.count(s)


# --- archive guard --------------------------------------------------------------------------------


def test_archive_hash_is_enforced(tmp_path):
    z = tmp_path / "a.zip"
    with zipfile.ZipFile(z, "w") as f:
        for s in fx.UNIVERSE:
            f.writestr(f"{s}_H1_202101040000_202609252300.csv", "x")
    with pytest.raises(ValueError, match="sha256"):
        fx.extract_archive(z, tmp_path / "out")
    assert not (tmp_path / "out").exists()
    written = fx.extract_archive(z, tmp_path / "out", expected=fx.sha256_file(z))
    assert len(written) == 7 and all(p.read_text() == "x" for p in written)
