import pytest

from qfx.volatility import realized_volatility, true_ranges


def test_true_ranges():
    assert true_ranges([10, 12], [9, 10], [9.5, 11]) == [1, 2.5]


def test_true_ranges_requires_equal_lengths():
    with pytest.raises(ValueError):
        true_ranges([10], [9, 8], [9.5])


def test_realized_volatility_requires_history():
    with pytest.raises(ValueError):
        realized_volatility([100])
