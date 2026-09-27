import json
import math
import random
import re
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qfx.backtest.bracket import BracketOrder
from qfx.backtest.types import Bar, ExecutionCosts, Side
from qfx.research import sweep
from qfx.research.drift import (
    CONFIG,
    SPEC_PATH,
    DriftConfig,
    Gates,
    Template,
    compare,
    control_repetition,
    empirical_p,
    evaluate_symbol,
    extract_templates,
    hour_pools,
    q1_drift,
    q2_timing,
    quantile,
    run_segment,
    seed_for,
)
from qfx.research.splits import Segment
from qfx.research.walkforward import WalkForwardConfig

ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2025, 1, 6, tzinfo=timezone.utc)


def test_code_matches_frozen_spec():
    text = (ROOT / SPEC_PATH).read_text(encoding="utf-8")
    assert "Status: **FROZEN**" in text
    spec = json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))
    assert spec["version"] == 1
    # Extended 2026-09-27 (approved): volatility expansion added, method unchanged.
    assert set(sweep.HYPOTHESES) <= set(spec["applies_to"])
    assert sorted(spec["applies_to"]) == sorted([*sweep.HYPOTHESES, "vol_expansion_long", "vol_expansion_short"])
    assert spec["track"] == CONFIG.track and spec["sampling"] == CONFIG.sampling
    assert spec["segments"] == list(CONFIG.segments)
    assert spec["repetitions"] == CONFIG.repetitions == 500
    assert spec["max_redraws"] == CONFIG.max_redraws
    assert spec["percentiles"] == list(CONFIG.percentiles)
    assert spec["band"] == list(CONFIG.band)
    assert spec["timing_value_max_p"] == CONFIG.timing_value_max_p
    assert spec["zero_trade_repetition_value"] == CONFIG.zero_trade_repetition_value
    assert spec["statistic"] == "mean_net_bps_per_trade" and spec["test"] == "one_sided_empirical_randomization"
    assert spec["directions_separate"] is True


# --- statistics ----------------------------------------------------------------


def test_empirical_p_formula():
    control = [0.0, 1.0, 2.0, 3.0]
    assert empirical_p(10.0, control) == pytest.approx(1 / 5)  # beats all: minimum p
    assert empirical_p(-10.0, control) == pytest.approx(1.0)  # beaten by all
    assert empirical_p(2.0, control) == pytest.approx(3 / 5)  # ties count against the hypothesis


def test_quantile_and_compare():
    assert quantile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5) == 3.0
    c = compare([4.0, 6.0], [[1.0], [2.0, 2.0], []], [0, 1, 2], templates=3)
    assert c.observed_mean == 5.0 and c.observed_total == 10.0
    assert c.control_mean == pytest.approx((1 + 2 + 0) / 3)  # zero-trade repetition counts as 0
    assert c.difference == pytest.approx(5.0 - 1.0)
    assert c.zero_trade_repetitions == 1 and c.observed_percentile == 1.0
    assert c.p_value == pytest.approx(1 / 4) and c.mean_dropped_templates == 1.0


def test_decision_labels():
    base = compare([1.0], [[0.0]] * 19, [0] * 19, 1)
    assert q2_timing(base).startswith("timing edge demonstrated")  # p = 1/20
    assert "inside band" in q1_drift(compare([0.0], [[x / 10] for x in range(-5, 6)], [0] * 11, 1))
    assert q2_timing(compare([0.0], [[1.0]] * 19, [0] * 19, 1)) == "no demonstrated timing edge"


# --- synthetic market with a plantable edge -------------------------------------


def market(n=1500, seed=11, jumps=25):
    """Random walk with +2% jumps at random bars (no time-of-day pattern)."""
    rng = random.Random(seed)
    jump_bars = set(rng.sample(range(50, n - 5), jumps))
    price, rows = 100.0, []
    for i in range(n):
        o = price
        price *= math.exp(rng.gauss(0, 0.001) + (0.02 if i in jump_bars else 0.0))
        rows.append(Bar(T0 + timedelta(hours=i), o, max(o, price) * 1.0003, min(o, price) * 0.9997, price))
    return rows, jump_bars


def oracle(bars, gates, seg, jump_bars):
    """Knows the future: signals two bars before each jump bar."""

    def signal(view, i):
        g = seg.start + i
        if g + 2 in jump_bars and gates.ready(g):
            return BracketOrder(Side.LONG, bars[g].close - gates.atr[g], 1.0, 48)
        return None

    return signal


