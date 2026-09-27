import pytest

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


from qfx.risk import correlated_risk


def test_data_failure_blocks_everything():
    assert RiskEngine().evaluate(True, False, 0.0, 0.0, data_ok=False).reason == "data_integrity_failure"


def test_marginal_setup_gets_zero():
    result = RiskEngine().evaluate(True, False, 0.0, 0.0, marginal_setup=True)
    assert not result.allowed and result.risk_fraction == 0.0


def test_requested_risk_is_capped():
    result = RiskEngine().evaluate(True, False, 0.0, 0.0, requested_fraction=0.02)
    assert result.risk_fraction == 0.0035


def test_kill_switches():
    engine = RiskEngine()
    assert engine.evaluate(True, False, 0.0, 0.0, spread_anomaly=True).reason == "spread_slippage_anomaly"
    assert engine.evaluate(True, False, 0.0, 0.0, drawdown_fraction=0.06).reason == "drawdown_limit"
    assert engine.evaluate(True, False, 0.0, 0.0, consecutive_losses=4).reason == "consecutive_loss_limit"


def test_correlated_exposure_shares_limit():
    engine = RiskEngine()
    reduced = engine.evaluate(True, False, 0.005, 0.0, correlated_open_risk=0.004)
    assert reduced.allowed and reduced.risk_fraction == pytest.approx(0.001)
    blocked = engine.evaluate(True, False, 0.005, 0.0, correlated_open_risk=0.005)
    assert not blocked.allowed


def test_correlated_risk_weights_by_correlation():
    corr = {("EURUSD", "XAUUSD"): 0.8, ("EURUSD", "BTCUSD"): 0.3}
    open_positions = {"XAUUSD": 0.0025, "BTCUSD": 0.0025, "EURUSD": 0.0025}
    assert correlated_risk("EURUSD", open_positions, corr) == pytest.approx(0.002)
