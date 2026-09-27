"""Checkpoint-4 tests. Synthetic data only: no test reads the replication exports."""
import json
import math
import random
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qfx.backtest.financing import SwapSpec, financing_cost_bps, rollover_charges
from qfx.backtest.types import Bar, ExecutionCosts, Side, Trade
from qfx.research.drift import CONFIG as DRIFT_CONFIG
from qfx.research.drift import Gates
from qfx.research.evaluation import trade_stats
from qfx.research.replication import (
    COMMISSION, DRIFT_MAX_P, ELIGIBLE, MIN_CLUSTERED_T, ORIGIN, SLIPPAGE_RATIO, SPEC_PATH, SPREAD_FLOORS,
    STANDARD_SWAPS, Coin, block_drift_segment, clustered_t, costs_for, pooled_windows, qualify_replication,
)
from qfx.research.walkforward import Stability, WalkForwardConfig, rolling_windows, run_walkforward, vol_expansion_spec

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def frozen():
    text = (ROOT / SPEC_PATH).read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


def test_constants_match_frozen_spec():
    spec = frozen()
    c4 = spec["checkpoint4"]
    assert spec["version"] == 2 and c4["strategy_computation_before_checkpoint4"] is False
    assert list(ELIGIBLE) == c4["eligible"]
    assert ORIGIN.isoformat().replace("+00:00", "Z") == c4["origin"] == spec["walkforward"]["common_origin"]
    assert MIN_CLUSTERED_T == c4["clustered_t_min"] == spec["primary"]["clustered_t_min"]
    assert DRIFT_MAX_P == c4["drift"]["max_p"]
    assert DRIFT_CONFIG.repetitions == c4["drift"]["repetitions"] == 500
    assert DRIFT_CONFIG.repetitions + 1 == c4["drift"]["p_denominator"]
    assert DRIFT_CONFIG.max_redraws == c4["drift"]["max_redraws"]
    assert SLIPPAGE_RATIO == pytest.approx(spec["costs"]["slippage_ratio_of_floor"])
    assert COMMISSION == spec["costs"]["commission"] == 0.0
    for sym in ELIGIBLE:
        assert SPREAD_FLOORS[sym] == pytest.approx(spec["costs"]["spread_floor_values"][sym])
        assert STANDARD_SWAPS[sym].long_points == spec["financing"]["standard_long_swap_points"][sym]
    assert STANDARD_SWAPS["BTCUSD"].long_points == spec["financing"]["standard_long_swap_points"]["BTCUSD.m"]


def test_costs_follow_frozen_rule():
    c = costs_for("ETHUSD.m")
    assert c.spread == 1.4 and c.slippage == pytest.approx(1.4 / 6) and c.commission == 0.0 and c.delay_bars == 1


# --- clustered t ------------------------------------------------------------------


def trade(entry, net):
    return Trade(Side.LONG, entry, entry + timedelta(hours=2), 100.0, 100.0, net, 0.0, net, mid_entry=100.0, mid_exit=100.0)


def test_one_trade_per_day_equals_iid_t():
    vals = [5, -3, 8, 1, -2, 7, 4]
    trades = [trade(datetime(2024, 1, 1 + i, 10, tzinfo=UTC), v / 100) for i, v in enumerate(vals)]
    ct = clustered_t(trades, 3)
    assert ct.unique_days == ct.trades == 7 and ct.windows == 3
    assert ct.clustered_t == pytest.approx(ct.raw_t)


def test_same_day_clustering_shrinks_t():
    days = [datetime(2024, 1, d, tzinfo=UTC) for d in (1, 2, 3, 4)]
    vals = [10, 12, -2, 11]
    trades = [trade(day + timedelta(hours=h), v / 100) for day, v in zip(days, vals) for h in range(3)]  # 3 copies per day
    ct = clustered_t(trades, 1)
    assert ct.trades == 12 and ct.unique_days == 4
    assert ct.clustered_t < ct.raw_t  # correlated same-day trades carry less information
    # Triplicating each trade within its day adds no information: clustered t is unchanged exactly.
    single = clustered_t([trade(d, v / 100) for d, v in zip(days, vals)], 1)
    assert ct.clustered_t == pytest.approx(single.clustered_t)


def test_single_cluster_cannot_qualify():
    trades = [trade(datetime(2024, 1, 1, h, tzinfo=UTC), 0.05) for h in range(10)]
    assert clustered_t(trades, 1).clustered_t == 0.0


