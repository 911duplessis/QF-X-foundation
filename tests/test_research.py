import math
import random
from datetime import datetime, timedelta, timezone

import pytest

from qfx.backtest.engine import run_backtest
from qfx.backtest.types import Bar, ExecutionCosts, Side
from qfx.research.baseline import run_symbol
from qfx.research.evaluation import trade_stats
from qfx.research.features import ewma_vol, log_returns, trend_z
from qfx.research.hypotheses import TrendParams, trend_continuation
from qfx.research.splits import chronological_split


def walk(n=600, seed=7, drift=0.0):
    rng = random.Random(seed)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price, bars = 100.0, []
    for i in range(n):
        o = price
        price *= math.exp(drift + rng.gauss(0, 0.002))
        bars.append(Bar(t0 + timedelta(hours=i), o, max(o, price) * 1.0005, min(o, price) * 0.9995, price))
    return bars


def same(a, b):
    return len(a) == len(b) and all((x != x and y != y) or x == pytest.approx(y) for x, y in zip(a, b))


def test_features_are_causal():
    closes = [b.close for b in walk()]
    full_vol = ewma_vol(log_returns(closes), 50)
    full_z = trend_z(closes, 24, full_vol)
    for cut in (30, 200, 450):
        part = closes[:cut]
        vol = ewma_vol(log_returns(part), 50)
        assert same(vol, full_vol[:cut])
        assert same(trend_z(part, 24, vol), full_z[:cut])


def test_trend_z_warmup_is_nan():
    closes = [b.close for b in walk(50)]
    z = trend_z(closes, 24, ewma_vol(log_returns(closes), 10))
    assert all(v != v for v in z[:24])


def test_chronological_split_is_ordered_and_complete():
    segs = chronological_split(100)
    assert [(s.start, s.end) for s in segs] == [(0, 60), (60, 80), (80, 100)]
    with pytest.raises(ValueError):
        chronological_split(100, 0.8, 0.3)


def test_strong_uptrend_goes_long_and_holds():
    bars = walk(400, drift=0.002)
    sig = trend_continuation(bars, TrendParams(lookback=24, vol_halflife=50))
    sides = [sig(bars, i) for i in range(len(bars))]
    assert Side.LONG in sides and Side.SHORT not in sides[100:]


def test_volatility_shock_forces_no_trade():
    bars = walk(400, drift=0.002)
    shock = bars[300]
    bars[300] = Bar(shock.timestamp, shock.open, shock.open * 1.2, shock.open * 0.99, shock.open * 1.15)
    params = TrendParams(lookback=24, vol_halflife=50, shock_halflife=3, shock_ratio=2.0)
    sig = trend_continuation(bars, params)
    sides = [sig(bars, i) for i in range(len(bars))]
    assert sides[300] is None


def test_offset_maps_segment_to_global_features():
    bars = walk(400, drift=0.002)
    params = TrendParams(lookback=24, vol_halflife=50)
    whole = trend_continuation(bars, params)
    full = [whole(bars, i) for i in range(len(bars))]
    seg = trend_continuation(bars, params, offset=200)
    assert [seg(bars[200:], i) for i in range(200)] == full[200:]


def test_trade_stats_cost_drag_and_empty():
    bars = walk(300, drift=0.002)
    params = TrendParams(lookback=24, vol_halflife=50)
    costs = ExecutionCosts(spread=0.05)
    net = run_backtest(bars, trend_continuation(bars, params), costs=costs)
    ideal = run_backtest(bars, trend_continuation(bars, params))
    stats = trade_stats(net, ideal, 300)
    assert stats.trades == len(net) > 0
    assert stats.cost_bps > 0
    assert stats.net_bps == pytest.approx(stats.gross_bps - stats.cost_bps)
    assert trade_stats([], [], 10).trades == 0


def test_run_symbol_smoke():
    result = run_symbol("TEST", walk(2000, drift=0.0005), ExecutionCosts(spread=0.01))
    assert [s.segment for s in result.segments] == ["train", "validation", "test"]
    assert result.stressed_test.cost_bps >= result.segments[2].stats.cost_bps


def test_verdict_rejects_thin_or_inconsistent_results():
    from qfx.research.baseline import verdict
    result = run_symbol("TEST", walk(2000, drift=0.0005), ExecutionCosts(spread=0.01))
    ok, reason = verdict(result)
    if result.segments[2].stats.trades < 30:
        assert not ok and "test trades" in reason
