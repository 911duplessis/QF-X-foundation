from datetime import datetime, timezone

from qfx.backtest.csv_loader import load_csv
from qfx.backtest.engine import run_backtest
from qfx.backtest.metrics import summarize
from qfx.backtest.types import ExecutionCosts, Side


def test_backtest_applies_delay_and_costs(tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text("timestamp,open,high,low,close\n" + "2026-01-01T00:00:00+00:00,100,101,99,100\n" + "2026-01-01T00:01:00+00:00,100,102,99,101\n" + "2026-01-01T00:02:00+00:00,101,103,100,102\n" + "2026-01-01T00:03:00+00:00,102,104,101,103\n")
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


def _bars(n=6):
    from qfx.backtest.types import Bar
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    from datetime import timedelta
    return [Bar(start + timedelta(minutes=i), 100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(n)]


def test_zero_delay_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        ExecutionCosts(delay_bars=0)


def test_signal_cannot_see_future_bars():
    import pytest
    bars = _bars()

    def peeking(view, i):
        assert len(view) == i + 1
        with pytest.raises(IndexError):
            view[i + 1]
        return None

    assert run_backtest(bars, peeking) == []


def test_exit_respects_delay():
    bars = _bars()
    trades = run_backtest(bars, lambda v, i: Side.LONG if i == 0 else None, costs=ExecutionCosts(delay_bars=2))
    assert trades[0].entry_time == bars[2].timestamp
    assert trades[0].exit_time == bars[4].timestamp


def test_open_position_is_closed_at_end_of_data():
    bars = _bars()
    trades = run_backtest(bars, lambda v, i: Side.SHORT)
    assert len(trades) == 1
    assert trades[0].exit_time == bars[-1].timestamp
    assert trades[0].exit_price == bars[-1].close