def test_clustered_formula_by_hand():
    # Two days: day1 {+2, +4}, day2 {-1}; values in bps via net/entry*1e4.
    trades = [trade(datetime(2024, 1, 1, 1, tzinfo=UTC), 0.02), trade(datetime(2024, 1, 1, 5, tzinfo=UTC), 0.04),
              trade(datetime(2024, 1, 2, 1, tzinfo=UTC), -0.01)]
    x = [2.0, 4.0, -1.0]
    m = sum(x) / 3
    s1, s2 = (2 - m) + (4 - m), (-1 - m)
    se = math.sqrt(2 / 1 * (s1 ** 2 + s2 ** 2)) / 3
    assert clustered_t(trades, 1).clustered_t == pytest.approx(m / se)


# --- financing ------------------------------------------------------------------------


ATH = SwapSpec(-100.0, 0.01)


def at(y, mo, d, h):  # server time (Europe/Athens) -> UTC
    from zoneinfo import ZoneInfo
    return datetime(y, mo, d, h, tzinfo=ZoneInfo("Europe/Athens")).astimezone(UTC)


def test_rollover_counting():
    # 2026-09-21 is a Monday.
    assert rollover_charges(at(2026, 9, 21, 20), at(2026, 9, 21, 20), ATH) == 0  # held [20:00, 21:00)
    assert rollover_charges(at(2026, 9, 21, 20), at(2026, 9, 21, 21), ATH) == 0  # held [20:00, 22:00): excludes 22:00
    assert rollover_charges(at(2026, 9, 21, 20), at(2026, 9, 21, 22), ATH) == 1  # exit bar 22:00 -> held through it
    assert rollover_charges(at(2026, 9, 23, 21), at(2026, 9, 23, 23), ATH) == 3  # Wednesday triple
    assert rollover_charges(at(2026, 9, 26, 10), at(2026, 9, 27, 23), ATH) == 0  # Saturday + Sunday
    assert rollover_charges(at(2026, 9, 21, 20), at(2026, 9, 24, 23), ATH) == 1 + 1 + 3 + 1


def test_financing_cost_in_bps():
    t = Trade(Side.LONG, at(2026, 9, 21, 20), at(2026, 9, 21, 23), 100.0, 100.0, 0, 0, 0, mid_entry=100.0, mid_exit=100.0)
    assert financing_cost_bps(t, ATH) == pytest.approx(100 * 0.01 / 100 * 1e4)  # one charge of 1.0 on 100 = 100 bps


# --- windows and pooling -----------------------------------------------------------------


def walk(start, n, seed):
    rng = random.Random(seed)
    price, out = 100.0, []
    for i in range(n):
        o = price
        price *= math.exp(rng.gauss(0, 0.003))
        out.append(Bar(start + timedelta(hours=i), o, max(o, price) * (1 + abs(rng.gauss(0, 0.002))),
                       min(o, price) * (1 - abs(rng.gauss(0, 0.002))), price))
    return out


CFG = WalkForwardConfig(train_months=4, validation_months=1, test_months=1, step_months=1, min_train_trades=5, min_validation_trades=1)
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def test_common_origin_aligns_windows_across_series():
    a = [b.timestamp for b in walk(T0, 24 * 300, 1)]
    b = [b.timestamp for b in walk(T0 + timedelta(hours=7), 24 * 300, 2)]
    wa, wb = rolling_windows(a, CFG, T0), rolling_windows(b, CFG, T0)
    assert len(wa) == len(wb)
    for x, y in zip(wa, wb):
        assert abs((a[x.test.start] - b[y.test.start]).total_seconds()) <= 7 * 3600
    assert rolling_windows(a, CFG) == rolling_windows(a, CFG, None)  # default unchanged


def reports_for(series):
    spec = vol_expansion_spec("vol_expansion_long")
    return [run_walkforward(f"C{i}", bars, spec, ExecutionCosts(spread=0.01), CFG, T0) for i, bars in enumerate(series)]


def test_pooled_windows_sum_coin_trades():
    series = [walk(T0, 24 * 330, s) for s in (3, 4)]
    reps = reports_for(series)
    forced = pooled_windows(reps, deployed_only=False)
    for k, w in enumerate(forced):
        assert w.test.trades == sum(r.windows[k].test.trades for r in reps)
        assert w.periods == reps[0].windows[k].periods
    dep = pooled_windows(reps, deployed_only=True)
    for k, w in enumerate(dep):
        assert w.deployed == any(r.windows[k].deployed for r in reps)
        assert w.test.trades == sum(r.windows[k].test.trades for r in reps if r.windows[k].deployed)


