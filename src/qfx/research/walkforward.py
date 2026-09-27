"""Rolling walk-forward evaluation.

    python -m qfx.research.walkforward --hypothesis trend_continuation \
        --report docs/results/walkforward_trend_continuation.md \
        --json docs/results/walkforward_trend_continuation.json

Per window (calendar time, never shuffled):
1. TRAIN screens the parameter grid: a candidate needs enough trades and
   positive net expectancy after costs.
2. VALIDATION selects among the train survivors.
3. TEST is evaluated once for the selected parameters.

Two tracks are reported so abstention cannot hide instability:
- deployed: what QF-X would have done; abstains (NO_TRADE) when no candidate
  passes train, validation has too few trades, or validation net <= 0.
- forced: always trades the validation-best candidate, measuring the
  hypothesis itself in every window.

Windows are reported individually. Pooled statistics are shown only next to
stability metrics (profitable-window share, median, worst window, dispersion,
cost survival, concentration) so one exceptional period cannot pass as a
repeatable edge.
"""
from __future__ import annotations

import argparse
import json
import math
from bisect import bisect_left
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from datetime import datetime
from enum import Enum
from itertools import product
from pathlib import Path
from statistics import median, pstdev, quantiles
from zoneinfo import ZoneInfo

from ..backtest.bracket import run_bracket_backtest
from ..backtest.engine import Signal, run_backtest
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts, Trade
from . import expansion, sweep
from .baseline import COSTS, GRID
from .evaluation import Stats, trade_stats
from .hypotheses import TrendParams, trend_continuation, trend_features
from .splits import Segment

SCHEMA_VERSION = 1

SignalFactory = Callable[[dict, int, ExecutionCosts], Callable]  # (params, offset, costs) -> fresh signal


Engine = Callable[[Sequence[Bar], Callable, ExecutionCosts], list[Trade]]


def _signal_engine(bars: Sequence[Bar], signal: Callable, costs: ExecutionCosts) -> list[Trade]:
    return run_backtest(bars, signal, costs=costs)


@dataclass(frozen=True)
class HypothesisSpec:
    name: str
    grid: tuple[dict, ...]
    bind: Callable[[Sequence[Bar]], SignalFactory]
    engine: Engine = _signal_engine
    spec_doc: str | None = None  # frozen pre-registration, when one exists


def trend_continuation_spec() -> HypothesisSpec:
    def bind(bars: Sequence[Bar]) -> SignalFactory:
        cache: dict[tuple, object] = {}

        def make(p: dict, offset: int, costs: ExecutionCosts) -> Signal:
            params = TrendParams(**p)
            key = tuple(sorted(p.items()))
            if key not in cache:
                cache[key] = trend_features(bars, params)
            return trend_continuation(bars, params, offset, cache[key])  # type: ignore[arg-type]

        return make

    grid = tuple({"lookback": lb, "entry_z": z} for lb, z in product(GRID["lookback"], GRID["entry_z"]))
    return HypothesisSpec("trend_continuation", grid, bind)


def _bracket_engine(bars: Sequence[Bar], signal: Callable, costs: ExecutionCosts) -> list[Trade]:
    return run_bracket_backtest(bars, signal, costs=costs)


def sweep_reversal_spec(name: str) -> HypothesisSpec:
    """Liquidity Sweep Reversal v1 for one direction (frozen specification)."""
    side = sweep.HYPOTHESES[name]

    def bind(bars: Sequence[Bar]) -> SignalFactory:
        cache: dict[tuple, list] = {}

        def make(p: dict, offset: int, costs: ExecutionCosts) -> Callable:
            key = (p["swing_lookback"], p["confirmation"])
            if key not in cache:
                cache[key] = sweep.find_setups(bars, side, *key)
            return sweep.sweep_signal(bars, cache[key], side, p["target_r"], costs, offset)

        return make

    return HypothesisSpec(name, sweep.grid(), bind, _bracket_engine, sweep.SPEC_PATH)


