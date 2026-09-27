import json
import math
import random
import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qfx.backtest.types import Bar, ExecutionCosts, Side
from qfx.research import sweep
from qfx.research.drift import Gates
from qfx.research.expansion import (
    FIXED,
    GRID_AXES,
    HYPOTHESES,
    SPEC_PATH,
    ExpansionFixed,
    box_series,
    compression_flags,
    expansion_signal,
    find_setups,
    grid,
)

ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)
SMALL = ExpansionFixed(compression_lookback_bars=10)


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
    assert "atr_period" not in spec["fixed"]  # the hypothesis uses no ATR
    assert ExecutionCosts().delay_bars == spec["fixed"]["delay_bars"]
    assert spec["walkforward"] == spec["costs"] == "unchanged from liquidity_sweep_reversal_v1"
    assert spec["drift_baseline"] == {"spec": "drift_baseline_v1", "applies": True, "max_p": 0.05, "control_atr_period": 24}


def test_drift_control_uses_this_hypothesis_gate_values_and_atr24():
    # The drift control's gates default to the sweep's values; they must equal this hypothesis's.
    for name in ("vol_long_halflife", "vol_shock_halflife", "vol_shock_ratio", "max_spread_to_stop", "max_hold_bars"):
        assert getattr(FIXED, name) == getattr(sweep.FIXED, name)
    assert sweep.FIXED.atr_period == frozen()["drift_baseline"]["control_atr_period"]
    assert Gates.for_bars.__defaults__[0] is sweep.FIXED


# --- compression rank ----------------------------------------------------------


def to_bars(rows):
    return [Bar(T0 + timedelta(hours=i), o, h, l, c) for i, (o, h, l, c) in enumerate(rows)]


def brute_flags(bars, n, fixed):
    highs, lows = box_series(bars, n)
    width = [h - l for h, l in zip(highs, lows)]
    L, out = fixed.compression_lookback_bars, []
    for j in range(len(bars)):
        refs = [width[e] for e in range(j - 1 - L, j - 1)] if j - 1 - L >= n - 1 else None
        out.append(bool(refs) and sum(1 for r in refs if r < width[j - 1]) / L <= fixed.compression_percentile)
    return out


def walk(n=4000, seed=9):
    rng = random.Random(seed)
    price, rows = 100.0, []
    for _ in range(n):
        o = price
        price *= math.exp(rng.gauss(0, 0.003))
        rows.append((o, max(o, price) * (1 + abs(rng.gauss(0, 0.002))), min(o, price) * (1 - abs(rng.gauss(0, 0.002))), price))
    return to_bars(rows)


@pytest.mark.parametrize("n", [3, 12])
def test_sliding_rank_equals_brute_force(n):
    bars = walk(1500)
    fixed = ExpansionFixed(compression_lookback_bars=50)
    assert compression_flags(bars, n, fixed) == brute_flags(bars, n, fixed)


def test_incomplete_reference_history_never_signals():
    bars = walk(3 - 1 + 10)  # one bar short of the first complete reference set
    assert not any(compression_flags(bars, 3, SMALL))


def test_ties_count_as_compressed_under_strict_rank_rule():
    bars = to_bars([(100, 101, 99, 100)] * 40)  # every box has the same width
    flags = compression_flags(bars, 3, SMALL)
    assert all(flags[3 - 1 + 10 + 1 :])  # count(ref < W) = 0 -> rank 0 <= 0.2


# --- hand-built breakout scenarios -------------------------------------------------


def wide(k=21):
    """Alternating closes with ~2.0 wide ranges; ends on close 100."""
    rows = []
    for i in range(k):
        c = 100.0 + 0.2 * (i % 2)
        o = 100.0 + 0.2 * ((i + 1) % 2)
        rows.append((o, max(o, c) + 0.9, min(o, c) - 0.9, c))
    return rows


NARROW = [(100.0, 100.1, 99.9, 100.0)] * 3  # box: high 100.1, low 99.9