# --- block drift ------------------------------------------------------------------------------


def coin(sym, bars, costs, gate_costs=None):
    spec = vol_expansion_spec("vol_expansion_long")
    c = Coin(sym, bars, costs, Gates.for_bars(bars, gate_costs or costs), spec.bind(bars), rolling_windows([b.timestamp for b in bars], CFG, T0))
    c.index = {b.timestamp: i for i, b in enumerate(bars)}
    return c


PARAMS = {"box_bars": 12, "stop": "box_opposite", "target_r": 1.0}


def test_group_members_share_one_random_timestamp():
    bars = walk(T0, 24 * 330, 5)
    twin = [replace(b) for b in bars]
    coins = [coin("A", bars, ExecutionCosts(spread=0.01)), coin("B", twin, ExecutionCosts(spread=0.01))]
    obs, ctrl, drp, groups = block_drift_segment(coins, [PARAMS, PARAMS], 1, "test", 5, 20)
    assert groups > 5 and len(obs) % 2 == 0
    for rep in ctrl:
        half = len(rep) // 2
        assert len(rep) % 2 == 0 and rep[:half] == rep[half:]  # identical coins replayed at identical times


def test_member_gate_failure_drops_whole_group():
    bars = walk(T0, 24 * 330, 6)
    twin = [replace(b) for b in bars]
    coins = [coin("A", bars, ExecutionCosts(spread=0.01)),
             coin("B", twin, ExecutionCosts(spread=0.01), gate_costs=ExecutionCosts(spread=1e6))]
    obs, ctrl, drp, groups = block_drift_segment(coins, [PARAMS, PARAMS], 1, "test", 4, 20)
    assert groups > 0
    assert all(d == groups for d in drp)  # every group contains B, whose gate always fails
    assert all(rep == [] for rep in ctrl)  # A is never placed without B


def test_block_drift_is_deterministic():
    bars = walk(T0, 24 * 330, 7)
    other = walk(T0, 24 * 330, 8)
    make = lambda: [coin("A", bars, ExecutionCosts(spread=0.01)), coin("B", other, ExecutionCosts(spread=0.01))]
    a = block_drift_segment(make(), [PARAMS, PARAMS], 2, "test", 6, 20)
    b = block_drift_segment(make(), [PARAMS, PARAMS], 2, "test", 6, 20)
    assert a == b


# --- qualification ------------------------------------------------------------------------------


def stab(**kw):
    e = trade_stats([], None, 0)
    base = dict(windows=5, traded_windows=5, abstained_windows=0, pct_profitable=0.8, median_window_bps=5.0,
                worst_window_bps=-2.0, worst_window_total_bps=-20.0, dispersion_bps=3.0, iqr_bps=4.0,
                pct_survive_stress=0.8, concentration=0.3, pooled_validation=replace(e, net_bps=3.0),
                pooled_test=replace(e, trades=300, net_bps=4.0, t_stat=9.0),
                pooled_test_stressed=replace(e, net_bps=2.0))
    base.update(kw)
    return Stability(**base)


def ct(v):
    from qfx.research.replication import ClusteredT
    return ClusteredT(300, 120, 5, 4.0, 9.0, v)


def test_qualification_uses_clustered_not_iid_t():
    cfg = WalkForwardConfig()
    assert qualify_replication(stab(), ct(2.5), 0.01, cfg)[0]
    ok, fails = qualify_replication(stab(), ct(1.4), 0.01, cfg)  # IID t = 9 cannot rescue it
    assert not ok and fails == ["day-clustered t +1.40 < 2.0"]
    ok, fails = qualify_replication(stab(pooled_test=replace(trade_stats([], None, 0), trades=300, net_bps=4.0, t_stat=0.5)), ct(2.5), 0.01, cfg)
    assert ok  # low IID t is not the qualification statistic


def test_drift_and_walkforward_rules_still_apply():
    cfg = WalkForwardConfig()
    ok, fails = qualify_replication(stab(), ct(2.5), 0.2, cfg)
    assert not ok and fails == ["block drift p 0.200 > 0.05"]
    ok, fails = qualify_replication(stab(concentration=0.9), ct(2.5), 0.01, cfg)
    assert not ok and any("one window" in f for f in fails)
