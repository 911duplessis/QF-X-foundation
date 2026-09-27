"""Baseline experiment: trend continuation on the committed MT5 H1 exports.

    python -m qfx.research.baseline [--report docs/results/baseline_trend_continuation.md]

Protocol (docs/VALIDATION_PROTOCOL.md, Gates 2-5 lite):
- chronological 60/20/20 train/validation/test split, never shuffled;
- parameters chosen on train only (highest mean net bps, min trade count);
- validation and test reported once for the chosen parameters;
- cost stress: test re-run with doubled spread and slippage.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

from ..backtest.engine import run_backtest
from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5
from ..backtest.types import Bar, ExecutionCosts
from .evaluation import Stats, trade_stats
from .hypotheses import TrendParams, trend_continuation
from .splits import Segment, chronological_split

# Research cost assumptions in price units (spread floor, per-side slippage).
# Per-bar MT5 spread is used when wider. Commission assumed 0 (spread-only CFD).
COSTS: dict[str, ExecutionCosts] = {
    "EURUSD": ExecutionCosts(spread=0.00010, slippage=0.00002),
    "XAUUSD": ExecutionCosts(spread=0.25, slippage=0.05),
    "BTCUSD": ExecutionCosts(spread=30.0, slippage=5.0),
}
GRID = {"lookback": (24, 72, 168), "entry_z": (1.0, 1.5, 2.0)}
MIN_TRAIN_TRADES = 30
MIN_TEST_TRADES = 30
MIN_TEST_T = 2.0


@dataclass(frozen=True)
class SegmentResult:
    segment: str
    stats: Stats


@dataclass(frozen=True)
class SymbolResult:
    symbol: str
    params: TrendParams
    train_grid: list[tuple[TrendParams, Stats]]
    segments: list[SegmentResult]
    stressed_test: Stats


def _frictionless(bars: list[Bar]) -> list[Bar]:
    return [replace(b, spread=None) for b in bars]


def evaluate(bars: list[Bar], clean: list[Bar], seg: Segment, params: TrendParams, costs: ExecutionCosts) -> Stats:
    part = bars[seg.start : seg.end]
    hours = (part[-1].timestamp - part[0].timestamp).total_seconds() / 3600
    trades = run_backtest(part, trend_continuation(bars, params, seg.start), costs=costs)
    ideal = run_backtest(clean[seg.start : seg.end], trend_continuation(bars, params, seg.start), costs=ExecutionCosts())
    return trade_stats(trades, ideal, hours)


def run_symbol(symbol: str, bars: list[Bar], costs: ExecutionCosts) -> SymbolResult:
    clean = _frictionless(bars)
    train, validation, test = chronological_split(len(bars))
    grid = []
    for lookback, entry_z in product(GRID["lookback"], GRID["entry_z"]):
        params = TrendParams(lookback=lookback, entry_z=entry_z)
        grid.append((params, evaluate(bars, clean, train, params, costs)))
    eligible = [g for g in grid if g[1].trades >= MIN_TRAIN_TRADES] or grid
    chosen = max(eligible, key=lambda g: g[1].net_bps)[0]
    segments = [SegmentResult(s.name, evaluate(bars, clean, s, chosen, costs)) for s in (train, validation, test)]
    stressed = replace(costs, spread=costs.spread * 2, slippage=costs.slippage * 2)
    stressed_bars = [replace(b, spread=b.spread * 2) if b.spread is not None else b for b in bars]
    stressed_test = evaluate(stressed_bars, clean, test, chosen, stressed)
    return SymbolResult(symbol, chosen, grid, segments, stressed_test)


def verdict(r: SymbolResult) -> tuple[bool, str]:
    """An edge qualifies only if it holds out of sample in both unseen
    segments, is statistically distinguishable from zero on a usable sample,
    and survives doubled costs."""
    seg = {s.segment: s.stats for s in r.segments}
    val, test = seg["validation"], seg["test"]
    failures = []
    if val.net_bps <= 0:
        failures.append("validation net <= 0")
    if test.net_bps <= 0:
        failures.append("test net <= 0")
    if test.trades < MIN_TEST_TRADES:
        failures.append(f"test trades {test.trades} < {MIN_TEST_TRADES}")
    if test.t_stat < MIN_TEST_T:
        failures.append(f"test t {test.t_stat:+.2f} < {MIN_TEST_T}")
    if r.stressed_test.net_bps <= 0:
        failures.append("negative at 2x costs")
    return (not failures, "; ".join(failures) or "all criteria met")


def _row(label: str, s: Stats) -> str:
    return (
        f"| {label} | {s.trades} | {s.net_bps:+.1f} | {s.median_bps:+.1f} | {s.gross_bps:+.1f} | {s.cost_bps:.1f} | "
        f"{s.win_rate:.0%} | {s.profit_factor:.2f} | {s.t_stat:+.2f} | {s.max_drawdown_bps:.0f} | {s.avg_hold_hours:.0f} | {s.exposure:.0%} |"
    )


HEADER = (
    "| | trades | net bps/trade | median | gross bps | cost bps | win | PF | t | max DD bps | hold h | exposure |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|"
)


def render(results: list[SymbolResult], spans: dict[str, str]) -> str:
    lines = ["# Baseline: trend continuation (H1)", "", __doc__.split("Protocol", 1)[1].join(["Protocol", ""]).strip(), ""]
    lines += [
        f"Qualification rule: validation and test net > 0, test t >= {MIN_TEST_T}, "
        f"test trades >= {MIN_TEST_TRADES}, and net > 0 at 2x costs.",
        "",
        "| symbol | qualified | reason |",
        "|---|---|---|",
        *[f"| {r.symbol} | {'YES' if verdict(r)[0] else 'NO'} | {verdict(r)[1]} |" for r in results],
        "",
    ]
    for r in results:
        p = r.params
        lines += [
            f"## {r.symbol}",
            "",
            f"Data: {spans[r.symbol]}. Chosen on train: lookback={p.lookback}, entry_z={p.entry_z}, exit_z={p.exit_z}.",
            "",
            HEADER,
            *[_row(s.segment, s.stats) for s in r.segments],
            _row("test @ 2x costs", r.stressed_test),
            "",
            "<details><summary>Train grid</summary>",
            "",
            HEADER,
            *[_row(f"L={gp.lookback} z={gp.entry_z}", gs) for gp, gs in r.train_grid],
            "",
            "</details>",
            "",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/mt5")
    parser.add_argument("--report", default=None)
    args = parser.parse_args(argv)
    results, spans = [], {}
    for path in sorted(Path(args.data).glob("*.csv")):
        loaded = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ))
        if loaded.symbol not in COSTS:
            continue
        b = loaded.bars
        spans[loaded.symbol] = f"{len(b)} bars, {b[0].timestamp:%Y-%m-%d} to {b[-1].timestamp:%Y-%m-%d} UTC"
        results.append(run_symbol(loaded.symbol, b, COSTS[loaded.symbol]))
    text = render(results, spans)
    print(text)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