def vol_expansion_spec(name: str) -> HypothesisSpec:
    """Volatility Expansion v1 for one direction (frozen specification)."""
    side = expansion.HYPOTHESES[name]

    def bind(bars: Sequence[Bar]) -> SignalFactory:
        flags: dict[int, list[bool]] = {}
        setups: dict[tuple, list] = {}

        def make(p: dict, offset: int, costs: ExecutionCosts) -> Callable:
            n, stop = p["box_bars"], p["stop"]
            if n not in flags:
                flags[n] = expansion.compression_flags(bars, n)
            if (n, stop) not in setups:
                setups[(n, stop)] = expansion.find_setups(bars, side, n, stop, flags=flags[n])
            return expansion.expansion_signal(bars, setups[(n, stop)], side, p["target_r"], costs, offset)

        return make

    return HypothesisSpec(name, expansion.grid(), bind, _bracket_engine, expansion.SPEC_PATH)


HYPOTHESIS_SPECS: dict[str, Callable[[], HypothesisSpec]] = {
    "trend_continuation": trend_continuation_spec,
    **{name: (lambda n=name: sweep_reversal_spec(n)) for name in sweep.HYPOTHESES},
    **{name: (lambda n=name: vol_expansion_spec(n)) for name in expansion.HYPOTHESES},
}


@dataclass(frozen=True)
class WalkForwardConfig:
    train_months: int = 24
    validation_months: int = 6
    test_months: int = 6
    step_months: int = 6
    min_partial_test_fraction: float = 0.5
    min_train_trades: int = 30
    min_validation_trades: int = 5
    stress_multiplier: float = 2.0
    # Qualification (applied to the deployed track).
    min_test_trades: int = 30
    min_test_t: float = 2.0
    min_profitable_windows: float = 0.6
    min_stress_survival: float = 0.6
    max_window_concentration: float = 0.5


@dataclass(frozen=True)
class Window:
    index: int
    train: Segment
    validation: Segment
    test: Segment


def add_months(dt: datetime, months: int) -> datetime:
    y, m = divmod(dt.month - 1 + months, 12)
    year, month = dt.year + y, m + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dt.replace(year=year, month=month, day=min(dt.day, days[month - 1]))


def rolling_windows(timestamps: Sequence[datetime], cfg: WalkForwardConfig, origin: datetime | None = None) -> list[Window]:
    """Contiguous, non-overlapping test windows stepping through time.
    ``origin`` fixes a common calendar start across instruments (default:
    the first timestamp)."""
    if not timestamps:
        return []
    origin, last = (origin or timestamps[0]), timestamps[-1]
    windows: list[Window] = []
    k = 0
    while True:
        t0 = add_months(origin, k * cfg.step_months)
        v0 = add_months(t0, cfg.train_months)
        s0 = add_months(v0, cfg.validation_months)
        s1 = add_months(s0, cfg.test_months)
        if s0 >= last:
            break
        if s1 > last:
            covered = (last - s0).total_seconds() / (s1 - s0).total_seconds()
            if covered < cfg.min_partial_test_fraction:
                break
        a, b, c = (bisect_left(timestamps, t) for t in (t0, v0, s0))
        d = bisect_left(timestamps, s1)
        if min(b - a, c - b, d - c) >= 2:
            windows.append(
                Window(len(windows), Segment("train", a, b), Segment("validation", b, c), Segment("test", c, d))
            )
        k += 1
    return windows


@dataclass
class SegmentRun:
    trades: list[Trade]
    hours: float
    stats: Stats


def run_segment(bars: Sequence[Bar], seg: Segment, spec: "HypothesisSpec", make: SignalFactory, params: dict, costs: ExecutionCosts) -> SegmentRun:
    """Cost drag comes from each trade's recorded mid prices, so no separate
    frictionless run is needed (and bracket hypotheses, whose cost gate can
    change which trades happen, stay comparable)."""
    part = bars[seg.start : seg.end]
    hours = (part[-1].timestamp - part[0].timestamp).total_seconds() / 3600
    trades = spec.engine(part, make(params, seg.start, costs), costs)
    return SegmentRun(trades, hours, trade_stats(trades, None, hours))


# --- descriptive context labels (not used for selection) --------------------

SESSIONS = (("asia", 0, 7), ("london", 7, 12), ("overlap", 12, 16), ("new_york", 16, 21), ("late", 21, 24))


def session_of(ts: datetime) -> str:
    return next(name for name, lo, hi in SESSIONS if lo <= ts.hour < hi)


