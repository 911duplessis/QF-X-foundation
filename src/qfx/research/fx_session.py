"""FX Session Directional Persistence v1, per the frozen specification
``docs/hypotheses/fx_session_persistence_v1.md`` (a test fails if the
constants here drift from its JSON block).

    python -m qfx.research.fx_session --archive <path to archive.zip> \
        --report docs/results/fx_session_persistence_v1.md \
        --json docs/results/fx_session_persistence_v1.json

One symmetric hypothesis on seven USD majors: an early London-session
displacement of at least theta x ATR(24) x sqrt(K) is followed by same-session
continuation. Parameters are selected jointly across the pairs in each
walk-forward window. Primary outcome: every walk-forward rule on the pooled
deployed track with the day-clustered t >= 2, AND block drift p <= 0.05
(forced track, test segments). Long/short and per-pair results are
descriptive only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import zipfile
from bisect import bisect_left
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta, timezone
from itertools import product
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

from ..backtest.bracket import BracketOrder, run_bracket_backtest
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts, Side, Trade
from .drift import CONFIG as DRIFT_CONFIG
from .drift import bps, compare, seed_for
from .replication import ClusteredT, _merge, clustered_t
from .splits import Segment
from .sweep import atr
from .walkforward import (
    HypothesisSpec,
    SegmentRun,
    Stability,
    WalkForwardConfig,
    Window,
    WindowResult,
    _bracket_engine,
    qualify,
    rolling_windows,
    run_segment,
    stability,
    stress,
    to_jsonable,
)

SPEC_PATH = "docs/hypotheses/fx_session_persistence_v1.md"
SCHEMA_VERSION = 1
NAME = "fx_session_persistence_v1"
UNIVERSE = ("EURUSD.m", "GBPUSD.m", "USDJPY.m", "USDCHF.m", "AUDUSD.m", "USDCAD.m", "NZDUSD.m")
ARCHIVE_SHA256 = "507058426d86f359097f438a7837b3ff55e115954d9569b441623b51cf10d3ab"
DATA_DIR = "data/mt5/fx_session_v1"
ORIGIN = datetime(2021, 1, 4, tzinfo=timezone.utc)
LONDON = ZoneInfo("Europe/London")
SESSION_OPEN = time(8, 0)
TIME_EXIT = time(16, 0)
GRID = tuple({"window_hours": k, "theta": th} for k, th in product((1, 2), (0.5, 1.0)))
ATR_PERIOD = 24
MIN_HISTORY_BARS = 25
STOP_ATR = 2.0
SPREAD_FLOORS = {
    "EURUSD.m": 0.00012, "GBPUSD.m": 0.00009, "USDJPY.m": 0.025, "USDCHF.m": 0.00013,
    "AUDUSD.m": 0.00009, "USDCAD.m": 0.00022, "NZDUSD.m": 0.00014,
}
SLIPPAGE_RATIO = 1 / 6
COMMISSION = 0.0
MIN_CLUSTERED_T = 2.0
DRIFT_MAX_P = 0.05
MDE_MULTIPLIER = 2.0 + 0.8416  # t >= 2 at 80% power, as in the power analysis


def costs_for(symbol: str) -> ExecutionCosts:
    floor = SPREAD_FLOORS[symbol]
    return ExecutionCosts(spread=floor, slippage=floor * SLIPPAGE_RATIO, commission=COMMISSION)


# --- session timeline -----------------------------------------------------------------


def london_utc(d: date, t: time) -> datetime:
    """A London wall-clock time on date ``d`` in UTC (DST-aware)."""
    return datetime.combine(d, t, LONDON).astimezone(timezone.utc)


@dataclass(frozen=True)
class DayPlan:
    """Bar indices for one pair, session day and window length, by
    availability only (no prices are looked at)."""

    day: date
    first: int  # first window bar (opens 08:00 London)
    signal: int  # last window bar; the signal is evaluated at its close
    entry: int  # opens 08:00 + K h London
    exit: int  # first bar opening >= 16:00 London (len(bars) if none)
    late_exit: bool  # the exit bar is not the 16:00 bar itself


@dataclass
class Pair:
    symbol: str
    bars: list[Bar]
    costs: ExecutionCosts
    timestamps: list[datetime] = field(init=False)
    index: dict[datetime, int] = field(init=False)
    atr: list[float] = field(init=False)
    _plans: dict = field(init=False, default_factory=dict)
    _setups: dict = field(init=False, default_factory=dict)
    _days: list = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.timestamps = [b.timestamp for b in self.bars]
        self.index = {ts: i for i, ts in enumerate(self.timestamps)}
        self.atr = atr(self.bars, ATR_PERIOD)

    def plan(self, day: date, k: int) -> DayPlan | None:
        key = (day, k)
        if key not in self._plans:
            self._plans[key] = self._make_plan(day, k)
        return self._plans[key]

    def _make_plan(self, day: date, k: int) -> DayPlan | None:
        if day.weekday() >= 5:
            return None
        t0 = london_utc(day, SESSION_OPEN)
        first = self.index.get(t0)
        if first is None or first < MIN_HISTORY_BARS:
            return None
        for j in range(1, k + 1):  # the rest of the window and the entry bar, exactly hourly
            if self.index.get(t0 + timedelta(hours=j)) != first + j:
                return None
        t_exit = london_utc(day, TIME_EXIT)
        exit_ = bisect_left(self.timestamps, t_exit)
        late = exit_ >= len(self.bars) or self.timestamps[exit_] != t_exit
        return DayPlan(day, first, first + k - 1, first + k, exit_, late)

    def scale_atr(self, p: DayPlan) -> float:
        """ATR(24) of the 24 bars before the window: never a window bar."""
        return self.atr[p.first - 1]

    def order(self, p: DayPlan, side: Side) -> BracketOrder:
        ref = self.bars[p.signal].close
        d = STOP_ATR * self.scale_atr(p)
        stop = ref - d if side is Side.LONG else ref + d
        return BracketOrder(side, stop, math.inf, max(1, p.exit - p.entry))

    def days(self) -> list[date]:
        if not self._days:
            self._days = sorted({ts.astimezone(LONDON).date() for ts in self.timestamps})
        return self._days


@dataclass(frozen=True)
class Setup:
    plan: DayPlan
    side: Side
    displacement: float
    threshold: float


def find_setups(pair: Pair, k: int, theta: float) -> dict[int, Setup]:
    """Signal-bar index -> setup. One per pair and session day at most."""
    if (k, theta) in pair._setups:
        return pair._setups[(k, theta)]
    out = pair._setups[(k, theta)] = {}
    for day in pair.days():
        p = pair.plan(day, k)
        if p is None:
            continue
        a = pair.scale_atr(p)
        if not a == a or a <= 0:
            continue
        d = pair.bars[p.signal].close - pair.bars[p.first].open
        threshold = theta * a * math.sqrt(k)
        if d != 0 and abs(d) >= threshold:
            out[p.signal] = Setup(p, Side.LONG if d > 0 else Side.SHORT, d, threshold)
    return out


def session_spec(pair: Pair) -> HypothesisSpec:
    def bind(bars: Sequence[Bar]):
        assert bars is pair.bars
        cache: dict[tuple, dict[int, Setup]] = {}

        def make(p: dict, offset: int, costs: ExecutionCosts):
            key = (p["window_hours"], p["theta"])
            if key not in cache:
                cache[key] = find_setups(pair, *key)
            setups = cache[key]

            def signal(view, i):
                s = setups.get(offset + i)
                return None if s is None else pair.order(s.plan, s.side)

            return signal

        return make

    return HypothesisSpec(NAME, GRID, bind, _bracket_engine, SPEC_PATH)


# --- joint walk-forward ----------------------------------------------------------------------


@dataclass
class PairContext:
    pair: Pair
    spec: HypothesisSpec
    make: object
    stressed: tuple
    windows: list[Window]


def build_contexts(pairs: Sequence[Pair], cfg: WalkForwardConfig) -> list[PairContext]:
    out = []
    for p in pairs:
        spec = session_spec(p)
        out.append(PairContext(p, spec, spec.bind(p.bars), stress(p.bars, p.costs, cfg.stress_multiplier),
                               rolling_windows(p.timestamps, cfg, ORIGIN)))
    n = len(out[0].windows)
    assert all(len(c.windows) == n for c in out), "pairs must share the window grid"
    return out


def _seg(w: Window, name: str) -> Segment:
    return {"train": w.train, "validation": w.validation, "test": w.test}[name]


def _period(c: PairContext, seg: Segment) -> str:
    return f"{c.pair.timestamps[seg.start]:%Y-%m-%d} to {c.pair.timestamps[seg.end - 1]:%Y-%m-%d}"


def _run(c: PairContext, k: int, name: str, params: dict, stressed: bool = False) -> SegmentRun:
    seg = _seg(c.windows[k], name)
    if stressed:
        bars, costs = c.stressed
        return run_segment(bars, seg, c.spec, c.make, params, costs)
    return run_segment(c.pair.bars, seg, c.spec, c.make, params, c.pair.costs)


@dataclass
class JointWindow:
    result: WindowResult
    per_pair: dict[str, dict[str, SegmentRun]]  # symbol -> {"test", "stressed"}


def evaluate_joint_window(ctxs: Sequence[PairContext], k: int, cfg: WalkForwardConfig) -> JointWindow:
    periods = {name: _period(ctxs[0], _seg(ctxs[0].windows[k], name)) for name in ("train", "validation", "test")}
    for c in ctxs:
        assert {n: _period(c, _seg(c.windows[k], n)) for n in periods} == periods, "windows must cover identical periods"

    def pooled(name: str, params: dict) -> SegmentRun:
        return _merge([_run(c, k, name, params) for c in ctxs])

    train = [(p, pooled("train", p)) for p in GRID]
    eligible = [(p, r) for p, r in train if r.stats.trades >= cfg.min_train_trades and r.stats.net_bps > 0]
    reason = ""
    if eligible:
        vals = [(p, tr, pooled("validation", p)) for p, tr in eligible]
        enough = [x for x in vals if x[2].stats.trades >= cfg.min_validation_trades]
        params, train_run, val_run = max(enough or vals, key=lambda x: x[2].stats.net_bps)
        if not enough:
            reason = f"validation trades < {cfg.min_validation_trades}"
        elif val_run.stats.net_bps <= 0:
            reason = "validation net <= 0"
    else:
        params, train_run = max(train, key=lambda x: x[1].stats.net_bps)
        val_run = pooled("validation", params)
        reason = "no candidate passed train screen"
    per_pair = {c.pair.symbol: {"test": _run(c, k, "test", params), "stressed": _run(c, k, "test", params, stressed=True)} for c in ctxs}
    test = _merge([v["test"] for v in per_pair.values()])
    stressed_run = _merge([v["stressed"] for v in per_pair.values()])
    result = WindowResult(
        index=k, periods=periods, eligible=len(eligible), params=params, deployed=not reason, abstain_reason=reason,
        train=train_run.stats, validation=val_run.stats, test=test.stats, test_stressed=stressed_run.stats, breakdown={},
        _runs={"validation": val_run, "test": test, "stressed": stressed_run},
    )
    return JointWindow(result, per_pair)


def qualify_fx(dep: Stability, ct: ClusteredT, drift_p: float, cfg: WalkForwardConfig) -> tuple[bool, list[str]]:
    """All existing walk-forward rules with the IID pooled t replaced by the
    day-clustered t, plus the block drift test."""
    _, fails = qualify(dep, replace(cfg, min_test_t=-math.inf))
    if ct.clustered_t < MIN_CLUSTERED_T:
        fails.append(f"day-clustered t {ct.clustered_t:+.2f} < {MIN_CLUSTERED_T}")
    if drift_p > DRIFT_MAX_P:
        fails.append(f"block drift p {drift_p:.3f} > {DRIFT_MAX_P}")
    return not fails, fails


# --- block drift control ------------------------------------------------------------------------


def replay_trade(pair: Pair, plan: DayPlan, side: Side, seg: Segment) -> Trade | None:
    """One trade on its own bar slice. Identical to the full-segment run
    because trades never overlap (every trade ends by the next signal)."""
    if not (seg.start <= plan.signal and plan.entry < seg.end):
        return None
    end = min(plan.exit + 1, seg.end)
    order = pair.order(plan, side)
    trades = run_bracket_backtest(pair.bars[plan.signal : end], lambda v, i: order if i == 0 else None, costs=pair.costs)
    return trades[0] if trades else None


class ReplayCache:
    def __init__(self) -> None:
        self._c: dict = {}

    def get(self, pair: Pair, plan: DayPlan, side: Side, seg: Segment) -> float | None:
        key = (pair.symbol, plan.day, plan.signal - plan.first, side, seg.start, seg.end)
        if key not in self._c:
            t = replay_trade(pair, plan, side, seg)
            self._c[key] = None if t is None else bps(t)
        return self._c[key]


def block_drift_segment(
    ctxs: Sequence[PairContext], params: dict, k: int, name: str, repetitions: int, max_redraws: int, cache: ReplayCache
) -> tuple[list[float], list[list[float]], list[int], int]:
    kh, theta = params["window_hours"], params["theta"]
    observed: list[float] = []
    groups: dict[date, list[tuple[int, Side]]] = defaultdict(list)
    segs = [_seg(c.windows[k], name) for c in ctxs]
    for c_i, (c, seg) in enumerate(zip(ctxs, segs)):
        for s in sorted(find_setups(c.pair, kh, theta).values(), key=lambda s: s.plan.signal):
            v = cache.get(c.pair, s.plan, s.side, seg)
            if v is not None:
                observed.append(v)
                groups[s.plan.day].append((c_i, s.side))
    lo = min(c.pair.timestamps[s.start] for c, s in zip(ctxs, segs))
    hi = max(c.pair.timestamps[s.end - 1] for c, s in zip(ctxs, segs))
    days = sorted({d for c in ctxs for d in c.pair.days() if d.weekday() < 5 and lo <= london_utc(d, SESSION_OPEN) <= hi})
    ordered = sorted(groups.items())
    control, dropped = [], []
    for r in range(repetitions):
        rng = random.Random(seed_for(NAME, "block", k, name, r))
        pool = list(days)
        rep: list[float] = []
        n_dropped = 0
        for _, members in ordered:
            placed = False
            for _ in range(1 + max_redraws):
                if not pool:
                    break
                j = rng.randrange(len(pool))
                pool[j], pool[-1] = pool[-1], pool[j]
                cand = pool.pop()
                vals = []
                for c_i, side in members:
                    plan = ctxs[c_i].pair.plan(cand, kh)
                    v = None if plan is None else cache.get(ctxs[c_i].pair, plan, side, segs[c_i])
                    if v is None:
                        break
                    vals.append(v)
                else:
                    rep += vals
                    placed = True
                    break
            n_dropped += not placed
        control.append(rep)
        dropped.append(n_dropped)
    return observed, control, dropped, len(ordered)


def block_drift(ctxs: Sequence[PairContext], windows: Sequence[JointWindow], repetitions: int, max_redraws: int) -> dict:
    cache, out = ReplayCache(), {}
    for name in DRIFT_CONFIG.segments:
        observed, control, dropped, groups, per_window = [], [[] for _ in range(repetitions)], [0] * repetitions, 0, []
        for jw in windows:
            k = jw.result.index
            obs, ctrl, drp, g = block_drift_segment(ctxs, jw.result.params, k, name, repetitions, max_redraws, cache)
            observed += obs
            for i in range(repetitions):
                control[i] += ctrl[i]
                dropped[i] += drp[i]
            groups += g
            per_window.append({"index": k, "comparison": compare(obs, ctrl, drp, g)})
        out[name] = {"pooled": compare(observed, control, dropped, groups), "windows": per_window}
    return out


# --- descriptives ------------------------------------------------------------------------------------


def summary(trades: Sequence[Trade], windows: int) -> dict:
    ct = clustered_t(trades, windows)
    se = ct.mean_bps / ct.clustered_t if ct.clustered_t else math.nan
    return {"trades": ct.trades, "unique_days": ct.unique_days, "mean_bps": ct.mean_bps, "raw_t": ct.raw_t,
            "clustered_t": ct.clustered_t, "achieved_mde_bps": MDE_MULTIPLIER * abs(se) if se == se else None}


def descriptives(ctxs: Sequence[PairContext], windows: Sequence[JointWindow], deployed_only: bool) -> dict:
    active = [w for w in windows if w.result.deployed or not deployed_only]
    by_pair = {c.pair.symbol: [t for w in active for t in w.per_pair[c.pair.symbol]["test"].trades] for c in ctxs}
    trades = [t for ts in by_pair.values() for t in ts]
    n = len(active)
    late = sum(1 for t in trades if t.exit_reason == "time"
               and t.exit_time != london_utc(t.entry_time.astimezone(LONDON).date(), TIME_EXIT))
    days = Counter(t.entry_time.date() for t in trades)
    return {
        "sides": {s.value: summary([t for t in trades if t.side is s], n) for s in Side},
        "pairs": {sym: summary(ts, n) for sym, ts in by_pair.items()},
        "exit_reasons": dict(Counter(t.exit_reason for t in trades)),
        "late_time_exits": late,
        "signal_days": len(days),
        "mean_signals_per_signal_day": mean(days.values()) if days else 0.0,
    }


# --- data ------------------------------------------------------------------------------------------------


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_archive(archive: str | Path, out_dir: str | Path = DATA_DIR, expected: str = ARCHIVE_SHA256) -> list[Path]:
    """Refuses any archive that is not byte-identical to the frozen one."""
    digest = sha256_file(archive)
    if digest != expected:
        raise ValueError(f"archive sha256 {digest} != frozen {expected}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    with zipfile.ZipFile(archive) as z:
        for sym in UNIVERSE:
            (entry,) = [n for n in z.namelist() if n.startswith(f"{sym}_H1_") and n.endswith(".csv")]
            target = out / Path(entry).name
            target.write_bytes(z.read(entry))
            written.append(target)
    return written


def load_pairs(data_dir: str = DATA_DIR) -> list[Pair]:
    data = {}
    for sym in UNIVERSE:
        path = sorted(Path(data_dir).glob(f"{sym}_H1_*.csv"))[0]
        bars = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ)).bars
        data[sym] = [b for b in bars if b.timestamp >= ORIGIN]
    end = min(b[-1].timestamp for b in data.values())
    return [Pair(s, [b for b in bars if b.timestamp <= end], costs_for(s)) for s, bars in data.items()]


# --- run ----------------------------------------------------------------------------------------------------


def run(pairs: Sequence[Pair], repetitions: int = DRIFT_CONFIG.repetitions, cfg: WalkForwardConfig = WalkForwardConfig()) -> dict:
    ctxs = build_contexts(pairs, cfg)
    windows = [evaluate_joint_window(ctxs, k, cfg) for k in range(len(ctxs[0].windows))]
    results = [w.result for w in windows]
    dep, forced = stability(results, True), stability(results, False)
    dep_trades = [t for r in results if r.deployed for t in r._runs["test"].trades]
    forced_trades = [t for r in results for t in r._runs["test"].trades]
    ct_dep = clustered_t(dep_trades, sum(1 for r in results if r.deployed))
    ct_forced = clustered_t(forced_trades, len(results))
    drift = block_drift(ctxs, windows, repetitions, DRIFT_CONFIG.max_redraws)
    obs = drift["test"]["pooled"]
    # The control's observed sample must be exactly the forced-track test sample.
    assert obs.observed_trades == len(forced_trades), "drift observed trades differ from forced track"
    assert math.isclose(obs.observed_mean, ct_forced.mean_bps, abs_tol=1e-9), "drift observed mean differs"
    ok, fails = qualify_fx(dep, ct_dep, obs.p_value, cfg)
    return {
        "windows": windows, "deployed_stability": dep, "forced_stability": forced,
        "clustered_deployed": ct_dep, "clustered_forced": ct_forced, "drift": drift, "qualified": ok, "failures": fails,
        "descriptive": {"deployed": descriptives(ctxs, windows, True), "forced": descriptives(ctxs, windows, False)},
        "resolution": {"deployed": summary(dep_trades, ct_dep.windows)["achieved_mde_bps"],
                       "forced": summary(forced_trades, ct_forced.windows)["achieved_mde_bps"]},
        "data": {p.symbol: f"{len(p.bars)} bars, {p.timestamps[0]:%Y-%m-%d %H:%M} to {p.timestamps[-1]:%Y-%m-%d %H:%M} UTC" for p in pairs},
    }


def _f(x, fmt):
    return "-" if x is None or (isinstance(x, float) and not math.isfinite(x)) else format(x, fmt)


def render(res: dict) -> str:
    d, f = res["deployed_stability"], res["forced_stability"]
    cd, cf = res["clustered_deployed"], res["clustered_forced"]
    dt = res["drift"]["test"]["pooled"]
    L = [
        "# FX Session Directional Persistence v1 (seven USD majors, H1)",
        "",
        f"Specification (frozen before this run): `{SPEC_PATH}`. Common origin 2021-01-04 UTC; 24M/6M/6M, 6M step; "
        "parameters selected jointly across pairs; commission 0; financing 0 (no position crosses rollover).",
        "",
        f"## Primary outcome: **{'QUALIFIED' if res['qualified'] else 'NOT QUALIFIED'}**",
        "",
        f"Failures: {'; '.join(res['failures']) or 'none'}",
        "",
        "## Pooled test sample and clustering",
        "",
        "| track | trades | unique calendar days | test windows | mean net bps | raw trade-level t (diagnostic) | day-clustered t (qualification) | achieved resolution (bps) |",
        "|---|---|---|---|---|---|---|---|",
        f"| deployed | {cd.trades} | {cd.unique_days} | {cd.windows} | {cd.mean_bps:+.2f} | {cd.raw_t:+.2f} | {cd.clustered_t:+.2f} | {_f(res['resolution']['deployed'], '.2f')} |",
        f"| forced | {cf.trades} | {cf.unique_days} | {cf.windows} | {cf.mean_bps:+.2f} | {cf.raw_t:+.2f} | {cf.clustered_t:+.2f} | {_f(res['resolution']['forced'], '.2f')} |",
        "",
        "Achieved resolution = 2.8416 x clustered SE; descriptive only (design MDE was 2.51 bps central).",
        "",
        "## Walk-forward stability (pooled across pairs)",
        "",
        "| track | windows | traded | abstained | profitable | median bps | worst bps | dispersion | survive 2x | concentration | pooled trades | pooled net | pooled 2x net | pooled validation |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, s in (("deployed", d), ("forced", f)):
        L.append(f"| {name} | {s.windows} | {s.traded_windows} | {s.abstained_windows} | {s.pct_profitable:.0%} | {s.median_window_bps:+.1f} | "
                 f"{s.worst_window_bps:+.1f} | {s.dispersion_bps:.1f} | {s.pct_survive_stress:.0%} | {_f(s.concentration, '.0%')} | "
                 f"{s.pooled_test.trades} | {s.pooled_test.net_bps:+.2f} | {s.pooled_test_stressed.net_bps:+.2f} | {s.pooled_validation.net_bps:+.2f} |")
    pc = dt.control_percentiles
    L += ["", "## Block-randomized drift control (forced track, test segments)", "",
          "| observed mean | control mean | difference | p | p (total) | control p5 / p50 / p95 | observed percentile | trades obs / ctrl | groups | mean dropped groups |",
          "|---|---|---|---|---|---|---|---|---|---|",
          f"| {dt.observed_mean:+.2f} | {dt.control_mean:+.2f} | {dt.difference:+.2f} | {dt.p_value:.3f} | {dt.p_value_total:.3f} | "
          f"{pc['p5']:+.2f} / {pc['p50']:+.2f} / {pc['p95']:+.2f} | {dt.observed_percentile:.0%} | {dt.observed_trades} / {dt.control_mean_trades:.0f} | "
          f"{dt.templates} | {dt.mean_dropped_templates:.2f} |", ""]
    for name in ("train", "validation"):
        c = res["drift"][name]["pooled"]
        L.append(f"- {name} (selection-biased, not evidence): observed {c.observed_mean:+.2f}, control {c.control_mean:+.2f}, p {c.p_value:.3f}")
    per = {x["index"]: x["comparison"] for x in res["drift"]["test"]["windows"]}
    L += ["", "## Windows (joint selection; pooled test)", "",
          "| # | test period | K / theta | train survivors | deployed | val net | test trades | net bps | 2x net | block drift p |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for jw in res["windows"]:
        w = jw.result
        dep = "yes" if w.deployed else f"no ({w.abstain_reason})"
        L.append(f"| {w.index} | {w.periods['test']} | {w.params['window_hours']} / {w.params['theta']} | {w.eligible} | {dep} | "
                 f"{w.validation.net_bps:+.2f} | {w.test.trades} | {w.test.net_bps:+.2f} | {w.test_stressed.net_bps:+.2f} | {per[w.index].p_value:.3f} |")
    for track in ("deployed", "forced"):
        ds = res["descriptive"][track]
        L += ["", f"## Descriptive only ({track} track; no qualification role)", "",
              "| group | trades | unique days | mean net bps | raw t | clustered t |", "|---|---|---|---|---|---|"]
        for label, v in [*ds["sides"].items(), *ds["pairs"].items()]:
            L.append(f"| {label} | {v['trades']} | {v['unique_days']} | {v['mean_bps']:+.2f} | {v['raw_t']:+.2f} | {v['clustered_t']:+.2f} |")
        L += ["", f"Exit reasons: {ds['exit_reasons']}. Late time exits: {ds['late_time_exits']}. "
              f"Signal days: {ds['signal_days']}; mean signalling pairs per signal day: {ds['mean_signals_per_signal_day']:.2f} "
              "(power assumption: k = 7 x 0.40 = 2.8 per day)."]
    L += ["", "Data: " + "; ".join(f"{s} {v}" for s, v in res["data"].items())]
    return "\n".join(L) + "\n"


def results_json(res: dict) -> dict:
    return to_jsonable({
        "schema_version": SCHEMA_VERSION, "spec": SPEC_PATH, "universe": list(UNIVERSE), "grid": list(GRID),
        "qualified": res["qualified"], "failures": res["failures"],
        "clustered": {"deployed": res["clustered_deployed"], "forced": res["clustered_forced"]},
        "resolution": res["resolution"],
        "stability": {"deployed": res["deployed_stability"], "forced": res["forced_stability"]},
        "windows": [w.result for w in res["windows"]], "drift": res["drift"], "descriptive": res["descriptive"], "data": res["data"],
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archive", help="verify and extract the frozen archive before running")
    parser.add_argument("--report")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    if args.archive:
        extract_archive(args.archive)
    res = run(load_pairs())
    text = render(res)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(results_json(res), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
