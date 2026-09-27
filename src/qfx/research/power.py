"""Statistical resolution (power) of the completed QF-X experiments.

DESCRIPTIVE ONLY. This module measures what effect size each completed
experiment could have distinguished from noise. It does not change any
verdict, qualification rule or threshold, and it must not be used to
redefine what counts as a successful result.

    python -m qfx.research.power --report docs/results/power_analysis.md --json docs/results/power_analysis.json

For each experiment (forced track, test segments) it reports the smallest
true mean edge per trade (bps) that gives an 80% chance of passing each
qualification component:

- t >= 2 (IID SE; day-clustered SE shown alongside);
- >= 60% of traded windows profitable (binomial over the actual window count,
  normal approximation per window with the observed trades per window);
- drift control p <= 0.05, from the spread of the experiment's own stored null
  distribution: 1.645 + 0.842 null standard deviations.

The design resolution is the largest component MDE, since all must pass.
Per-trade data come from re-running the frozen experiment code; every
reproduction is checked against the published pooled mean.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import timezone
from pathlib import Path
from statistics import mean, stdev
from zoneinfo import ZoneInfo

from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Trade
from .baseline import COSTS
from .drift import bps
from .walkforward import HYPOTHESIS_SPECS, WalkForwardConfig, run_walkforward

POWER = 0.80
Z_POWER = 0.8416212335729143  # Phi^-1(0.80)
Z_ALPHA = 1.6448536269514722  # one-sided 5%
T_RULE = 2.0
MIN_PROFITABLE = 0.6


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def se_iid(x: Sequence[float]) -> float:
    return stdev(x) / math.sqrt(len(x)) if len(x) > 1 else math.inf


def se_day(trades: Sequence[Trade]) -> float:
    """Calendar-day clustered SE (same CR1 formula as Replication R1)."""
    x = [bps(t) for t in trades]
    n, m = len(x), mean(x)
    groups: dict = defaultdict(float)
    for t, v in zip(trades, x):
        groups[t.entry_time.astimezone(timezone.utc).date()] += v - m
    g = len(groups)
    return math.sqrt(g / (g - 1) * sum(v * v for v in groups.values())) / n if g > 1 else math.inf


def mde_t(se: float) -> float:
    """Edge with an 80% chance that mean / SE >= 2."""
    return (T_RULE + Z_POWER) * se


def p_windows_pass(delta: float, sd: float, per_window: float, windows: int) -> float:
    """P(at least 60% of windows have a positive mean), each window's mean ~ N(delta, sd^2/per_window)."""
    p = phi(delta * math.sqrt(per_window) / sd)
    need = math.ceil(MIN_PROFITABLE * windows - 1e-9)
    return sum(math.comb(windows, k) * p ** k * (1 - p) ** (windows - k) for k in range(need, windows + 1))


def mde_windows(sd: float, per_window: float, windows: int) -> float:
    lo, hi = 0.0, 10 * sd
    for _ in range(100):
        mid = (lo + hi) / 2
        if p_windows_pass(mid, sd, per_window, windows) >= POWER:
            hi = mid
        else:
            lo = mid
    return hi


def mde_drift(null_sd: float) -> float:
    return (Z_ALPHA + Z_POWER) * null_sd


@dataclass(frozen=True)
class Resolution:
    experiment: str
    symbol: str
    trades: int
    windows: int
    trades_per_window: float
    observed_bps: float
    cost_bps: float
    sd_bps: float
    unique_days: int
    se_iid: float
    se_day: float
    mde_t_iid: float
    mde_t_day: float
    mde_windows: float
    mde_drift: float | None
    design_mde: float
    mde_over_cost: float


def resolution(experiment: str, symbol: str, trades: Sequence[Trade], windows: int, cost_bps: float, null_sd: float | None) -> Resolution:
    x = [bps(t) for t in trades]
    sd = stdev(x)
    days = len({t.entry_time.astimezone(timezone.utc).date() for t in trades})
    s_iid, s_day = se_iid(x), se_day(trades)
    m_t, m_td = mde_t(s_iid), mde_t(s_day)
    m_w = mde_windows(sd, len(x) / windows, windows)
    m_d = mde_drift(null_sd) if null_sd is not None else None
    design = max(v for v in (m_td, m_w, m_d) if v is not None)
    return Resolution(experiment, symbol, len(x), windows, len(x) / windows, mean(x), cost_bps, sd, days, s_iid, s_day,
                      m_t, m_td, m_w, m_d, design, design / cost_bps if cost_bps > 0 else math.inf)


# --- reproduction of completed experiments ----------------------------------------------

