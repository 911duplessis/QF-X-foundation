"""Replication R1: Volatility Expansion v1 (long, unchanged) on the eligible
broker crypto universe, per the frozen specification
``docs/hypotheses/replication_r1_vol_expansion_crypto.md`` (v2).

    python -m qfx.research.replication \
        --report docs/results/replication_r1.md --json docs/results/replication_r1.json

Primary outcome (single test, pooled over ETHUSD, LTCUSD, XRPUSD):
every walk-forward qualification rule on the pooled deployed track, with the
pooled t replaced by a calendar-day clustered t >= 2, AND block-randomized
drift control p <= 0.05 (forced track, as in Drift Baseline v1). Per-coin
results are descriptive only. Financing is 0 (swap-free account); standard
swaps are a descriptive sensitivity.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

from ..backtest.bracket import BracketOrder, run_bracket_backtest
from ..backtest.financing import SwapSpec, financing_cost_bps
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts, Side, Trade
from . import expansion
from .baseline import COSTS as V1_COSTS
from .drift import CONFIG as DRIFT_CONFIG
from .drift import Gates, Template, bps, compare, extract_templates, seed_for
from .evaluation import trade_stats
from .splits import Segment
from .walkforward import (
    SegmentRun,
    Stability,
    SymbolReport,
    WalkForwardConfig,
    Window,
    WindowResult,
    qualify,
    rolling_windows,
    run_walkforward,
    stability,
    to_jsonable,
    vol_expansion_spec,
)

SPEC_PATH = "docs/hypotheses/replication_r1_vol_expansion_crypto.md"
SCHEMA_VERSION = 1
HYPOTHESIS = "vol_expansion_long"
ELIGIBLE = ("ETHUSD.m", "LTCUSD.m", "XRPUSD.m")
DATA_DIR = "data/mt5/replication_r1"
ORIGIN = datetime(2021, 1, 1, tzinfo=timezone.utc)
SPREAD_FLOORS = {"ETHUSD.m": 1.4, "LTCUSD.m": 1.43, "XRPUSD.m": 0.01}
SLIPPAGE_RATIO = 1 / 6
COMMISSION = 0.0
MIN_CLUSTERED_T = 2.0
DRIFT_MAX_P = 0.05
# Standard (non-swap-free) long swaps, points/night, and point size from quote digits.
STANDARD_SWAPS = {
    "ETHUSD.m": SwapSpec(-280.56, 0.01),
    "LTCUSD.m": SwapSpec(-10.632, 0.01),
    "XRPUSD.m": SwapSpec(-27.828, 0.0001),
    "BTCUSD": SwapSpec(-8466.6, 0.01),
}


def costs_for(symbol: str) -> ExecutionCosts:
    floor = SPREAD_FLOORS[symbol]
    return ExecutionCosts(spread=floor, slippage=floor * SLIPPAGE_RATIO, commission=COMMISSION)


# --- clustered inference ------------------------------------------------------


@dataclass(frozen=True)
class ClusteredT:
    trades: int
    unique_days: int
    windows: int
    mean_bps: float
    raw_t: float  # IID trade-level t, diagnostic only
    clustered_t: float  # calendar-day clustered t, used for qualification


def clustered_t(trades: Sequence[Trade], windows: int) -> ClusteredT:
    """t = mean / SE, SE = sqrt(G/(G-1) * sum_g (sum_{i in g}(x_i - mean))^2) / n,
    clusters = UTC calendar day of entry. Fewer than 2 clusters gives t = 0."""
    x = [bps(t) for t in trades]
    n = len(x)
    if n == 0:
        return ClusteredT(0, 0, windows, 0.0, 0.0, 0.0)
    m = mean(x)
    by_day: dict = defaultdict(float)
    for t, v in zip(trades, x):
        by_day[t.entry_time.astimezone(timezone.utc).date()] += v - m
    g = len(by_day)
    ss = sum(v * v for v in by_day.values())
    se_c = math.sqrt(g / (g - 1) * ss) / n if g > 1 else 0.0
    dev = sum((v - m) ** 2 for v in x)
    se_raw = math.sqrt(dev / (n * (n - 1))) if n > 1 else 0.0
    return ClusteredT(n, g, windows, m, m / se_raw if se_raw > 0 else 0.0, m / se_c if se_c > 0 else 0.0)


# --- pooling --------------------------------------------------------------------


def _merge(runs: Sequence[SegmentRun]) -> SegmentRun:
    trades = [t for r in runs for t in r.trades]
    hours = sum(r.hours for r in runs)
    return SegmentRun(trades, hours, trade_stats(trades, None, hours))


def pooled_windows(reports: Sequence[SymbolReport], deployed_only: bool) -> list[WindowResult]:
    """Window-by-window pooling across coins (identical calendar windows)."""
    n = len(reports[0].windows)
    assert all(len(r.windows) == n for r in reports), "coins must share the window grid"
    out = []
    for k in range(n):
        ws = [r.windows[k] for r in reports]
        assert all(w.periods == ws[0].periods for w in ws), "windows must cover identical periods"
        members = [w for w in ws if w.deployed or not deployed_only]
        runs = {key: _merge([w._runs[key] for w in members]) for key in ("validation", "test", "stressed")}
        empty = trade_stats([], None, 0)
        out.append(
            WindowResult(
                index=k,
                periods=ws[0].periods,
                eligible=sum(w.eligible for w in ws),
                params={r.symbol: w.params for r, w in zip(reports, ws)},
                deployed=bool(members),
                abstain_reason="" if members else "all coins abstained",
                train=empty,
                validation=runs["validation"].stats,
                test=runs["test"].stats,
                test_stressed=runs["stressed"].stats,
                breakdown={},
                _runs=runs,
            )
        )
    return out


# --- block-randomized drift control ------------------------------------------------


@dataclass
class Coin:
    symbol: str
    bars: list[Bar]
    costs: ExecutionCosts
    gates: Gates
    make: object
    windows: list[Window]
    index: dict = field(default_factory=dict)  # timestamp -> global bar index


def _segment(w: Window, name: str) -> Segment:
    return {"train": w.train, "validation": w.validation, "test": w.test}[name]


def block_drift_segment(
    coins: Sequence[Coin], params: Sequence[dict], k: int, name: str, repetitions: int, max_redraws: int
) -> tuple[list[float], list[list[float]], list[int], int]:
    """Observed pooled net bps and N control repetitions for one window and
    segment. Signals sharing a timestamp form a group; each group is replayed
    at one random same-UTC-hour timestamp, redrawn as a whole on any member's
    gate failure (up to ``max_redraws`` redraws), else dropped as a whole."""
    observed: list[float] = []
    groups: dict[datetime, list[tuple[int, Template]]] = defaultdict(list)
    segs, signals = [], []
    for c_i, (coin, p) in enumerate(zip(coins, params)):
        seg = _segment(coin.windows[k], name)
        segs.append(seg)
        signal = coin.make(p, seg.start, coin.costs)
        signals.append(signal)
        observed += [bps(t) for t in run_bracket_backtest(coin.bars[seg.start : seg.end], signal, costs=coin.costs)]
        for t in extract_templates(coin.bars, seg, signal, coin.gates.atr):
            groups[coin.bars[t.bar].timestamp].append((c_i, t))
    start = min(c.bars[s.start].timestamp for c, s in zip(coins, segs))
    end = max(c.bars[s.end - 1].timestamp for c, s in zip(coins, segs))
    stamps = sorted({b.timestamp for c in coins for b in c.bars if start <= b.timestamp <= end})
    by_hour: dict[int, list[datetime]] = defaultdict(list)
    for ts in stamps:
        by_hour[ts.hour].append(ts)
    ordered = sorted(groups.items())
    control, dropped = [], []
    for r in range(repetitions):
        rng = random.Random(seed_for("replication_r1", "block", k, name, r))
        pools = {h: list(v) for h, v in by_hour.items()}
        orders: list[dict[int, BracketOrder]] = [dict() for _ in coins]
        n_dropped = 0
        for ts, members in ordered:
            pool = pools.get(ts.hour, [])
            placed = False
            for _ in range(1 + max_redraws):
                if not pool:
                    break
                j = rng.randrange(len(pool))
                pool[j], pool[-1] = pool[-1], pool[j]
                cand = pool.pop()
                spots = []
                for c_i, t in members:
                    coin, seg = coins[c_i], segs[c_i]
                    h = coin.index.get(cand)
                    if h is None or not seg.start <= h < seg.end - 1 or not coin.gates.passes(coin.bars, h, t.k):
                        break
                    spots.append((c_i, h, t))
                else:
                    for c_i, h, t in spots:
                        coin = coins[c_i]
                        stop = coin.bars[h].close - t.k * coin.gates.atr[h]
                        orders[c_i][h - segs[c_i].start] = BracketOrder(Side.LONG, stop, params[c_i]["target_r"], expansion.FIXED.max_hold_bars)
                    placed = True
                    break
            n_dropped += not placed
        rep: list[float] = []
        for c_i, coin in enumerate(coins):
            seg, o = segs[c_i], orders[c_i]
            rep += [bps(t) for t in run_bracket_backtest(coin.bars[seg.start : seg.end], lambda v, i, o=o: o.get(i), costs=coin.costs)]
        control.append(rep)
        dropped.append(n_dropped)
    return observed, control, dropped, len(ordered)


def block_drift(coins: Sequence[Coin], reports: Sequence[SymbolReport], repetitions: int, max_redraws: int) -> dict:
    out = {}
    for name in DRIFT_CONFIG.segments:
        observed, control, dropped, groups = [], [[] for _ in range(repetitions)], [0] * repetitions, 0
        per_window = []
        for k in range(len(reports[0].windows)):
            params = [r.windows[k].params for r in reports]
            obs, ctrl, drp, g = block_drift_segment(coins, params, k, name, repetitions, max_redraws)
            observed += obs
            for i in range(repetitions):
                control[i] += ctrl[i]
                dropped[i] += drp[i]
            groups += g
            per_window.append({"index": k, "comparison": compare(obs, ctrl, drp, g)})
        out[name] = {"pooled": compare(observed, control, dropped, groups), "windows": per_window}
    return out


# --- financing sensitivity -----------------------------------------------------------


def financing_summary(trades_by_symbol: dict[str, list[Trade]]) -> dict:
    rows, all_net, all_fin = {}, [], []
    for sym, trades in trades_by_symbol.items():
        net = [bps(t) for t in trades]
        fin = [bps(t) - financing_cost_bps(t, STANDARD_SWAPS[sym]) for t in trades]
        rows[sym] = {"trades": len(trades), "net_bps_swap_free": mean(net) if net else 0.0,
                     "net_bps_standard_swaps": mean(fin) if fin else 0.0}
        all_net += net
        all_fin += fin
    rows["pooled"] = {"trades": len(all_net), "net_bps_swap_free": mean(all_net) if all_net else 0.0,
                      "net_bps_standard_swaps": mean(all_fin) if all_fin else 0.0}
    return rows


def btc_recost(data_dir: str = "data/mt5") -> dict:
    """Descriptive re-costing of the Volatility Expansion v1 BTCUSD long forced
    test trades at standard swap rates. Cannot alter the replication."""
    path = sorted(Path(data_dir).glob("BTCUSD*.csv"))[0]
    bars = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ)).bars
    report = run_walkforward("BTCUSD", bars, vol_expansion_spec(HYPOTHESIS), V1_COSTS["BTCUSD"])
    trades = [t for w in report.windows for t in w._runs["test"].trades]
    return financing_summary({"BTCUSD": trades})["BTCUSD"]


# --- qualification -----------------------------------------------------------------------


def qualify_replication(dep: Stability, ct: ClusteredT, drift_p: float, cfg: WalkForwardConfig) -> tuple[bool, list[str]]:
    """All existing walk-forward rules with the IID pooled t replaced by the
    day-clustered t, plus the block drift test."""
    _, fails = qualify(dep, replace(cfg, min_test_t=-math.inf))
    if ct.clustered_t < MIN_CLUSTERED_T:
        fails.append(f"day-clustered t {ct.clustered_t:+.2f} < {MIN_CLUSTERED_T}")
    if drift_p > DRIFT_MAX_P:
        fails.append(f"block drift p {drift_p:.3f} > {DRIFT_MAX_P}")
    return not fails, fails


# --- run ---------------------------------------------------------------------------------


def load_coins(data_dir: str = DATA_DIR) -> dict[str, list[Bar]]:
    out = {}
    for sym in ELIGIBLE:
        path = sorted(Path(data_dir).glob(f"{sym}_H1_*.csv"))[0]
        bars = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ)).bars
        out[sym] = [b for b in bars if b.timestamp >= ORIGIN]
    end = min(b[-1].timestamp for b in out.values())
    return {s: [b for b in bars if b.timestamp <= end] for s, bars in out.items()}


def run(data_dir: str = DATA_DIR, repetitions: int = DRIFT_CONFIG.repetitions, cfg: WalkForwardConfig = WalkForwardConfig(),
        include_btc_recost: bool = True) -> dict:
    spec = vol_expansion_spec(HYPOTHESIS)
    data = load_coins(data_dir)
    reports = [run_walkforward(s, bars, spec, costs_for(s), cfg, ORIGIN) for s, bars in data.items()]
    dep_w, forced_w = pooled_windows(reports, True), pooled_windows(reports, False)
    dep, forced = stability(dep_w, True), stability(forced_w, False)
    dep_trades = [t for w in dep_w if w.deployed for t in w._runs["test"].trades]
    forced_trades = [t for w in forced_w for t in w._runs["test"].trades]
    ct_dep = clustered_t(dep_trades, sum(1 for w in dep_w if w.deployed))
    ct_forced = clustered_t(forced_trades, len(forced_w))
    coins = []
    for s, bars in data.items():
        c = Coin(s, bars, costs_for(s), Gates.for_bars(bars, costs_for(s)), spec.bind(bars),
                 rolling_windows([b.timestamp for b in bars], cfg, ORIGIN))
        c.index = {b.timestamp: i for i, b in enumerate(bars)}
        coins.append(c)
    drift = block_drift(coins, reports, repetitions, DRIFT_CONFIG.max_redraws)
    # The control's observed sample must be exactly the forced-track test sample.
    obs = drift["test"]["pooled"]
    assert obs.observed_trades == len(forced_trades), "drift observed trades differ from forced track"
    assert math.isclose(obs.observed_mean, clustered_t(forced_trades, 0).mean_bps, abs_tol=1e-9), "drift observed mean differs"
    drift_p = obs.p_value
    ok, fails = qualify_replication(dep, ct_dep, drift_p, cfg)
    fin = {
        "deployed": financing_summary({r.symbol: [t for w in r.windows if w.deployed for t in w._runs["test"].trades] for r in reports}),
        "forced": financing_summary({r.symbol: [t for w in r.windows for t in w._runs["test"].trades] for r in reports}),
    }
    return {
        "reports": reports, "deployed_stability": dep, "forced_stability": forced,
        "deployed_windows": dep_w, "forced_windows": forced_w,
        "clustered_deployed": ct_dep, "clustered_forced": ct_forced,
        "drift": drift, "replicated": ok, "failures": fails, "financing": fin,
        "btc_recost": btc_recost() if include_btc_recost else None,
        "data": {s: f"{len(b)} bars, {b[0].timestamp:%Y-%m-%d %H:%M} to {b[-1].timestamp:%Y-%m-%d %H:%M} UTC" for s, b in data.items()},
    }


def _f(x, fmt):
    return "-" if x is None or (isinstance(x, float) and not math.isfinite(x)) else format(x, fmt)


def render(res: dict) -> str:
    d, f = res["deployed_stability"], res["forced_stability"]
    cd, cf = res["clustered_deployed"], res["clustered_forced"]
    dt = res["drift"]["test"]["pooled"]
    L = [
        "# Replication R1: Volatility Expansion v1 (long) on ETHUSD, LTCUSD, XRPUSD",
        "",
        f"Specification (frozen, v2): `{SPEC_PATH}`. Universe N = 3 by the pre-registered eligibility rule. "
        "Common window origin 2021-01-01 UTC; 24M/6M/6M, 6M step; per-coin parameter selection as v1; financing 0 (swap-free).",
        "",
        f"## Primary outcome: **{'REPLICATED' if res['replicated'] else 'NOT REPLICATED'}**",
        "",
        f"Failures: {'; '.join(res['failures']) or 'none'}",
        "",
        "## Pooled test sample and clustering",
        "",
        "| track | trades | unique calendar days | test windows | mean net bps | raw trade-level t (diagnostic) | day-clustered t (qualification) |",
        "|---|---|---|---|---|---|---|",
        f"| deployed | {cd.trades} | {cd.unique_days} | {cd.windows} | {cd.mean_bps:+.2f} | {cd.raw_t:+.2f} | {cd.clustered_t:+.2f} |",
        f"| forced | {cf.trades} | {cf.unique_days} | {cf.windows} | {cf.mean_bps:+.2f} | {cf.raw_t:+.2f} | {cf.clustered_t:+.2f} |",
        "",
        "## Walk-forward stability (pooled across coins, window by window)",
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
    L += ["", "## Windows (pooled test, deployed track)", "",
          "| # | test period | params per coin | coins deployed | trades | net bps | block drift p |", "|---|---|---|---|---|---|---|"]
    per = {x["index"]: x["comparison"] for x in res["drift"]["test"]["windows"]}
    for w in res["deployed_windows"]:
        params = "; ".join(f"{s.split('.')[0]}: {p['box_bars']}/{p['stop']}/{p['target_r']}" for s, p in w.params.items())
        n_dep = sum(1 for r in res["reports"] if r.windows[w.index].deployed)
        L.append(f"| {w.index} | {w.periods['test']} | {params} | {n_dep}/3 | {w.test.trades} | {w.test.net_bps:+.2f} | {per[w.index].p_value:.3f} |")
    L += ["", "## Per coin (descriptive only; no qualification role)", "",
          "| coin | forced test trades | net bps | t (IID) | profitable windows | deployed windows | 2x net |", "|---|---|---|---|---|---|---|"]
    for r in res["reports"]:
        s = r.forced
        L.append(f"| {r.symbol} | {s.pooled_test.trades} | {s.pooled_test.net_bps:+.2f} | {s.pooled_test.t_stat:+.2f} | {s.pct_profitable:.0%} | "
                 f"{r.deployed.traded_windows}/{r.deployed.windows} | {s.pooled_test_stressed.net_bps:+.2f} |")
    L += ["", "## Financing sensitivity (descriptive only)", "",
          "Primary uses financing = 0 (swap-free). Standard swaps: long points/night at 22:00 server, weekdays, Wednesday x3.", "",
          "| track | coin | trades | net bps swap-free | net bps standard swaps |", "|---|---|---|---|---|"]
    for track in ("deployed", "forced"):
        for sym, v in res["financing"][track].items():
            L.append(f"| {track} | {sym} | {v['trades']} | {v['net_bps_swap_free']:+.2f} | {v['net_bps_standard_swaps']:+.2f} |")
    if res["btc_recost"]:
        b = res["btc_recost"]
        L += ["", f"**BTCUSD v1 candidate re-costed (forced test, diagnostic only):** {b['trades']} trades, "
              f"{b['net_bps_swap_free']:+.2f} bps swap-free vs {b['net_bps_standard_swaps']:+.2f} bps at standard swaps."]
    L += ["", "Data: " + "; ".join(f"{s} {v}" for s, v in res["data"].items())]
    return "\n".join(L) + "\n"


def results_json(res: dict) -> dict:
    return to_jsonable({
        "schema_version": SCHEMA_VERSION, "spec": SPEC_PATH, "hypothesis": HYPOTHESIS, "universe": list(ELIGIBLE),
        "replicated": res["replicated"], "failures": res["failures"],
        "clustered": {"deployed": res["clustered_deployed"], "forced": res["clustered_forced"]},
        "stability": {"deployed": res["deployed_stability"], "forced": res["forced_stability"]},
        "drift": res["drift"], "financing": res["financing"], "btc_recost": res["btc_recost"], "data": res["data"],
        "per_coin": {r.symbol: {"deployed": r.deployed, "forced": r.forced, "windows": r.windows} for r in res["reports"]},
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    res = run()
    text = render(res)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(results_json(res), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