def test_hour_matching_absorbs_a_pure_time_of_day_effect():
    """Jumps only at one UTC hour: an 'edge' that is purely time-of-day must
    not look like timing skill against the hour-matched control."""
    rng = random.Random(4)
    n, price, rows = 2400, 100.0, []
    jump_bars = {i for i in range(50, n - 5) if i % 24 == 14}
    for i in range(n):
        o = price
        price *= math.exp(rng.gauss(0, 0.001) + (0.004 if i in jump_bars else 0.0))
        rows.append(Bar(T0 + timedelta(hours=i), o, max(o, price) * 1.0003, min(o, price) * 0.9997, price))
    gates = Gates.for_bars(rows, ExecutionCosts(spread=0.001))
    seg = Segment("test", 0, len(rows))
    run = run_segment(rows, seg, oracle(rows, gates, seg, jump_bars), Side.LONG, 1.0, gates, ("tod",), DriftConfig(repetitions=50))
    c = compare(run.observed, run.control, run.dropped, run.templates, DriftConfig(repetitions=50))
    assert c.observed_mean > 0 and c.control_mean > 0  # both capture the hour effect
    assert c.p_value > 0.05  # so it is not credited as timing skill


def test_planted_oracle_edge_reaches_minimum_p():
    bars, jumps = market()
    gates = Gates.for_bars(bars, ExecutionCosts(spread=0.001))
    seg = Segment("test", 0, len(bars))
    cfg = DriftConfig(repetitions=50)
    run = run_segment(bars, seg, oracle(bars, gates, seg, jumps), Side.LONG, 1.0, gates, ("oracle",), cfg)
    c = compare(run.observed, run.control, run.dropped, run.templates, cfg)
    assert run.templates >= 20 and c.observed_trades >= 20
    assert c.p_value == pytest.approx(1 / 51) and c.observed_percentile == 1.0
    assert c.difference > 0


def test_control_is_hour_matched_unique_and_gated():
    bars, jumps = market()
    gates = Gates.for_bars(bars, ExecutionCosts(spread=0.001))
    seg = Segment("test", 0, len(bars))
    templates = extract_templates(bars, seg, oracle(bars, gates, seg, jumps), gates.atr)
    run = control_repetition(bars, seg, templates, Side.LONG, 1.0, 48, gates, hour_pools(bars, seg, gates), seed_for("x", 1), 20)
    assert run.dropped == 0
    assert Counter(bars[h].timestamp.hour for h in run.entries) == Counter(t.hour for t in templates)
    assert len(set(run.entries)) == len(run.entries)
    assert all(gates.passes(bars, h, 1.0) for h in run.entries)


def test_control_is_deterministic_and_seed_sensitive():
    bars, jumps = market()
    gates = Gates.for_bars(bars, ExecutionCosts(spread=0.001))
    seg = Segment("test", 0, len(bars))
    templates = extract_templates(bars, seg, oracle(bars, gates, seg, jumps), gates.atr)
    pools = hour_pools(bars, seg, gates)
    a = control_repetition(bars, seg, templates, Side.LONG, 1.0, 48, gates, pools, seed_for("k", 1), 20)
    b = control_repetition(bars, seg, templates, Side.LONG, 1.0, 48, gates, pools, seed_for("k", 1), 20)
    c = control_repetition(bars, seg, templates, Side.LONG, 1.0, 48, gates, pools, seed_for("k", 2), 20)
    assert a.entries == b.entries and a.net_bps == b.net_bps
    assert a.entries != c.entries
    assert pools == hour_pools(bars, seg, gates)  # pools are not mutated


def test_templates_dropped_when_gates_reject_every_draw():
    bars, _ = market()
    gates = Gates.for_bars(bars, ExecutionCosts(spread=0.001))
    seg = Segment("test", 0, len(bars))
    templates = [Template(100, 1.0, bars[100].timestamp.hour)] * 3
    strict = Gates(gates.atr, gates.long_vol, gates.shock_vol, ExecutionCosts(spread=1e6))
    run = control_repetition(bars, seg, templates, Side.LONG, 1.0, 48, strict, hour_pools(bars, seg, strict), 1, 20)
    assert run.dropped == 3 and run.net_bps == [] and run.entries == []


def test_observed_matches_walkforward_forced_track():
    rng = random.Random(3)
    price, bars = 100.0, []
    for i in range(24 * 365):
        o = price
        price *= math.exp(rng.gauss(0, 0.003))
        bars.append(Bar(T0 + timedelta(hours=i), o, max(o, price) * (1 + abs(rng.gauss(0, 0.002))), min(o, price) * (1 - abs(rng.gauss(0, 0.002))), price))
    wf = WalkForwardConfig(train_months=4, validation_months=1, test_months=1, step_months=1, min_train_trades=5, min_validation_trades=1)
    out = evaluate_symbol("sweep_reversal_long", "T", bars, ExecutionCosts(spread=0.01), wf, DriftConfig(repetitions=3))
    assert out["windows"]
    for w in out["windows"]:
        assert w["segments"]["test"].observed_mean == pytest.approx(w["walkforward_forced_test_net_bps"])
    assert len(out["pooled_control_means"]["test"]) == 3
    assert set(out["pooled"]) == {"train", "validation", "test"}
