import pytest

from qfx.models import Candle, DecisionState, MarketState, Regime


def test_valid_candle():
    Candle("2026-01-01T00:00:00Z", 100, 105, 99, 103).validate()


def test_invalid_candle():
    with pytest.raises(ValueError):
        Candle("2026-01-01T00:00:00Z", 100, 98, 99, 97).validate()


def test_market_state_defaults_to_no_trade():
    state = MarketState("EURUSD", Regime.UNKNOWN)
    assert state.decision is DecisionState.NO_TRADE