WALKFORWARD_EXPERIMENTS = {
    "trend_continuation": ("walkforward_trend_continuation.json", None),
    "sweep_reversal_long": ("walkforward_sweep_reversal_long.json", ("drift_baseline_v1.json", "sweep_reversal_long")),
    "sweep_reversal_short": ("walkforward_sweep_reversal_short.json", ("drift_baseline_v1.json", "sweep_reversal_short")),
    "vol_expansion_long": ("walkforward_vol_expansion_long.json", ("drift_baseline_v1_vol_expansion.json", "vol_expansion_long")),
    "vol_expansion_short": ("walkforward_vol_expansion_short.json", ("drift_baseline_v1_vol_expansion.json", "vol_expansion_short")),
}


def null_sd_from(results_dir: Path, source: tuple[str, str] | None, symbol: str) -> float | None:
    if source is None:
        return None
    data = json.loads((results_dir / source[0]).read_text())["results"][source[1]][symbol]
    return stdev(data["pooled_control_means"]["test"])


def reproduce_walkforward(data_dir: Path, results_dir: Path) -> list[Resolution]:
    bars = {}
    for path in sorted(data_dir.glob("*.csv")):
        loaded = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ))
        bars[loaded.symbol] = loaded.bars
    out = []
    for name, (report_file, drift_source) in WALKFORWARD_EXPERIMENTS.items():
        published = json.loads((results_dir / report_file).read_text())["symbols"]
        for symbol, series in bars.items():
            rep = run_walkforward(symbol, series, HYPOTHESIS_SPECS[name](), COSTS[symbol], WalkForwardConfig())
            trades = [t for w in rep.windows for t in w._runs["test"].trades]
            want = published[symbol]["stability"]["forced"]["pooled_test"]["net_bps"]
            got = mean(bps(t) for t in trades) if trades else 0.0
            if not math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-9):
                raise AssertionError(f"{name} {symbol}: reproduced {got} != published {want}")
            out.append(resolution(name, symbol, trades, rep.forced.traded_windows,
                                  rep.forced.pooled_test.cost_bps, null_sd_from(results_dir, drift_source, symbol)))
    return out


def reproduce_replication(results_dir: Path) -> Resolution:
    from .replication import ORIGIN, costs_for, load_coins, pooled_windows, vol_expansion_spec

    data = load_coins()
    reports = [run_walkforward(s, b, vol_expansion_spec("vol_expansion_long"), costs_for(s), WalkForwardConfig(), ORIGIN) for s, b in data.items()]
    forced = pooled_windows(reports, False)
    trades = [t for w in forced for t in w._runs["test"].trades]
    published = json.loads((results_dir / "replication_r1.json").read_text())
    want = published["clustered"]["forced"]["mean_bps"]
    got = mean(bps(t) for t in trades)
    if not math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"replication: reproduced {got} != published {want}")
    pc = published["drift"]["test"]["pooled"]["control_percentiles"]
    null_sd = (pc["p95"] - pc["p5"]) / (2 * Z_ALPHA)  # normal approximation from stored percentiles
    ideal = [((t.mid_exit - t.mid_entry) / t.mid_entry * 1e4) for t in trades]
    cost = mean(i - bps(t) for i, t in zip(ideal, trades))
    windows = sum(1 for w in forced if w.test.trades > 0)
    return resolution("replication_r1_pooled", "ETH+LTC+XRP", trades, windows, cost, null_sd)


def render(rows: Sequence[Resolution]) -> str:
    L = [
        "# Statistical resolution of completed experiments (descriptive)",
        "",
        "**Descriptive only.** This report does not change any verdict, qualification rule or threshold. "
        "It shows the smallest true mean edge per trade (bps) that each completed experiment would have detected "
        f"with {POWER:.0%} probability, per qualification component (forced track, test segments). "
        "The design MDE is the largest component, since all must pass.",
        "",
        "| experiment | symbol | trades | windows | trades/window | observed bps | cost bps | sd bps | days | MDE t>=2 (IID) | MDE t>=2 (day-clustered) | MDE windows>=60% | MDE drift p<=0.05 | **design MDE** | MDE / cost |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md = "-" if r.mde_drift is None else f"{r.mde_drift:.1f}"
        L.append(f"| {r.experiment} | {r.symbol} | {r.trades} | {r.windows} | {r.trades_per_window:.0f} | {r.observed_bps:+.1f} | {r.cost_bps:.1f} | "
                 f"{r.sd_bps:.0f} | {r.unique_days} | {r.mde_t_iid:.1f} | {r.mde_t_day:.1f} | {r.mde_windows:.1f} | {md} | **{r.design_mde:.1f}** | {r.mde_over_cost:.1f}x |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="data/mt5")
    parser.add_argument("--results", default="docs/results")
    parser.add_argument("--report")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    rows = reproduce_walkforward(Path(args.data), Path(args.results)) + [reproduce_replication(Path(args.results))]
    text = render(rows)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in rows], indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
