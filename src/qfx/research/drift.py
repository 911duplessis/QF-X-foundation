"""Drift Baseline v1: timing-shuffled control for bracket hypotheses.

Implements the frozen specification in ``docs/hypotheses/drift_baseline_v1.md``
(a test fails if this module drifts from it). The control tests an
already-defined hypothesis; it must never be used to choose its parameters.

    python -m qfx.research.drift --group sweep \
        --report docs/results/drift_baseline_v1.md --json docs/results/drift_baseline_v1.json
    python -m qfx.research.drift --group expansion \
        --report docs/results/drift_baseline_v1_vol_expansion.md \
        --json docs/results/drift_baseline_v1_vol_expansion.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

from ..backtest.bracket import BracketOrder, run_bracket_backtest
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts, Side, Trade
from . import expansion, sweep
from .baseline import COSTS
from .features import ewma_vol, log_returns
from .splits import Segment
from .walkforward import HYPOTHESIS_SPECS, WalkForwardConfig, rolling_windows, run_walkforward, to_jsonable

SPEC_PATH = "docs/hypotheses/drift_baseline_v1.md"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DriftConfig:
    repetitions: int = 500
    max_redraws: int = 20
    percentiles: tuple[float, ...] = (0.05, 0.5, 0.95)
    band: tuple[float, float] = (0.05, 0.95)
    timing_value_max_p: float = 0.05
    zero_trade_repetition_value: float = 0.0
    segments: tuple[str, ...] = ("train", "validation", "test")
    sampling: str = "hour_matched"
    track: str = "forced"


CONFIG = DriftConfig()

# Hypotheses the control applies to (the frozen specification's applies_to).
HYPOTHESIS_SIDES: dict[str, Side] = {**sweep.HYPOTHESES, **expansion.HYPOTHESES}


# --- gates and templates -----------------------------------------------------


@dataclass(frozen=True)
class Gates:
    """The hypothesis's own gates, evaluated at a (random) signal bar."""

    atr: Sequence[float]
    long_vol: Sequence[float]
    shock_vol: Sequence[float]
    costs: ExecutionCosts
    fixed: sweep.SweepFixed = sweep.FIXED

    @classmethod
    def for_bars(cls, bars: Sequence[Bar], costs: ExecutionCosts, fixed: sweep.SweepFixed = sweep.FIXED) -> "Gates":
        rets = log_returns([b.close for b in bars])
        return cls(sweep.atr(bars, fixed.atr_period), ewma_vol(rets, fixed.vol_long_halflife), ewma_vol(rets, fixed.vol_shock_halflife), costs, fixed)

    def ready(self, h: int) -> bool:
        a, lv, sv = self.atr[h], self.long_vol[h], self.shock_vol[h]
        return a == a and lv == lv and sv == sv and a > 0

    def passes(self, bars: Sequence[Bar], h: int, k: float) -> bool:
        if not self.ready(h) or self.shock_vol[h] > self.fixed.vol_shock_ratio * self.long_vol[h]:
            return False
        bar = bars[h]
        spread = max(bar.spread, self.costs.spread) if bar.spread is not None else self.costs.spread
        return spread <= self.fixed.max_spread_to_stop * k * self.atr[h]


@dataclass(frozen=True)
class Template:
    bar: int  # global index of the hypothesis's signal bar
    k: float  # stop distance in ATR units at that bar
    hour: int  # UTC hour of the signal bar


def extract_templates(bars: Sequence[Bar], seg: Segment, signal: Callable, atr: Sequence[float]) -> list[Template]:
    """The hypothesis's orders in the segment after all its gates."""
    out = []
    for i in range(seg.end - seg.start):
        order = signal(bars, i)
        if order is not None:
            g = seg.start + i
            out.append(Template(g, abs(bars[g].close - order.stop) / atr[g], bars[g].timestamp.hour))
    return out


