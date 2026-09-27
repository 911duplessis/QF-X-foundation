from qfx.expectancy import EdgeEstimate
from qfx.models import Candle, DecisionState
from qfx.pipeline import AccountState, decide

GOOD_EDGE = EdgeEstimate(0.5, 2.0, 1.0, 0.1, 500)


def trend(n=10, start=100.0, step=0.2):
    out = []
    for i in range(n):
        c = start + step * i
        out.append(Candle(f"2026-01-01T{i:02d}:00:00Z", c - step / 2, c + 0.3, c - 0.3, c))
    return out


def test_defaults_to_no_trade_on_bad_data():
    result = decide("EURUSD", [], GOOD_EDGE)
    assert result.state.decision is DecisionState.NO_TRADE
    assert not result.risk.allowed


def test_no_edge_is_watch_only():
    result = decide("EURUSD", trend(), None)
    assert result.state.decision is DecisionState.WATCH
    assert result.risk.risk_fraction == 0.0


def test_qualified_path():
    result = decide("EURUSD", trend(), GOOD_EDGE)
    assert result.state.decision is DecisionState.QUALIFIED
    assert result.risk.risk_fraction == 0.0025


def test_risk_limits_override_edge():
    result = decide("EURUSD", trend(), GOOD_EDGE, AccountState(daily_loss_fraction=0.02))
    assert result.state.decision is DecisionState.NO_TRADE
    assert result.state.reason == "daily_loss_limit"


def test_extreme_volatility_blocks():
    result = decide("EURUSD", trend(), GOOD_EDGE, vol_history=[0.0] * 100)
    assert result.state.decision is DecisionState.NO_TRADE
    assert result.state.reason == "volatility_outside_validated_bounds"