@dataclass(frozen=True)
class Context:
    index: dict[datetime, int]
    vol: list[float]
    trend_z: list[float]


def build_context(bars: Sequence[Bar]) -> Context:
    f = trend_features(bars, TrendParams(lookback=168, entry_z=1.0))
    return Context({b.timestamp: i for i, b in enumerate(bars)}, f.long_vol, f.z)


def breakdown(trades: Sequence[Trade], ctx: Context, train: Segment) -> dict[str, dict[str, dict[str, float]]]:
    """Per-trade labels at entry: UTC session, volatility tercile relative to
    the window's own train period, and trending (|z168| >= 1) vs ranging."""
    train_vol = sorted(v for v in ctx.vol[train.start : train.end] if v == v)
    lo, hi = (quantiles(train_vol, n=3) if len(train_vol) >= 3 else (math.inf, math.inf))
    groups: dict[str, dict[str, list[float]]] = {
        "session": defaultdict(list), "vol_regime": defaultdict(list), "trend_regime": defaultdict(list), "exit": defaultdict(list)
    }
    for t in trades:
        i = ctx.index[t.entry_time]
        bps = t.net_pnl / t.entry_price * 1e4
        v, z = ctx.vol[i], ctx.trend_z[i]
        groups["session"][session_of(t.entry_time)].append(bps)
        groups["vol_regime"]["low" if v <= lo else "normal" if v <= hi else "high"].append(bps)
        groups["trend_regime"]["trending" if z == z and abs(z) >= 1.0 else "ranging"].append(bps)
        groups["exit"][t.exit_reason].append(bps)
    return {
        dim: {label: {"trades": len(xs), "net_bps": sum(xs) / len(xs), "total_bps": sum(xs)} for label, xs in sorted(g.items())}
        for dim, g in groups.items()
    }


# --- per-window evaluation ---------------------------------------------------


@dataclass
class WindowResult:
    index: int
    periods: dict[str, str]
    eligible: int
    params: dict
    deployed: bool
    abstain_reason: str
    train: Stats
    validation: Stats
    test: Stats
    test_stressed: Stats
    breakdown: dict
    _runs: dict[str, SegmentRun] = field(default_factory=dict, repr=False)


def _period(bars: Sequence[Bar], seg: Segment) -> str:
    return f"{bars[seg.start].timestamp:%Y-%m-%d} to {bars[seg.end - 1].timestamp:%Y-%m-%d}"


def stress(bars: Sequence[Bar], costs: ExecutionCosts, k: float) -> tuple[list[Bar], ExecutionCosts]:
    stressed = [replace(b, spread=b.spread * k) if b.spread is not None else b for b in bars]
    return stressed, replace(costs, spread=costs.spread * k, slippage=costs.slippage * k, commission=costs.commission * k)


def evaluate_window(
    w: Window,
    bars: Sequence[Bar],
    stressed: tuple[Sequence[Bar], ExecutionCosts],
    make: SignalFactory,
    spec: HypothesisSpec,
    costs: ExecutionCosts,
    ctx: Context,
    cfg: WalkForwardConfig,
) -> WindowResult:
    train_runs = [(p, run_segment(bars, w.train, spec, make, p, costs)) for p in spec.grid]
    eligible = [(p, r) for p, r in train_runs if r.stats.trades >= cfg.min_train_trades and r.stats.net_bps > 0]

    reason = ""
    if eligible:
        val_runs = [(p, tr, run_segment(bars, w.validation, spec, make, p, costs)) for p, tr in eligible]
        enough = [x for x in val_runs if x[2].stats.trades >= cfg.min_validation_trades]
        params, train_run, val_run = max(enough or val_runs, key=lambda x: x[2].stats.net_bps)
        if not enough:
            reason = f"validation trades < {cfg.min_validation_trades}"
        elif val_run.stats.net_bps <= 0:
            reason = "validation net <= 0"
    else:
        # Nothing passes train: the forced track still measures the train-best.
        params, train_run = max(train_runs, key=lambda x: x[1].stats.net_bps)
        val_run = run_segment(bars, w.validation, spec, make, params, costs)
        reason = "no candidate passed train screen"

    test_run = run_segment(bars, w.test, spec, make, params, costs)
    s_bars, s_costs = stressed
    stressed_run = run_segment(s_bars, w.test, spec, make, params, s_costs)
    return WindowResult(
        index=w.index,
        periods={name: _period(bars, seg) for name, seg in (("train", w.train), ("validation", w.validation), ("test", w.test))},
        eligible=len(eligible),
        params=params,
        deployed=not reason,
        abstain_reason=reason,
        train=train_run.stats,
        validation=val_run.stats,
        test=test_run.stats,
        test_stressed=stressed_run.stats,
        breakdown=breakdown(test_run.trades, ctx, w.train),
        _runs={"validation": val_run, "test": test_run, "stressed": stressed_run},
    )