def seed_for(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")


def hour_pools(bars: Sequence[Bar], seg: Segment, gates: Gates) -> dict[int, list[int]]:
    """Candidate bars per UTC hour; the last bar is excluded (no entry bar left)."""
    pools: dict[int, list[int]] = {}
    for h in range(seg.start, seg.end - 1):
        if gates.ready(h):
            pools.setdefault(bars[h].timestamp.hour, []).append(h)
    return pools


@dataclass
class ControlRun:
    net_bps: list[float]
    dropped: int
    entries: list[int] = field(default_factory=list)  # chosen random signal bars (global)


def control_repetition(
    bars: Sequence[Bar],
    seg: Segment,
    templates: Sequence[Template],
    side: Side,
    target_r: float,
    max_hold_bars: int,
    gates: Gates,
    pools: dict[int, list[int]],
    seed: int,
    max_redraws: int,
) -> ControlRun:
    rng = random.Random(seed)
    remaining = {h: list(v) for h, v in pools.items()}
    orders: dict[int, BracketOrder] = {}
    dropped = 0
    for t in templates:
        pool = remaining.get(t.hour, [])
        placed = False
        for _ in range(1 + max_redraws):
            if not pool:
                break
            j = rng.randrange(len(pool))
            pool[j], pool[-1] = pool[-1], pool[j]
            h = pool.pop()  # without replacement; rejected bars are not redrawn
            if gates.passes(bars, h, t.k):
                d = t.k * gates.atr[h]
                stop = bars[h].close - d if side is Side.LONG else bars[h].close + d
                orders[h - seg.start] = BracketOrder(side, stop, target_r, max_hold_bars)
                placed = True
                break
        dropped += not placed
    trades = run_bracket_backtest(bars[seg.start : seg.end], lambda v, i: orders.get(i), costs=gates.costs)
    return ControlRun([bps(t) for t in trades], dropped, sorted(o + seg.start for o in orders))


def bps(t: Trade) -> float:
    return t.net_pnl / t.entry_price * 1e4


# --- statistics ----------------------------------------------------------------


def empirical_p(observed: float, control: Sequence[float]) -> float:
    """One-sided: (1 + #{control >= observed}) / (N + 1)."""
    return (1 + sum(1 for c in control if c >= observed)) / (len(control) + 1)


def quantile(values: Sequence[float], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    pos = q * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _mean(xs: Sequence[float], cfg: DriftConfig) -> float:
    return mean(xs) if xs else cfg.zero_trade_repetition_value


@dataclass(frozen=True)
class Comparison:
    observed_mean: float
    observed_trades: int
    observed_total: float
    control_mean: float
    control_mean_trades: float
    difference: float  # primary effect size
    p_value: float  # primary: mean net bps/trade
    p_value_total: float  # secondary: total net bps
    control_percentiles: dict[str, float]
    observed_percentile: float  # share of control repetitions below observed
    zero_trade_repetitions: int
    mean_dropped_templates: float
    templates: int


def compare(observed: Sequence[float], control: Sequence[Sequence[float]], dropped: Sequence[int], templates: int, cfg: DriftConfig = CONFIG) -> Comparison:
    t_obs = _mean(observed, cfg)
    t_ctrl = [_mean(c, cfg) for c in control]
    totals = [sum(c) for c in control]
    return Comparison(
        observed_mean=t_obs,
        observed_trades=len(observed),
        observed_total=sum(observed),
        control_mean=mean(t_ctrl),
        control_mean_trades=mean(len(c) for c in control),
        difference=t_obs - mean(t_ctrl),
        p_value=empirical_p(t_obs, t_ctrl),
        p_value_total=empirical_p(sum(observed), totals),
        control_percentiles={f"p{round(q * 100)}": quantile(t_ctrl, q) for q in cfg.percentiles},
        observed_percentile=sum(1 for c in t_ctrl if c < t_obs) / len(t_ctrl),
        zero_trade_repetitions=sum(1 for c in control if not c),
        mean_dropped_templates=mean(dropped) if dropped else 0.0,
        templates=templates,
    )


# --- per hypothesis/symbol evaluation -------------------------------------------


@dataclass
class SegmentRun:
    observed: list[float]
    control: list[list[float]]
    dropped: list[int]
    templates: int


def run_segment(
    bars: Sequence[Bar], seg: Segment, signal: Callable, side: Side, target_r: float, gates: Gates, key: tuple, cfg: DriftConfig
) -> SegmentRun:
    part = bars[seg.start : seg.end]
    observed = [bps(t) for t in run_bracket_backtest(part, signal, costs=gates.costs)]
    templates = extract_templates(bars, seg, signal, gates.atr)
    pools = hour_pools(bars, seg, gates)
    runs = [
        control_repetition(bars, seg, templates, side, target_r, gates.fixed.max_hold_bars, gates, pools, seed_for(*key, r), cfg.max_redraws)
        for r in range(cfg.repetitions)
    ]
    return SegmentRun(observed, [r.net_bps for r in runs], [r.dropped for r in runs], len(templates))


def evaluate_symbol(
    hypothesis: str, symbol: str, bars: Sequence[Bar], costs: ExecutionCosts, wf: WalkForwardConfig = WalkForwardConfig(), cfg: DriftConfig = CONFIG
) -> dict:
    side = HYPOTHESIS_SIDES[hypothesis]
    spec = HYPOTHESIS_SPECS[hypothesis]()
    report = run_walkforward(symbol, bars, spec, costs, wf)
    windows = rolling_windows([b.timestamp for b in bars], wf)
    assert len(windows) == len(report.windows)
    gates = Gates.for_bars(bars, costs)
    make = spec.bind(bars)
    per_window, pooled_runs = [], {s: [] for s in cfg.segments}
    for w, res in zip(windows, report.windows):
        p = res.params  # forced-track parameters already selected in this window
        segs = {"train": w.train, "validation": w.validation, "test": w.test}
        out = {}
        for name in cfg.segments:
            seg = segs[name]
            signal = make(p, seg.start, costs)
            run = run_segment(bars, seg, signal, side, p["target_r"], gates, (hypothesis, symbol, w.index, name), cfg)
            out[name] = compare(run.observed, run.control, run.dropped, run.templates, cfg)
            pooled_runs[name].append(run)
        per_window.append({"index": w.index, "params": p, "periods": res.periods, "segments": out,
                           "walkforward_forced_test_net_bps": res.test.net_bps})
    pooled, distributions = {}, {}
    for name, runs in pooled_runs.items():
        observed = [x for r in runs for x in r.observed]
        control = [[x for r in runs for x in r.control[i]] for i in range(cfg.repetitions)]
        dropped = [sum(r.dropped[i] for r in runs) for i in range(cfg.repetitions)]
        pooled[name] = compare(observed, control, dropped, sum(r.templates for r in runs), cfg)
        distributions[name] = [_mean(c, cfg) for c in control]
    return {"pooled": pooled, "windows": per_window, "pooled_control_means": distributions}


# --- decisions (pre-registered) --------------------------------------------------


def q1_drift(train: Comparison, cfg: DriftConfig = CONFIG) -> str:
    lo, hi = cfg.band
    if train.observed_percentile > hi:
        return "above band: timing had in-sample value"
    if train.observed_percentile < lo:
        return "below band: timing worse than random in-sample"
    return "inside band: attributed to drift and geometry, not timing"


def q2_timing(test: Comparison, cfg: DriftConfig = CONFIG) -> str:
    if test.p_value <= cfg.timing_value_max_p:
        return "timing edge demonstrated (p <= 0.05; walk-forward rules still apply)"
    return "no demonstrated timing edge"


# --- output ---------------------------------------------------------------------


TITLES = {
    "sweep": "Liquidity Sweep Reversal v1",
    "expansion": "Volatility Expansion v1",
}
GROUPS = {"sweep": sorted(sweep.HYPOTHESES), "expansion": sorted(expansion.HYPOTHESES)}


def render(results: dict, cfg: DriftConfig = CONFIG, subject: str = TITLES["sweep"]) -> str:
    L = [
        f"# Drift Baseline v1: timing-shuffled control for {subject}",
        "",
        f"Specification (frozen before implementation): `{SPEC_PATH}`. One-sided empirical randomization test, "
        f"{cfg.repetitions} hour-matched repetitions per window and segment, forced-track parameters. "
        "Statistic: mean net bps/trade; effect = observed - control mean; p = (1 + #{control >= observed}) / (N + 1). "
        "Total net bps is the secondary statistic. Long and short are separate hypotheses.",
        "",
        "## Pre-registered answers",
        "",
        "| direction | symbol | Q1 train (drift?) | Q2 test (timing edge?) | Q3 drift line: control test mean bps |",
        "|---|---|---|---|---|",
    ]
    for hyp, by_sym in results.items():
        for sym, r in by_sym.items():
            L.append(f"| {hyp.split('_')[-1]} | {sym} | {q1_drift(r['pooled']['train'], cfg)} | {q2_timing(r['pooled']['test'], cfg)} | {r['pooled']['test'].control_mean:+.2f} |")
    L += ["", "## Pooled comparisons", "",
          "| direction | symbol | segment | observed mean | trades | control mean | ctrl trades | difference | p | p (total) | ctrl p5 / p50 / p95 | observed pctl | dropped |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for hyp, by_sym in results.items():
        for sym, r in by_sym.items():
            for seg, c in r["pooled"].items():
                pc = c.control_percentiles
                L.append(
                    f"| {hyp.split('_')[-1]} | {sym} | {seg} | {c.observed_mean:+.2f} | {c.observed_trades} | {c.control_mean:+.2f} | "
                    f"{c.control_mean_trades:.0f} | {c.difference:+.2f} | {c.p_value:.3f} | {c.p_value_total:.3f} | "
                    f"{pc['p5']:+.2f} / {pc['p50']:+.2f} / {pc['p95']:+.2f} | {c.observed_percentile:.0%} | {c.mean_dropped_templates:.1f}/{c.templates} |"
                )
    for hyp, by_sym in results.items():
        L += ["", f"## {hyp}: per window (test segment)", "",
              "| symbol | # | test period | params | observed mean | trades | control mean | difference | p | observed pctl |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for sym, r in by_sym.items():
            for w in r["windows"]:
                c = w["segments"]["test"]
                params = " ".join(f"{k}={v}" for k, v in w["params"].items())
                L.append(f"| {sym} | {w['index']} | {w['periods']['test']} | {params} | {c.observed_mean:+.2f} | {c.observed_trades} | "
                         f"{c.control_mean:+.2f} | {c.difference:+.2f} | {c.p_value:.3f} | {c.observed_percentile:.0%} |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="data/mt5")
    parser.add_argument("--report", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument("--group", default="sweep", choices=sorted(GROUPS))
    args = parser.parse_args(argv)
    loaded = [load_mt5(p, ZoneInfo(DEFAULT_SERVER_TZ)) for p in sorted(Path(args.data).glob("*.csv"))]
    results = {
        hyp: {l.symbol: evaluate_symbol(hyp, l.symbol, l.bars, COSTS[l.symbol]) for l in loaded if l.symbol in COSTS}
        for hyp in GROUPS[args.group]
    }
    text = render(results, subject=TITLES[args.group])
    print(text)
    payload = to_jsonable({"schema_version": SCHEMA_VERSION, "spec": SPEC_PATH, "config": CONFIG, "results": results})
    for target, content in ((args.report, text), (args.json, json.dumps(payload, indent=2) + "\n")):
        if target:
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
