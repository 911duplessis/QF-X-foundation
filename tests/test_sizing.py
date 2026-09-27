import pytest

from qfx.sizing import DEFAULT_SPECS, position_size


def test_eurusd_sizing():
    # 100k * 0.25% = 250 risk; 20 pips = 0.0020 * 100k = 200 per lot -> 1.25 lots
    assert position_size(100_000, 0.0025, 1.1000, 1.0980, DEFAULT_SPECS["EURUSD"]) == pytest.approx(1.25)


def test_rounds_down_never_up():
    lots = position_size(100_000, 0.0025, 1.1000, 1.0977, DEFAULT_SPECS["EURUSD"])
    loss = lots * 0.0023 * 100_000
    assert loss <= 250


def test_costs_reduce_size():
    spec = DEFAULT_SPECS["EURUSD"]
    assert position_size(100_000, 0.0025, 1.1, 1.098, spec, cost_per_lot=7) < position_size(
        100_000, 0.0025, 1.1, 1.098, spec
    )


def test_below_min_lot_returns_zero():
    assert position_size(1_000, 0.001, 2000, 1950, DEFAULT_SPECS["XAUUSD"]) == 0.0


def test_capped_at_max_lot():
    assert position_size(1e9, 0.0025, 1.1, 1.0999, DEFAULT_SPECS["EURUSD"]) == 100.0


def test_zero_stop_distance_rejected():
    with pytest.raises(ValueError):
        position_size(100_000, 0.0025, 1.1, 1.1, DEFAULT_SPECS["EURUSD"])
