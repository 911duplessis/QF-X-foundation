from datetime import datetime, timedelta, timezone

import pytest

from qfx.backtest.bracket import BracketOrder, run_bracket_backtest
from qfx.backtest.types import Bar, ExecutionCosts, Side

T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)


def bars(*ohlc, spread=None):
    return [Bar(T0 + timedelta(hours=i), o, h, l, c, spread=spread) for i, (o, h, l, c) in enumerate(ohlc)]


def once(order, at=0):
    return lambda view, i: order if i == at else None


FLAT = (100, 100.5, 99.5, 100)


def test_long_target_hit_after_delayed_entry():
    b = bars(FLAT, (100, 100.5, 99.5, 100), (100, 102.5, 99.8, 102), FLAT)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 99.0, 2.0, 48)))[0]
    assert t.entry_time == b[1].timestamp  # signal on bar 0 fills at bar 1 open
    assert (t.exit_reason, t.exit_price, t.exit_time) == ("target", 102.0, b[2].timestamp)
    assert t.r_multiple == pytest.approx(2.0)


def test_stop_first_when_same_bar_touches_both():
    b = bars(FLAT, FLAT, (100, 103, 98.5, 101), FLAT)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 99.0, 2.0, 48)))[0]
    assert t.exit_reason == "stop" and t.exit_price == 99.0
    assert t.r_multiple == pytest.approx(-1.0)


def test_stop_can_trigger_on_entry_bar():
    b = bars(FLAT, (100, 100.2, 98.0, 98.5), FLAT)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 99.0, 1.0, 48)))[0]
    assert t.exit_reason == "stop" and t.exit_time == b[1].timestamp


def test_gap_through_stop_fills_at_open():
    b = bars(FLAT, FLAT, (97, 97.5, 96.5, 97), FLAT)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 99.0, 2.0, 48)))[0]
    assert t.exit_reason == "stop" and t.exit_price == 97.0
    assert t.r_multiple == pytest.approx(-3.0)


def test_short_mirror_and_costs_paid_both_sides():
    b = bars(FLAT, FLAT, (100, 100.2, 97.9, 98), FLAT)
    costs = ExecutionCosts(spread=0.2, slippage=0.05)
    t = run_bracket_backtest(b, once(BracketOrder(Side.SHORT, 101.0, 2.0, 48)), costs=costs)[0]
    # entry fill = 100 - 0.1 - 0.05 = 99.85; risk = 1.15; target = 97.55 (not reached: low 97.9)
    assert t.entry_price == pytest.approx(99.85)
    assert t.exit_reason == "end_of_data"
    assert t.mid_entry == 100 and t.gross_pnl < (t.mid_entry - t.mid_exit)


def test_entry_skipped_when_fill_beyond_stop():
    b = bars(FLAT, (98, 98.5, 97.5, 98), FLAT)
    assert run_bracket_backtest(b, once(BracketOrder(Side.LONG, 99.0, 2.0, 48))) == []


def test_time_stop_exits_at_open():
    b = bars(FLAT, *[FLAT] * 5)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 90.0, 5.0, 3)))[0]
    assert t.exit_reason == "time" and t.exit_time == b[4].timestamp  # entry bar 1 + 3


def test_orders_ignored_while_busy_and_signal_sees_no_future():
    b = bars(*[FLAT] * 8)
    calls = []

    def sig(view, i):
        calls.append(i)
        assert len(view) == i + 1
        with pytest.raises(IndexError):
            view[i + 1]
        return BracketOrder(Side.LONG, 90.0, 5.0, 3)

    trades = run_bracket_backtest(b, sig)
    assert calls == list(range(8))  # called every bar
    assert [t.entry_time for t in trades] == [b[1].timestamp, b[5].timestamp]  # no overlap


def test_per_bar_spread_is_a_floor():
    b = bars(FLAT, FLAT, FLAT, spread=1.0)
    t = run_bracket_backtest(b, once(BracketOrder(Side.LONG, 90.0, 5.0, 48)), costs=ExecutionCosts(spread=0.1))[0]
    assert t.entry_price == pytest.approx(100.5)
