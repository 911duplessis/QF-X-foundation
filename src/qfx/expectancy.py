"""Expected value gate: EV = P(win) * AvgWin - P(loss) * AvgLoss - Costs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeEstimate:
    win_rate: float
    avg_win: float
    avg_loss: float
    costs: float
    sample_size: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.win_rate <= 1.0:
            raise ValueError("Win rate must be within [0, 1]")
        if self.avg_win < 0 or self.avg_loss < 0 or self.costs < 0:
            raise ValueError("Payoffs and costs must be non-negative magnitudes")
        if self.sample_size < 0:
            raise ValueError("Sample size must be non-negative")

    @property
    def expected_value(self) -> float:
        return self.win_rate * self.avg_win - (1.0 - self.win_rate) * self.avg_loss - self.costs


def passes_ev_gate(estimate: EdgeEstimate, min_ev: float = 0.0, min_sample: int = 100) -> tuple[bool, str]:
    """Reject thin samples before looking at EV: a small sample cannot prove edge."""
    if estimate.sample_size < min_sample:
        return False, "insufficient_sample"
    if estimate.expected_value <= min_ev:
        return False, "non_positive_edge_after_costs"
    return True, "positive_edge_after_costs"