# --- stability across windows -----------------------------------------------


@dataclass(frozen=True)
class Stability:
    windows: int
    traded_windows: int
    abstained_windows: int
    pct_profitable: float
    median_window_bps: float
    worst_window_bps: float
    worst_window_total_bps: float
    dispersion_bps: float  # std dev of per-window mean net bps
    iqr_bps: float
    pct_survive_stress: float
    concentration: float | None  # largest window total / pooled total, when pooled total > 0
    pooled_validation: Stats
    pooled_test: Stats
    pooled_test_stressed: Stats


def _pool(results: Sequence[WindowResult], key: str) -> Stats:
    trades, hours = [], 0.0
    for r in results:
        run = r._runs[key]
        trades += run.trades
        hours += run.hours
    return trade_stats(trades, None, hours)


def stability(results: Sequence[WindowResult], deployed_only: bool) -> Stability:
    active = [r for r in results if r.deployed or not deployed_only]
    traded = [r for r in active if r.test.trades > 0]
    means = [r.test.net_bps for r in traded]
    pooled = _pool(active, "test") if active else trade_stats([], [], 0)
    totals = [r.test.total_bps for r in traded]
    return Stability(
        windows=len(results),
        traded_windows=len(traded),
        abstained_windows=len(results) - len(active),
        pct_profitable=sum(1 for m in means if m > 0) / len(means) if means else 0.0,
        median_window_bps=median(means) if means else 0.0,
        worst_window_bps=min(means) if means else 0.0,
        worst_window_total_bps=min(totals) if totals else 0.0,
        dispersion_bps=pstdev(means) if len(means) > 1 else 0.0,
        iqr_bps=(lambda q: q[2] - q[0])(quantiles(means, n=4)) if len(means) >= 2 else 0.0,
        pct_survive_stress=sum(1 for r in traded if r.test_stressed.net_bps > 0) / len(traded) if traded else 0.0,
        concentration=max(totals) / pooled.total_bps if totals and pooled.total_bps > 0 else None,
        pooled_validation=_pool(active, "validation") if active else trade_stats([], [], 0),
        pooled_test=pooled,
        pooled_test_stressed=_pool(active, "stressed") if active else trade_stats([], [], 0),
    )


def qualify(s: Stability, cfg: WalkForwardConfig) -> tuple[bool, list[str]]:
    """Conservative single-split rule on pooled out-of-sample trades, plus
    walk-forward consistency so the result must repeat across time."""
    f: list[str] = []
    if s.traded_windows == 0:
        return False, ["no traded test windows"]
    if s.pooled_validation.net_bps <= 0:
        f.append("pooled validation net <= 0")
    if s.pooled_test.net_bps <= 0:
        f.append("pooled test net <= 0")
    if s.pooled_test.trades < cfg.min_test_trades:
        f.append(f"test trades {s.pooled_test.trades} < {cfg.min_test_trades}")
    if s.pooled_test.t_stat < cfg.min_test_t:
        f.append(f"test t {s.pooled_test.t_stat:+.2f} < {cfg.min_test_t}")
    if s.pooled_test_stressed.net_bps <= 0:
        f.append(f"negative at {cfg.stress_multiplier:g}x costs")
    if s.pct_profitable < cfg.min_profitable_windows:
        f.append(f"profitable windows {s.pct_profitable:.0%} < {cfg.min_profitable_windows:.0%}")
    if s.median_window_bps <= 0:
        f.append("median window net <= 0")
    if s.pct_survive_stress < cfg.min_stress_survival:
        f.append(f"windows surviving stress {s.pct_survive_stress:.0%} < {cfg.min_stress_survival:.0%}")
    if s.concentration is not None and s.concentration > cfg.max_window_concentration:
        f.append(f"one window = {s.concentration:.0%} of pooled P&L")
    return not f, f


