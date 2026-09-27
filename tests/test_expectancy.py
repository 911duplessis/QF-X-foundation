import pytest

from qfx.expectancy import EdgeEstimate, passes_ev_gate


def test_expected_value_includes_costs():
    edge = EdgeEstimate(0.5, 2.0, 1.0, 0.1, 500)
    assert edge.expected_value == pytest.approx(0.4)


def test_costs_can_destroy_edge():
    ok, reason = passes_ev_gate(EdgeEstimate(0.5, 1.1, 1.0, 0.1, 500))
    assert not ok and reason == "non_positive_edge_after_costs"


def test_thin_sample_rejected_even_with_edge():
    ok, reason = passes_ev_gate(EdgeEstimate(0.9, 3.0, 1.0, 0.0, 20))
    assert not ok and reason == "insufficient_sample"


def test_invalid_win_rate():
    with pytest.raises(ValueError):
        EdgeEstimate(1.2, 1.0, 1.0, 0.0, 100)
