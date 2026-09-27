from qfx.risk import RiskEngine


def test_invalid_setup_is_rejected():
    result = RiskEngine().evaluate(False, False, 0.0, 0.0)
    assert not result.allowed
    assert result.risk_fraction == 0.0


def test_abnormal_volatility_reduces_risk():
    result = RiskEngine().evaluate(True, True, 0.0, 0.0)
    assert result.allowed
    assert result.risk_fraction == 0.001


def test_open_risk_limit_is_hard():
    result = RiskEngine().evaluate(True, False, 0.01, 0.0)
    assert not result.allowed


def test_daily_loss_limit_is_hard():
    result = RiskEngine().evaluate(True, False, 0.0, 0.015)
    assert not result.allowed
