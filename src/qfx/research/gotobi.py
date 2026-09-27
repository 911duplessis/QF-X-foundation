"""USDJPY Gotobi-Day Tokyo Fix v1, per the frozen specification
``docs/hypotheses/usdjpy_gotobi_v1.md`` (a test fails if the constants here
drift from its JSON block).

    python -m qfx.research.gotobi --csv <path to the quarantined CSV> \
        --report docs/results/usdjpy_gotobi_v1.md --json docs/results/usdjpy_gotobi_v1.json

One parameter-free trade per gotobi day: long USDJPY from the open of the
00:00 UTC bar (09:00 JST) to the open of the 01:00 UTC bar (10:00 JST).
Version 2: qualification uses all H1 data 2019-06-10..2026-09-25 (days inside
the one documented data gap excluded) with Bonferroni-adjusted t >= 2.28 on
both t-gates. The placebo is the same trade on non-gotobi Japanese bank
business days.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import shutil
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import mean, median, stdev
from zoneinfo import ZoneInfo

from ..backtest.costs import execution_price
from ..backtest.engine import _spread
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts, Side, Trade
from .walkforward import to_jsonable

SPEC_PATH = "docs/hypotheses/usdjpy_gotobi_v1.md"
SCHEMA_VERSION = 1
SPEC_VERSION = 2
SYMBOL = "USDJPY.m"
CSV_NAME = "USDJPY.m_H1_201308230000_202609252300.csv"
CSV_SHA256 = "578b734606f674bfef3ca6c8758a11335fecf2258ea550c9c15bef0f9633d05f"
DATA_DIR = "data/mt5/gotobi_v1"
CALENDAR_PATH = "docs/hypotheses/assets/jp_bank_holidays_2013_2026.json"
CALENDAR_SHA256 = "3fc1131a9d7ea4ea7f02325b43c289cb161fa773695f96c5282814621ee400be"
GOTOBI_DAYS = (5, 10, 15, 20, 25, 30)
ENTRY_UTC = time(0, 0)
EXIT_UTC = time(1, 0)
PRIMARY = (date(2019, 6, 10), date(2026, 9, 25))
EXCLUDED = (date(2019, 12, 17), date(2020, 3, 29))  # days inside the documented data gap
SUBPERIODS = ((date(2019, 6, 10), date(2020, 12, 31)), (date(2021, 1, 4), date(2026, 9, 25)))  # descriptive
DOCUMENTED_GAP = (datetime(2019, 12, 16, 13, tzinfo=timezone.utc), datetime(2020, 3, 29, 21, tzinfo=timezone.utc))
MAX_GAP = timedelta(days=4)
SPREAD_FLOOR = 0.025
SLIPPAGE_RATIO = 1 / 6
COMMISSION = 0.0
STRESS = 2.0
MIN_T = 2.28  # Bonferroni, family of 2 tests on this data
PLACEBO_MIN_T = 2.28
MIN_YEAR_SHARE = 0.6
MIN_YEAR_EVENTS = 30
MIN_TRADES = 400
MDE_MULTIPLIER = MIN_T + 0.8416  # detection at the qualification threshold, 80% power

COSTS = ExecutionCosts(spread=SPREAD_FLOOR, slippage=SPREAD_FLOOR * SLIPPAGE_RATIO, commission=COMMISSION)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- calendar ------------------------------------------------------------------------


def load_closures(path: str | Path = CALENDAR_PATH, expected: str = CALENDAR_SHA256) -> frozenset[date]:
    digest = sha256_file(path)
    if digest != expected:
        raise ValueError(f"calendar sha256 {digest} != frozen {expected}")
    return frozenset(date.fromisoformat(d) for d in json.loads(Path(path).read_text())["dates"])


def is_business_day(d: date, closures: frozenset[date]) -> bool:
    return d.weekday() < 5 and d not in closures


def gotobi_days(start: date, end: date, closures: frozenset[date]) -> list[date]:
    """5/10/15/20/25/30 of each month, rolled back to the preceding bank
    business day; no February month-end event; duplicates count once."""
    out: set[date] = set()
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        last = calendar.monthrange(y, m)[1]
        for day in GOTOBI_DAYS:
            if day > last:
                continue
            d = date(y, m, day)
            while not is_business_day(d, closures):
                d -= timedelta(days=1)
            out.add(d)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return sorted(d for d in out if start <= d <= end)


def placebo_days(start: date, end: date, closures: frozenset[date], gotobi: Sequence[date]) -> list[date]:
    g, out, d = set(gotobi), [], start
    while d <= end:
        if is_business_day(d, closures) and d not in g:
            out.append(d)
        d += timedelta(days=1)
    return out


# --- trades ------------------------------------------------------------------------------


def day_trade(bars: Sequence[Bar], index: dict[datetime, int], d: date, costs: ExecutionCosts) -> Trade | None:
    """Long from the 00:00 UTC bar open to the 01:00 UTC bar open on date d;
    None when either bar is missing (availability only)."""
    t0 = datetime.combine(d, ENTRY_UTC, timezone.utc)
    t1 = datetime.combine(d, EXIT_UTC, timezone.utc)
    i, j = index.get(t0), index.get(t1)
    if i is None or j is None:
        return None
    b0, b1 = bars[i], bars[j]
    entry = execution_price(b0.open, Side.LONG, _spread(b0, costs), costs.slippage)
    exit_ = execution_price(b1.open, Side.SHORT, _spread(b1, costs), costs.slippage)
    gross = exit_ - entry
    cost = abs(costs.commission)
    return Trade(Side.LONG, t0, t1, entry, exit_, gross, cost, gross - cost,
                 mid_entry=b0.open, mid_exit=b1.open, exit_reason="time")


def net_bps(t: Trade) -> float:
    return t.net_pnl / t.entry_price * 1e4


def gross_bps(t: Trade) -> float:
    return (t.mid_exit - t.mid_entry) / t.mid_entry * 1e4


def stressed(bars: Sequence[Bar], costs: ExecutionCosts, k: float = STRESS) -> tuple[list[Bar], ExecutionCosts]:
    s_bars = [replace(b, spread=b.spread * k) if b.spread is not None else b for b in bars]
    return s_bars, replace(costs, spread=costs.spread * k, slippage=costs.slippage * k, commission=costs.commission * k)


# --- statistics ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Sample:
    n: int
    mean: float
    sd: float
    t: float

    @classmethod
    def of(cls, xs: Sequence[float]) -> "Sample":
        n = len(xs)
        if n < 2:
            return cls(n, mean(xs) if xs else 0.0, 0.0, 0.0)
        m, sd = mean(xs), stdev(xs)
        return cls(n, m, sd, m / (sd / math.sqrt(n)) if sd > 0 else 0.0)


def welch_t(a: Sequence[float], b: Sequence[float]) -> float:
    sa, sb = Sample.of(a), Sample.of(b)
    se = math.sqrt(sa.sd ** 2 / sa.n + sb.sd ** 2 / sb.n) if sa.n > 1 and sb.n > 1 else 0.0
    return (sa.mean - sb.mean) / se if se > 0 else 0.0


@dataclass
class Evaluation:
    period: tuple[date, date]
    calendar_events: int
    trades: list[Trade]
    placebo: list[Trade]
    stressed: list[Trade]
    net: Sample
    gross: Sample
    placebo_gross: Sample
    placebo_diff: float
    placebo_welch_t: float
    stress_net: Sample
    years: dict[int, dict]
    counted_years: list[int]
    year_share_positive: float
    median_year: float
    achieved_mde_bps: float | None
    month_end_split: dict
    qualified: bool
    failures: list[str]


def evaluate(bars: Sequence[Bar], period: tuple[date, date], closures: frozenset[date], costs: ExecutionCosts = COSTS,
             excluded: tuple[date, date] | None = EXCLUDED) -> Evaluation:
    index = {b.timestamp: i for i, b in enumerate(bars)}

    def keep(d: date) -> bool:
        return excluded is None or not excluded[0] <= d <= excluded[1]

    g_days = [d for d in gotobi_days(*period, closures) if keep(d)]
    p_days = [d for d in placebo_days(*period, closures, g_days) if keep(d)]
    trades = [t for d in g_days if (t := day_trade(bars, index, d, costs)) is not None]
    placebo = [t for d in p_days if (t := day_trade(bars, index, d, costs)) is not None]
    s_bars, s_costs = stressed(bars, costs)
    s_trades = [t for d in g_days if (t := day_trade(s_bars, index, d, s_costs)) is not None]
    net, gross = Sample.of([net_bps(t) for t in trades]), Sample.of([gross_bps(t) for t in trades])
    p_gross = Sample.of([gross_bps(t) for t in placebo])
    diff = gross.mean - p_gross.mean
    wt = welch_t([gross_bps(t) for t in trades], [gross_bps(t) for t in placebo])
    by_year: dict[int, list[float]] = defaultdict(list)
    for t in trades:
        by_year[t.entry_time.year].append(net_bps(t))
    years = {y: {"trades": len(v), "net_bps": mean(v)} for y, v in sorted(by_year.items())}
    counted = [y for y, v in years.items() if v["trades"] >= MIN_YEAR_EVENTS]
    share = sum(1 for y in counted if years[y]["net_bps"] > 0) / len(counted) if counted else 0.0
    med = median(years[y]["net_bps"] for y in counted) if counted else 0.0
    stress_net = Sample.of([net_bps(t) for t in s_trades])
    month_end = [t for t in trades if t.entry_time.day >= 26]  # 30th events (a rolled 25th stays <= 25)
    other = [t for t in trades if t not in month_end]
    split = {"month_end_30": Sample.of([net_bps(t) for t in month_end]), "days_5_to_25": Sample.of([net_bps(t) for t in other])}
    fails = []
    if net.mean <= 0 or net.t < MIN_T:
        fails.append(f"net {net.mean:+.2f} bps, t {net.t:+.2f} (need > 0 and t >= {MIN_T})")
    if diff <= 0 or wt < PLACEBO_MIN_T:
        fails.append(f"placebo difference {diff:+.2f} bps, Welch t {wt:+.2f} (need > 0 and t >= {PLACEBO_MIN_T})")
    if share < MIN_YEAR_SHARE:
        fails.append(f"positive years {share:.0%} < {MIN_YEAR_SHARE:.0%}")
    if med <= 0:
        fails.append(f"median year {med:+.2f} <= 0")
    if stress_net.mean <= 0:
        fails.append(f"net at {STRESS:g}x costs {stress_net.mean:+.2f} <= 0")
    if net.n < MIN_TRADES:
        fails.append(f"trades {net.n} < {MIN_TRADES}")
    mde = MDE_MULTIPLIER * net.sd / math.sqrt(net.n) if net.n > 1 else None
    return Evaluation(period, len(g_days), trades, placebo, s_trades, net, gross, p_gross, diff, wt, stress_net,
                      years, counted, share, med, mde, split, not fails, fails)


# --- data and run ---------------------------------------------------------------------------------


def install_csv(src: str | Path, out_dir: str | Path = DATA_DIR, expected: str = CSV_SHA256) -> Path:
    """Refuses any file that is not byte-identical to the frozen one."""
    digest = sha256_file(src)
    if digest != expected:
        raise ValueError(f"csv sha256 {digest} != frozen {expected}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / CSV_NAME
    shutil.copyfile(src, target)
    return target


def long_gaps(bars: Sequence[Bar], limit: timedelta = MAX_GAP) -> list[tuple[datetime, datetime]]:
    return [(a.timestamp, b.timestamp) for a, b in zip(bars, bars[1:]) if b.timestamp - a.timestamp > limit]


def check_gaps(bars: Sequence[Bar]) -> None:
    """Only the one documented gap may exceed the frozen 4-day limit."""
    gaps = long_gaps(bars)
    if gaps != [DOCUMENTED_GAP]:
        raise ValueError(f"undocumented data gaps: {gaps}")


def load_bars(data_dir: str = DATA_DIR) -> list[Bar]:
    path = Path(data_dir) / CSV_NAME
    if sha256_file(path) != CSV_SHA256:
        raise ValueError("installed csv does not match the frozen sha256")
    span = DOCUMENTED_GAP[1] - DOCUMENTED_GAP[0]
    bars = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ), max_gap=span).bars
    check_gaps(bars)
    return bars


def run(bars: Sequence[Bar], closures: frozenset[date] | None = None) -> dict:
    closures = closures if closures is not None else load_closures()
    primary = evaluate(bars, PRIMARY, closures)
    subs = [evaluate(bars, p, closures) for p in SUBPERIODS]
    return {"primary": primary, "subperiods": subs, "qualified": primary.qualified, "failures": primary.failures,
            "data": f"{len(bars)} bars, {bars[0].timestamp:%Y-%m-%d %H:%M} to {bars[-1].timestamp:%Y-%m-%d %H:%M} UTC"}


def _row(name: str, e: Evaluation) -> str:
    return (f"| {name} | {e.period[0]} to {e.period[1]} | {e.calendar_events} | {e.net.n} | {e.gross.mean:+.2f} | {e.net.mean:+.2f} | "
            f"{e.net.t:+.2f} | {e.placebo_gross.n} | {e.placebo_gross.mean:+.2f} | {e.placebo_diff:+.2f} | {e.placebo_welch_t:+.2f} | "
            f"{e.stress_net.mean:+.2f} | {e.year_share_positive:.0%} | {e.median_year:+.2f} | "
            f"{'-' if e.achieved_mde_bps is None else format(e.achieved_mde_bps, '.2f')} |")


def render(res: dict) -> str:
    p = res["primary"]
    L = [
        "# USDJPY Gotobi-Day Tokyo Fix v1",
        "",
        f"Specification (frozen before this run, version {SPEC_VERSION}): `{SPEC_PATH}`. Long USDJPY 00:00-01:00 UTC (09:00-10:00 JST) "
        "on gotobi days; placebo = the same trade on non-gotobi Japanese bank business days. "
        f"Days {EXCLUDED[0]} to {EXCLUDED[1]} (data gap) excluded. Both t-gates use t >= {MIN_T} (Bonferroni, family of 2).",
        "",
        f"## Primary outcome: **{'QUALIFIED' if res['qualified'] else 'NOT QUALIFIED'}**",
        "",
        f"Failures: {'; '.join(res['failures']) or 'none'}",
        "",
        "| sample | period | calendar events | trades | gross bps | net bps | t | placebo days | placebo gross | gotobi - placebo (gross) | Welch t | net 2x costs | positive years | median year | achieved resolution |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        _row("primary (qualification)", p),
        *[_row(f"sub-period {i + 1} (descriptive only)", e) for i, e in enumerate(res["subperiods"])],
        "",
        "Sub-period 1 (2019-06 to 2020) was untouched by any earlier test; sub-period 2 (2021-2026) was read by test 17 (other hours).",
        f"Achieved resolution = {MDE_MULTIPLIER:.4f} x SE of net bps; descriptive only (design MDE 1.68 bps central at t >= 2.28, assumption-based).",
    ]
    for name, e in (("primary", p),):
        L += ["", f"## Per year ({name}; years with < {MIN_YEAR_EVENTS} events are not counted)", "",
              "| year | trades | net bps | counted |", "|---|---|---|---|"]
        for y, v in e.years.items():
            L.append(f"| {y} | {v['trades']} | {v['net_bps']:+.2f} | {'yes' if y in e.counted_years else 'no'} |")
        ms = e.month_end_split
        L += ["", f"Descriptive split ({name}): 30th events {ms['month_end_30'].n} trades, {ms['month_end_30'].mean:+.2f} bps; "
              f"5th-25th events {ms['days_5_to_25'].n} trades, {ms['days_5_to_25'].mean:+.2f} bps."]
    L += ["", f"Data: {SYMBOL} {res['data']}."]
    return "\n".join(L) + "\n"


def results_json(res: dict) -> dict:
    def ev(e: Evaluation) -> dict:
        out = {k: v for k, v in e.__dict__.items() if k not in ("trades", "placebo", "stressed")}
        out["period"] = [d.isoformat() for d in e.period]
        return out
    return to_jsonable({"schema_version": SCHEMA_VERSION, "spec": SPEC_PATH, "symbol": SYMBOL,
                        "qualified": res["qualified"], "failures": res["failures"],
                        "spec_version": SPEC_VERSION, "primary": ev(res["primary"]),
                        "subperiods": [ev(e) for e in res["subperiods"]], "data": res["data"]})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", help="verify and install the frozen CSV before running")
    parser.add_argument("--report")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    if args.csv:
        install_csv(args.csv)
    res = run(load_bars())
    text = render(res)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(results_json(res), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
