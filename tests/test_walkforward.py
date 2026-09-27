import json
import math
import random
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from qfx.backtest.types import Bar, ExecutionCosts
from qfx.research.evaluation import trade_stats
from qfx.research.walkforward import (
    HypothesisSpec,
    Stability,
    WalkForwardConfig,
    add_months,
    qualify,
    render,
    results_json,
    rolling_windows,
    run_walkforward,
    trend_continuation_spec,
)

CFG = WalkForwardConfig(train_months=4, validation_months=1, test_months=1, step_months=1, min_train_trades=5, min_validation_trades=1)


def walk(n=24 * 365, seed=3, drift=0.0):
    rng = random.Random(seed)
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    price, bars = 100.0, []
    for i in range(n):
        o = price
        price *= math.exp(drift + rng.gauss(0, 0.003))
        bars.append(Bar(t0 + timedelta(hours=i), o, max(o, price) * 1.001, min(o, price) * 0.999, price))
    return bars


def small_spec() -> HypothesisSpec:
    full = trend_continuation_spec()
    grid = ({"lookback": 24, "entry_z": 1.0}, {"lookback": 72, "entry_z": 1.5})
    return HypothesisSpec(full.name, grid, full.bind)


def test_add_months_clamps_day():
    assert add_months(datetime(2025, 1, 31), 1) == datetime(2025, 2, 28)
    assert add_months(datetime(2024, 1, 31), 1) == datetime(2024, 2, 29)
    assert add_months(datetime(2025, 11, 15), 3) == datetime(2026, 2, 15)


def test_windows_are_chronological_contiguous_and_non_overlapping():
    stamps = [b.timestamp for b in walk()]
    windows = rolling_windows(stamps, CFG)
    assert len(windows) >= 6
    for w in windows:
        assert w.train.start < w.train.end == w.validation.start < w.validation.end == w.test.start < w.test.end
    for a, b in zip(windows, windows[1:]):
        assert a.test.end == b.test.start  # contiguous test coverage, no overlap


def test_partial_final_window_needs_minimum_coverage():
    stamps = [b.timestamp for b in walk(24 * (30 * 6 + 5))]  # ~6 months + 5 days
    assert rolling_windows(stamps, CFG)[-1].test.end <= len(stamps)
    strict = replace(CFG, min_partial_test_fraction=1.0)
    assert all(stamps[w.test.end - 1] - stamps[w.test.start] >= timedelta(days=27) for w in rolling_windows(stamps, strict))


def test_selection_never_sees_test_data():
    bars = walk()
    base = run_walkforward("T", bars, small_spec(), ExecutionCosts(spread=0.01), CFG)
    target = base.windows[2]
    start = rolling_windows([b.timestamp for b in bars], CFG)[2].test.start
    # Replace everything from the window's test segment onward with an
    # independent random path (different returns, not just rescaled prices).
    other = walk(seed=99)
    scale = bars[start - 1].close / other[start - 1].close
    scrambled = bars[:start] + [
        replace(b, open=o.open * scale, high=o.high * scale, low=o.low * scale, close=o.close * scale)
        for b, o in zip(bars[start:], other[start:])
    ]
    again = run_walkforward("T", scrambled, small_spec(), ExecutionCosts(spread=0.01), CFG).windows[2]
    assert again.test != target.test  # the test data really changed
    assert again.params == target.params
    assert again.deployed == target.deployed
    assert again.train == target.train
    assert again.validation == target.validation


def test_deployed_track_abstains_and_forced_always_trades():
    report = run_walkforward("T", walk(), small_spec(), ExecutionCosts(spread=0.01), CFG)
    assert report.forced.abstained_windows == 0
    for w in report.windows:
        assert w.deployed == (w.abstain_reason == "")
    assert report.deployed.abstained_windows == sum(1 for w in report.windows if not w.deployed)


def _stability(**kw):
    empty = trade_stats([], [], 0)
    base = dict(windows=5, traded_windows=5, abstained_windows=0, pct_profitable=0.8, median_window_bps=5.0,
                worst_window_bps=-2.0, worst_window_total_bps=-20.0, dispersion_bps=3.0, iqr_bps=4.0,
                pct_survive_stress=0.8, concentration=0.3, pooled_validation=replace(empty, net_bps=3.0),
                pooled_test=replace(empty, trades=100, net_bps=4.0, t_stat=2.5),
                pooled_test_stressed=replace(empty, net_bps=2.0))
    base.update(kw)
    return Stability(**base)


def test_qualification_passes_only_consistent_results():
    assert qualify(_stability(), CFG)[0]
    ok, fails = qualify(_stability(concentration=0.9), CFG)
    assert not ok and "one window" in fails[0]
    ok, fails = qualify(_stability(pct_profitable=0.4, median_window_bps=-1.0), CFG)
    assert not ok and len(fails) == 2
    assert qualify(_stability(traded_windows=0), CFG) == (False, ["no traded test windows"])


def test_one_exceptional_window_cannot_qualify():
    # Pooled numbers look excellent, but P&L comes from a single window.
    ok, fails = qualify(_stability(pct_profitable=0.2, median_window_bps=-3.0, concentration=3.0), CFG)
    assert not ok
    assert any("profitable windows" in f for f in fails) and any("one window" in f for f in fails)


def test_outputs_are_strict_json_and_markdown():
    spec = small_spec()
    report = run_walkforward("T", walk(), spec, ExecutionCosts(spread=0.01), CFG)
    payload = results_json(spec, CFG, [report])
    text = json.dumps(payload, allow_nan=False)
    data = json.loads(text)
    assert data["schema_version"] == 1
    assert len(data["symbols"]["T"]["windows"]) == len(report.windows)
    assert "_runs" not in data["symbols"]["T"]["windows"][0]
    md = render(spec, CFG, [report])
    assert "## T" in md and "Stability across test windows" in md