def mirror(bars):
    return [Bar(b.timestamp, 200 - b.open, 200 - b.low, 200 - b.high, 200 - b.close) for b in bars]


def test_upside_breakout_from_compression_gives_long_setup():
    bars = to_bars(wide() + NARROW + [(100.0, 100.4, 99.95, 100.3)])
    j = len(bars) - 1
    opp = find_setups(bars, Side.LONG, 3, "box_opposite", SMALL)
    mid = find_setups(bars, Side.LONG, 3, "box_mid", SMALL)
    assert [i for i, s in enumerate(opp) if s] == [j]
    assert opp[j].stop == pytest.approx(99.9) and mid[j].stop == pytest.approx(100.0)
    assert opp[j].signal_close == 100.3
    assert not any(find_setups(bars, Side.SHORT, 3, "box_opposite", SMALL))


def test_signal_bar_is_excluded_from_box():
    bars = to_bars(wide() + NARROW + [(100.0, 101.5, 98.5, 100.3)])  # huge own range
    s = find_setups(bars, Side.LONG, 3, "box_opposite", SMALL)[-1]
    assert s is not None and s.stop == pytest.approx(99.9)


def test_downside_breakout_is_exact_mirror():
    bars = to_bars(wide() + NARROW + [(100.0, 100.4, 99.95, 100.3)])
    long = find_setups(bars, Side.LONG, 3, "box_opposite", SMALL)
    short = find_setups(mirror(bars), Side.SHORT, 3, "box_opposite", SMALL)
    assert [i for i, s in enumerate(short) if s] == [len(bars) - 1]
    assert short[-1].stop == pytest.approx(200 - long[-1].stop)


def test_close_inside_box_is_not_a_breakout():
    bars = to_bars(wide() + NARROW + [(100.0, 100.4, 99.95, 100.05)])  # trades above, closes inside
    assert not any(find_setups(bars, Side.LONG, 3, "box_opposite", SMALL))


def test_wide_box_after_narrow_history_is_not_compressed():
    narrow_hist = [(100.0, 100.1, 99.9, 100.0 + 0.02 * (i % 2)) for i in range(21)]
    wide_box = [(100.0, 101.0, 99.0, 100.0)] * 3
    bars = to_bars(narrow_hist + wide_box + [(100.0, 101.6, 99.9, 101.5)])
    assert not compression_flags(bars, 3, SMALL)[-1]
    assert not any(find_setups(bars, Side.LONG, 3, "box_opposite", SMALL))


def test_volatility_shock_gate_blocks_breakout():
    bars = to_bars(wide() + NARROW + [(100.0, 106.0, 99.95, 105.0)])
    assert not any(find_setups(bars, Side.LONG, 3, "box_opposite", SMALL))


def test_cost_gate_uses_frozen_ratio():
    bars = to_bars(wide() + NARROW + [(100.0, 100.4, 99.95, 100.3), (100.3, 100.4, 100.2, 100.3)])
    setups = find_setups(bars, Side.LONG, 3, "box_opposite", SMALL)
    j = len(bars) - 2
    distance = abs(setups[j].signal_close - setups[j].stop)  # 0.4
    ok = expansion_signal(bars, setups, Side.LONG, 2.0, ExecutionCosts(spread=0.24 * distance))(bars, j)
    blocked = expansion_signal(bars, setups, Side.LONG, 2.0, ExecutionCosts(spread=0.26 * distance))(bars, j)
    assert ok is not None and ok.max_hold_bars == FIXED.max_hold_bars and ok.target_r == 2.0
    assert blocked is None


# --- causality ---------------------------------------------------------------


@pytest.mark.parametrize("side", [Side.LONG, Side.SHORT])
@pytest.mark.parametrize("stop", ["box_opposite", "box_mid"])
def test_setups_are_causal(side, stop):
    bars = walk()
    full = find_setups(bars, side, 12, stop)
    assert sum(1 for s in full if s) > 10
    for cut in (600, 2100, 3700):
        assert find_setups(bars[:cut], side, 12, stop) == full[:cut]
