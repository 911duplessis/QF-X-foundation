"""Gate 0 audit for MT5 exports.

    python -m qfx.backtest.audit data/mt5/*.csv --tz Europe/Athens --interval-hours 1
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from zoneinfo import ZoneInfo

from .mt5 import DEFAULT_SERVER_TZ, load_mt5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--tz", default=DEFAULT_SERVER_TZ, help="Broker server timezone (IANA name)")
    parser.add_argument("--interval-hours", type=float, default=1.0)
    parser.add_argument("--max-gap-days", type=float, default=4.0)
    args = parser.parse_args(argv)

    failed = False
    for path in args.paths:
        result = load_mt5(
            path,
            ZoneInfo(args.tz),
            interval=timedelta(hours=args.interval_hours),
            max_gap=timedelta(days=args.max_gap_days),
            validate=False,
        )
        r = result.report
        span = f"{result.bars[0].timestamp:%Y-%m-%d %H:%M} -> {result.bars[-1].timestamp:%Y-%m-%d %H:%M} UTC" if result.bars else "-"
        status = "PASS" if r.passed else "FAIL"
        print(f"{status} {result.symbol}: {r.bars} bars, {span}, trimmed_prefix={r.trimmed_prefix}, dst_dropped={result.dst_collisions_dropped}, gaps={r.gap_count}, max_gap={r.max_gap}")
        for issue in r.issues[:10]:
            print(f"    {issue}")
        failed |= not r.passed
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
