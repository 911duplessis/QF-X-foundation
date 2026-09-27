from datetime import datetime, timezone

from qfx.backtest.csv_loader import load_csv
from qfx.backtest.engine import run_backtest
from qfx.backtest.metrics import summarize
from qfx.backtest.types import ExecutionCosts, Side


def test_backtest_applies_delay_and_costs(tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text("timestamp,open,high,low,close\\n" + "2026-01-01T00:00:00+00:00,100,101,99,100\\n" + "2026-01-01T00:01:00+00:00,100,102,99,101\\n" + "2026-01-01T00:02:00+00:00,101,103,100,102\\n" + "2026-01-01T00:03:00+00:00,102,104,101,103\\n")
    bars = load_csv(path)

    def signal(bars, i):
        if i == 0:
            return Side.LONG
        if i == 2:
            return None
        return None

    trades = run_backtest(bars, signal, costs=ExecutionCosts(spread=0.2, commission=0.1, slippage=0.05, delay_bars=1))
    assert len(trades) == 1
    assert trades[0].entry_time == bars[1].timestamp
    assert trades[0].exit_time == bars[2].timestamp
    assert trades[0].net_pnl < trades[0].gross_pnl


def test_metrics():
    from qfx.backtest.types import Trade
    t1 = Trade(Side.LONG, datetime.now(timezone.utc), datetime.now(timezone.utc), 100, 102, 2, 0.1, 1.9)
    t2 = Trade(Side.SHORT, datetime.now(timezone.utc), datetime.now(timezone.utc), 100, 101, -1, 0.1, -1.1)
    summary = summarize([t1, t2])
    assert summary["trades"] == 2
    assert summary["win_rate"] == 0.5
    assert summary["profit_factor"] > 1
