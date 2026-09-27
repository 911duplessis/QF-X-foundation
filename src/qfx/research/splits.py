"""Chronological splits. Time-series observations are never shuffled."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    name: str
    start: int
    end: int  # exclusive


def chronological_split(n: int, train: float = 0.6, validation: float = 0.2) -> list[Segment]:
    if n < 3:
        raise ValueError("Need at least three observations")
    if train <= 0 or validation <= 0 or train + validation >= 1:
        raise ValueError("Require train > 0, validation > 0 and train + validation < 1")
    a = int(n * train)
    b = int(n * (train + validation))
    return [Segment("train", 0, a), Segment("validation", a, b), Segment("test", b, n)]
