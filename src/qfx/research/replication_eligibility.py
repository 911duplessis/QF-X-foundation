"""Replication R1 eligibility (checkpoint 3). Data-quality and history checks
only: no returns, signals or strategy computation.

    python -m qfx.research.replication_eligibility <export files...> \
        --report docs/results/replication_r1_eligibility.md --json docs/results/replication_r1_eligibility.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..backtest.mt5 import DEFAULT_SERVER_TZ, load_mt5

SPEC_PATH = "docs/hypotheses/replication_r1_vol_expansion_crypto.md"
CANDIDATES = (
    "BCHUSD.m", "ETHUSD.m", "LTCUSD.m", "XRPUSD.m", "ADAUSD.m", "DOTUSD.m", "XLMUSD.m", "KSMUSD.m",
    "SOLUSD.m", "TRXUSD.m", "UNIUSD.m", "AVAXUSD.m", "DOGEUSD.m", "LINKUSD.m", "MATICUSD.m",
)
FIRST_AT_OR_BEFORE = datetime(2021, 1, 1, tzinfo=timezone.utc)
LAST_AT_OR_AFTER = datetime(2026, 8, 24, tzinfo=timezone.utc)
INTERVAL = timedelta(hours=1)
MAX_GAP = timedelta(days=4)


@dataclass(frozen=True)
class Eligibility:
    symbol: str
    file: str
    sha256: str
    eligible: bool
    reasons: tuple[str, ...]
    bars: int
    first_h1_utc: str | None
    last_h1_utc: str | None
    trimmed_prefix: int
    dst_collisions_dropped: int
    gap_count: int
    max_gap_hours: float
    gate0_issues: tuple[str, ...]


def symbol_of(path: Path) -> str:
    """``8a2cf904-ETHUSD.m_H1_...csv`` or ``ETHUSD.m_H1_...csv`` -> ``ETHUSD.m``."""
    name = path.name.split("-", 1)[1] if "-" in path.name.split("_")[0] else path.name
    return name.split("_")[0]


def check(path: str | Path) -> Eligibility:
    path = Path(path)
    symbol = symbol_of(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    reasons: list[str] = []
    if symbol not in CANDIDATES:
        reasons.append("not in the frozen candidate list")
    res = load_mt5(path, ZoneInfo(DEFAULT_SERVER_TZ), interval=INTERVAL, max_gap=MAX_GAP, validate=False)
    r, bars = res.report, res.bars
    if not r.passed:
        reasons.append("gate0 failed")
    first = bars[0].timestamp if bars else None
    last = bars[-1].timestamp if bars else None
    if first is None or first > FIRST_AT_OR_BEFORE:
        reasons.append(f"first H1 {first} after {FIRST_AT_OR_BEFORE}")
    if last is None or last < LAST_AT_OR_AFTER:
        reasons.append(f"last H1 {last} before {LAST_AT_OR_AFTER}")
    return Eligibility(
        symbol, path.name, digest, not reasons, tuple(reasons), r.bars,
        first.isoformat() if first else None, last.isoformat() if last else None,
        r.trimmed_prefix, res.dst_collisions_dropped, r.gap_count, r.max_gap.total_seconds() / 3600, tuple(r.issues[:10]),
    )


def render(results: list[Eligibility]) -> str:
    ok = [r for r in results if r.eligible]
    missing = sorted(set(CANDIDATES) - {r.symbol for r in results})
    L = [
        "# Replication R1: eligibility report (checkpoint 3)",
        "",
        f"Specification: `{SPEC_PATH}` (v2). Loader: Europe/Athens, 1h interval, 4-day max gap, D1-prefix trimming, Gate 0 unchanged. "
        f"Rule: first H1 <= {FIRST_AT_OR_BEFORE.isoformat()} and last H1 >= {LAST_AT_OR_AFTER.isoformat()}.",
        "No returns, signals or strategy computation were run to produce this report.",
        "",
        f"**Eligible: N = {len(ok)}** ({', '.join(r.symbol for r in ok) or 'none'}). "
        f"Candidates without an export: {', '.join(missing) or 'none'}.",
        "",
        "| symbol | eligible | first H1 (UTC) | last H1 (UTC) | bars | D1 prefix trimmed | DST drops | gaps | max gap (h) | reasons |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: (not x.eligible, x.symbol)):
        L.append(
            f"| {r.symbol} | {'YES' if r.eligible else 'no'} | {r.first_h1_utc} | {r.last_h1_utc} | {r.bars} | {r.trimmed_prefix} | "
            f"{r.dst_collisions_dropped} | {r.gap_count} | {r.max_gap_hours:.0f} | {'; '.join(r.reasons) or '-'} |"
        )
    L += ["", "File hashes (sha256):", ""] + [f"- `{r.sha256}` {r.file}" for r in sorted(results, key=lambda x: x.symbol)]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--report")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    results = [check(f) for f in args.files]
    text = render(results)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
