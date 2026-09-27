import json
import math
import random
import re
from dataclasses import asdict, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qfx.backtest.types import Bar, ExecutionCosts, Side
from qfx.research.baseline import COSTS
from qfx.research.sweep import FIXED, GRID_AXES, HYPOTHESES, SPEC_PATH, atr, find_setups, grid, sweep_signal
from qfx.research.walkforward import WalkForwardConfig

ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)


# --- the implementation must match the frozen specification -----------------


def frozen():
    text = (ROOT / SPEC_PATH).read_text(encoding="utf-8")
    assert "Status: **FROZEN**" in text
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


def test_code_matches_frozen_spec():
    spec = frozen()
    assert spec["version"] == 1
    assert sorted(spec["hypotheses"]) == sorted(HYPOTHESES)
    assert {k: list(v) for k, v in GRID_AXES.items()} == spec["grid"]
    assert len(grid()) == 8
    assert asdict(FIXED) == spec["fixed"]
    assert ExecutionCosts().delay_bars == spec["fixed"]["delay_bars"]
    wf = asdict(WalkForwardConfig())
    assert {k: wf[k] for k in spec["walkforward"]} == spec["walkforward"]
    assert {s: {k: v for k, v in asdict(c).items() if k != "delay_bars"} for s, c in COSTS.items()} == spec["costs"]


# --- hand-built bar sequences ----------------------------------------------


def base(n=30):
    """Alternating closes 100 / 100.2 with flat highs/lows: no swings, steady vol."""
    out, prev = [], 100.2
    for i in range(n):
        c = 100.0 + 0.2 * (i % 2)
        out.append((prev, max(prev, c) + 0.3, min(prev, c) - 0.3, c))
        prev = c
    return out


def with_swing_high(after):
    """Swing high 102 at bar 30 (lookback 3, confirmed at bar 33), then ``after``."""
    rows = base()
    rows.append((100.0, 102.0, 99.9, 100.1))
    rows += [(100.1, 100.5, 99.8, 100.1)] * 3
    rows.append((100.1, 100.5, 99.8, 100.1))  # bar 34
    return to_bars(rows + list(after))


def to_bars(rows, spread=None):
    return [Bar(T0 + timedelta(hours=i), o, h, l, c, spread=spread) for i, (o, h, l, c) in enumerate(rows)]


def mirror(bars):
    return [Bar(b.timestamp, 200 - b.open, 200 - b.low, 200 - b.high, 200 - b.close) for b in bars]


SWEEP = (100.1, 102.5, 100.0, 100.8)  # bar 35: trades above 102, closes back below


def test_buy_side_sweep_gives_short_setup_on_sweep_bar():
    bars = with_swing_high([SWEEP, (100.8, 100.9, 100.5, 100.6)])
    setups = find_setups(bars, Side.SHORT, 3, "none")
    assert [i for i, s in enumerate(setups) if s] == [35]
    assert setups[35].stop == pytest.approx(102.5 + 0.5 * atr(bars, 24)[35])
    assert setups[35].signal_close == 100.8


def test_sell_side_sweep_is_exact_mirror():
    bars = with_swing_high([SWEEP, (100.8, 100.9, 100.5, 100.6)])
    short = find_setups(bars, Side.SHORT, 3, "none")
    long = find_setups(mirror(bars), Side.LONG, 3, "none")
    assert [i for i, s in enumerate(long) if s] == [35]
    assert long[35].stop == pytest.approx(200 - short[35].stop)
    assert find_setups(bars, Side.LONG, 3, "none")[35] is None  # wrong direction


def test_breakout_close_removes_level():
    bars = with_swing_high([(100.1, 102.4, 100.0, 102.3), (102.3, 102.5, 100.5, 100.8)])
    assert not any(find_setups(bars, Side.SHORT, 3, "none"))


def test_level_expires_after_max_age():
    rows = [(100.1, 100.5, 99.8, 100.1)] * (FIXED.level_max_age_bars - 3)
    bars = with_swing_high(rows + [SWEEP])
    assert not any(find_setups(bars, Side.SHORT, 3, "none"))


def test_structure_confirmation_signals_on_confirming_bar():
    bars = with_swing_high([SWEEP, (100.8, 100.9, 100.3, 100.4), (100.4, 100.5, 99.7, 99.8)])
    setups = find_setups(bars, Side.SHORT, 3, "structure")
    assert [i for i, s in enumerate(setups) if s] == [37]  # close 99.8 < sweep low 100.0
    assert setups[37].stop == pytest.approx(102.5 + 0.5 * atr(bars, 24)[37])


def test_structure_cancelled_when_price_trades_beyond_sweep_extreme():
    bars = with_swing_high([SWEEP, (100.8, 102.6, 99.5, 99.6)])
    assert not any(find_setups(bars, Side.SHORT, 3, "structure"))


def test_structure_expires_after_window():
    idle = [(100.8, 100.9, 100.3, 100.4)] * FIXED.confirmation_window_bars
    bars = with_swing_high([SWEEP, *idle, (100.4, 100.5, 99.7, 99.8)])
    assert not any(find_setups(bars, Side.SHORT, 3, "structure"))


def test_volatility_shock_gate_blocks_setup():
    bars = with_swing_high([(100.1, 102.5, 94.0, 95.0)])
    assert not any(find_setups(bars, Side.SHORT, 3, "none"))


def test_cost_gate_blocks_when_spread_too_wide_relative_to_stop():
    bars = with_swing_high([SWEEP, (100.8, 100.9, 100.5, 100.6), (100.6, 100.7, 100.4, 100.5)])
    setups = find_setups(bars, Side.SHORT, 3, "none")
    distance = abs(setups[35].signal_close - setups[35].stop)
    ok = sweep_signal(bars, setups, Side.SHORT, 2.0, ExecutionCosts(spread=0.24 * distance))
    blocked = sweep_signal(bars, setups, Side.SHORT, 2.0, ExecutionCosts(spread=0.26 * distance))
    order = ok(bars, 35)
    assert order is not None and order.side is Side.SHORT and order.target_r == 2.0
    assert order.max_hold_bars == FIXED.max_hold_bars
    assert blocked(bars, 35) is None


# --- causality ---------------------------------------------------------------


def walk(n=4000, seed=5):
    rng = random.Random(seed)
    price, rows = 100.0, []
    for i in range(n):
        o = price
        price *= math.exp(rng.gauss(0, 0.004))
        rows.append((o, max(o, price) * (1 + abs(rng.gauss(0, 0.002))), min(o, price) * (1 - abs(rng.gauss(0, 0.002))), price))
    return to_bars(rows)


@pytest.mark.parametrize("side", [Side.LONG, Side.SHORT])
@pytest.mark.parametrize("confirmation", ["none", "structure"])
def test_setups_are_causal(side, confirmation):
    bars = walk()
    full = find_setups(bars, side, 3, confirmation)
    assert sum(1 for s in full if s) > 10  # the test exercises real setups
    for cut in (300, 1700, 3500):
        assert find_setups(bars[:cut], side, 3, confirmation) == full[:cut]
