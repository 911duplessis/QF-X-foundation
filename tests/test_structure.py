from qfx.structure import (
    LiquidityPool,
    SwingKind,
    break_of_structure,
    detect_sweep,
    equal_levels,
    find_swings,
    known_swings,
)

HIGHS = [1, 2, 5, 2, 1, 2, 5, 2, 1]
LOWS = [0.5, 1, 4, 1, 0.2, 1, 4, 1, 0.5]


def test_swings_found_with_confirmation_delay():
    swings = find_swings(HIGHS, LOWS, lookback=2)
    highs = [s for s in swings if s.kind is SwingKind.HIGH]
    assert [(s.index, s.confirmed_at) for s in highs] == [(2, 4), (6, 8)]
    lows = [s for s in swings if s.kind is SwingKind.LOW]
    assert [s.index for s in lows] == [4]


def test_no_look_ahead():
    swings = find_swings(HIGHS, LOWS, lookback=2)
    assert all(s.confirmed_at > s.index for s in swings)
    assert [s.index for s in known_swings(swings, as_of=3)] == []
    assert 2 in [s.index for s in known_swings(swings, as_of=4)]


def test_last_bars_cannot_be_swings():
    swings = find_swings(HIGHS, LOWS, lookback=2)
    assert all(s.index < len(HIGHS) - 2 for s in swings)


def test_break_of_structure():
    swings = find_swings(HIGHS, LOWS, lookback=2)
    closes = [1, 1, 1, 1, 1, 6, 1, 1, 1]
    assert break_of_structure(closes, swings, 5) is SwingKind.HIGH
    closes[5] = 0.1
    # Swing low at bar 4 is not confirmed until bar 6: no break is knowable yet.
    assert break_of_structure(closes, swings, 5) is None
    closes[7] = 0.1
    assert break_of_structure(closes, swings, 7) is SwingKind.LOW


def test_equal_highs_form_pool():
    swings = find_swings(HIGHS, LOWS, lookback=2)
    pools = equal_levels(swings, tolerance=0.01)
    assert pools == [LiquidityPool(SwingKind.HIGH, 5, (2, 6))]


def test_sweep_requires_close_back_inside():
    pool = LiquidityPool(SwingKind.HIGH, 5, (2, 6))
    assert detect_sweep(5.5, 4.5, 4.8, 9, pool) is not None
    assert detect_sweep(5.5, 4.5, 5.2, 9, pool) is None
    assert detect_sweep(5.5, 4.5, 4.8, 6, pool) is None