@dataclass
class SymbolReport:
    symbol: str
    data: str
    costs: ExecutionCosts
    windows: list[WindowResult]
    deployed: Stability
    forced: Stability
    qualified: bool
    failures: list[str]
    forced_qualified: bool
    forced_failures: list[str]
    breakdown_forced: dict


def merge_breakdowns(results: Sequence[WindowResult]) -> dict:
    out: dict = defaultdict(lambda: defaultdict(lambda: {"trades": 0, "total_bps": 0.0}))
    for r in results:
        for dim, labels in r.breakdown.items():
            for label, v in labels.items():
                out[dim][label]["trades"] += v["trades"]
                out[dim][label]["total_bps"] += v["total_bps"]
    return {
        dim: {l: {**v, "net_bps": v["total_bps"] / v["trades"] if v["trades"] else 0.0} for l, v in sorted(ls.items())}
        for dim, ls in out.items()
    }


def run_walkforward(
    symbol: str,
    bars: Sequence[Bar],
    spec: HypothesisSpec,
    costs: ExecutionCosts,
    cfg: WalkForwardConfig = WalkForwardConfig(),
    origin: datetime | None = None,
) -> SymbolReport:
    stressed = stress(bars, costs, cfg.stress_multiplier)
    make = spec.bind(bars)
    ctx = build_context(bars)
    windows = rolling_windows([b.timestamp for b in bars], cfg, origin)
    results = [evaluate_window(w, bars, stressed, make, spec, costs, ctx, cfg) for w in windows]
    dep, forced = stability(results, True), stability(results, False)
    ok, fails = qualify(dep, cfg)
    fok, ffails = qualify(forced, cfg)
    data = f"{len(bars)} bars, {bars[0].timestamp:%Y-%m-%d} to {bars[-1].timestamp:%Y-%m-%d} UTC" if bars else "-"
    return SymbolReport(symbol, data, costs, results, dep, forced, ok, fails, fok, ffails, merge_breakdowns(results))


# --- output ------------------------------------------------------------------


def to_jsonable(obj):
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, WindowResult):
        return to_jsonable({k: v for k, v in obj.__dict__.items() if not k.startswith("_")})
    if is_dataclass(obj):
        return to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def results_json(spec: HypothesisSpec, cfg: WalkForwardConfig, reports: Sequence[SymbolReport]) -> dict:
    return to_jsonable(
        {
            "schema_version": SCHEMA_VERSION,
            "hypothesis": spec.name,
            "grid": list(spec.grid),
            "config": cfg,
            "symbols": {
                r.symbol: {
                    "data": r.data,
                    "costs": r.costs,
                    "qualified": r.qualified,
                    "failures": r.failures,
                    "forced_qualified": r.forced_qualified,
                    "forced_failures": r.forced_failures,
                    "stability": {"deployed": r.deployed, "forced": r.forced},
                    "breakdown_forced_test": r.breakdown_forced,
                    "windows": r.windows,
                }
                for r in reports
            },
        }
    )


def _f(x: float | None, fmt: str) -> str:
    return "-" if x is None or (isinstance(x, float) and not math.isfinite(x)) else format(x, fmt)


