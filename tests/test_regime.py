import pytest

from qfx.models import Regime
from qfx.regime import classify_regime


def test_short_history_is_unknown():
    assert classify_regime([100]) is Regime.UNKNOWN


def test_compression():
    assert classify_regime([100, 100.1]) is Regime.COMPRESSION


def test_trend_up():
    assert classify_regime([100, 101]) is Regime.TREND_UP


def test_trend_down():
    assert classify_regime([100, 99]) is Regime.TREND_DOWN


def test_invalid_price():
    with pytest.raises(ValueError):
        classify_regime([0, 1])
