"""A warning that the wallet balance is likely to fall under the safety cushion."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Alert:
    day: date  # the first day the chance of being under the cushion reaches the alert level
    chance: float  # the highest chance of being under the cushion on any day in the warning window, 0 to 1
    gap: float  # taka: how far the cautious forecast falls under the cushion at its lowest
    cushion: float  # taka: the safety cushion the forecast was compared with

    def __post_init__(self):
        if not 0 < self.chance <= 1:
            raise ValueError("chance must be above 0 and at most 1")
        if self.gap < 0 or self.cushion <= 0:
            raise ValueError("gap cannot be negative and the cushion must be positive")