def render(spec: HypothesisSpec, cfg: WalkForwardConfig, reports: Sequence[SymbolReport]) -> str:
    L = [
        f"# Walk-forward: {spec.name} (H1)",
        "",
        *([f"Specification (frozen before this run): `{spec.spec_doc}`.", ""] if spec.spec_doc else []),
        f"Windows: {cfg.train_months}m train -> {cfg.validation_months}m validation -> {cfg.test_months}m test, "
        f"step {cfg.step_months}m. Train screen: >= {cfg.min_train_trades} trades and net > 0. "
        f"Validation selects (>= {cfg.min_validation_trades} trades, net > 0, else abstain). "
        f"Grid: {len(spec.grid)} parameter sets. Machine-readable results in the matching `.json` file.",
        "",
        "Qualification (deployed track): pooled validation > 0; pooled test > 0 with "
        f">= {cfg.min_test_trades} trades and t >= {cfg.min_test_t}; positive at {cfg.stress_multiplier:g}x costs; "
        f">= {cfg.min_profitable_windows:.0%} of traded test windows profitable; median window > 0; "
        f">= {cfg.min_stress_survival:.0%} of windows positive at {cfg.stress_multiplier:g}x costs; "
        f"no window > {cfg.max_window_concentration:.0%} of pooled P&L.",
        "",
        "| symbol | deployed qualified | forced qualified | deployed failures |",
        "|---|---|---|---|",
        *[f"| {r.symbol} | {'YES' if r.qualified else 'NO'} | {'YES' if r.forced_qualified else 'NO'} | {'; '.join(r.failures) or '-'} |" for r in reports],
        "",
    ]
    for r in reports:
        L += [f"## {r.symbol}", "", f"Data: {r.data}.", "", "### Stability across test windows", "",
              "| track | windows | traded | abstained | profitable | median bps | worst bps | worst total | dispersion | IQR | survive 2x | concentration | pooled trades | pooled net | pooled t | pooled 2x net | pooled R |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, s in (("deployed", r.deployed), ("forced", r.forced)):
            L.append(
                f"| {name} | {s.windows} | {s.traded_windows} | {s.abstained_windows} | {s.pct_profitable:.0%} | "
                f"{s.median_window_bps:+.1f} | {s.worst_window_bps:+.1f} | {s.worst_window_total_bps:+.0f} | {s.dispersion_bps:.1f} | "
                f"{s.iqr_bps:.1f} | {s.pct_survive_stress:.0%} | {_f(s.concentration, '.0%')} | {s.pooled_test.trades} | "
                f"{s.pooled_test.net_bps:+.1f} | {s.pooled_test.t_stat:+.2f} | {s.pooled_test_stressed.net_bps:+.1f} | {_f(s.pooled_test.avg_r, '+.2f')} |"
            )
        L += ["", "### Windows (test segment of the selected parameters; forced track)", "",
              "| # | test period | params | eligible | deployed | val net | test trades | net bps | avg R | win | avg win | avg loss | PF | t | max DD | cost bps | 2x net |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for w in r.windows:
            t = w.test
            params = " ".join(f"{k}={v}" for k, v in w.params.items())
            dep = "yes" if w.deployed else f"no ({w.abstain_reason})"
            L.append(
                f"| {w.index} | {w.periods['test']} | {params} | {w.eligible} | {dep} | {w.validation.net_bps:+.1f} | {t.trades} | "
                f"{t.net_bps:+.1f} | {_f(t.avg_r, '+.2f')} | {t.win_rate:.0%} | {t.avg_win_bps:.0f} | {t.avg_loss_bps:.0f} | {_f(t.profit_factor, '.2f')} | "
                f"{t.t_stat:+.2f} | {t.max_drawdown_bps:.0f} | {t.cost_bps:.1f} | {w.test_stressed.net_bps:+.1f} |"
            )
        L += ["", "### Context breakdown (all forced test trades; descriptive only)", "", "| dimension | label | trades | net bps | total bps |", "|---|---|---|---|---|"]
        for dim, labels in r.breakdown_forced.items():
            for label, v in labels.items():
                L.append(f"| {dim} | {label} | {v['trades']} | {v['net_bps']:+.1f} | {v['total_bps']:+.0f} |")
        L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="data/mt5")
    parser.add_argument("--report", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument("--hypothesis", default="trend_continuation", choices=sorted(HYPOTHESIS_SPECS))
    args = parser.parse_args(argv)
    spec, cfg = HYPOTHESIS_SPECS[args.hypothesis](), WalkForwardConfig()
    reports = []
    for path in sorted(Path(args.data).glob("*.csv")):
        loaded = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ))
        if loaded.symbol in COSTS:
            reports.append(run_walkforward(loaded.symbol, loaded.bars, spec, COSTS[loaded.symbol], cfg))
    text = render(spec, cfg, reports)
    print(text)
    for target, content in ((args.report, text + "\n"), (args.json, json.dumps(results_json(spec, cfg, reports), indent=2) + "\n")):
        if target:
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
