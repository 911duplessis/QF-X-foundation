import math
from datetime import datetime, timedelta, timezone

import pytest

from qfx.backtest.types import Side, Trade
from qfx.research.power import (
    Z_ALPHA, Z_POWER, mde_drift, mde_t, mde_windows, p_windows_pass, phi, resolution, se_day, se_iid,
)


def trade(day, hour, bps_val):
    t0 = datetime(2024, 1, day, hour, tzinfo=timezone.utc)
    net = bps_val / 1e4 * 100
    return Trade(Side.LONG, t0, t0 + timedelta(hours=1), 100.0, 100.0, net, 0.0, net, mid_entry=100.0, mid_exit=100.0 + net)


def test_mde_t_gives_80pct_power_at_t2():
    se = 5.0
    delta = mde_t(se)
    assert phi(delta / se - 2.0) == pytest.approx(0.80, abs=1e-6)


def test_mde_drift_gives_80pct_power_at_5pct():
    sd = 3.0
    assert phi(mde_drift(sd) / sd - Z_ALPHA) == pytest.approx(0.80, abs=1e-6)


def test_window_rule_power_is_monotone_and_solved():
    sd, per, w = 100.0, 30, 6
    assert p_windows_pass(0.0, sd, per, w) == pytest.approx(sum(math.comb(6, k) for k in (4, 5, 6)) / 64)
    d = mde_windows(sd, per, w)
    assert p_windows_pass(d, sd, per, w) == pytest.approx(0.80, abs=1e-6)
    assert p_windows_pass(d * 1.2, sd, per, w) > 0.80 > p_windows_pass(d * 0.8, sd, per, w)


def test_se_day_equals_iid_when_one_trade_per_day():
    trades = [trade(d, 10, v) for d, v in zip(range(1, 8), [5, -3, 8, 1, -2, 7, 4])]
    x = [5, -3, 8, 1, -2, 7, 4]
    assert se_day(trades) == pytest.approx(se_iid(x))


def test_design_mde_is_largest_component():
    trades = [trade(1 + i % 28, i % 24, (-1) ** i * 50 + 3) for i in range(200)]
    r = resolution("x", "S", trades, 6, cost_bps=5.0, null_sd=2.0)
    assert r.design_mde == max(r.mde_t_day, r.mde_windows, r.mde_drift)
    assert r.mde_over_cost == pytest.approx(r.design_mde / 5.0)
    r2 = resolution("x", "S", trades, 6, cost_bps=5.0, null_sd=None)
    assert r2.mde_drift is None and r2.design_mde == max(r2.mde_t_day, r2.mde_windows)
