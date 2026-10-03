"""A forecast of one user's wallet balance for the days after "today"."""
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ForecastPoint:
    """The forecast for one future day, in taka.

    The five balance levels describe a range: the real balance should be under
    p10 about 1 time in 10, under p50 half the time, and under p90 about 9 times in 10.
    """
    day: date
    p10: float  # cautious
    p25: float
    p50: float  # most likely
    p75: float
    p90: float  # optimistic
    cautious_income: float  # money expected to arrive between today and this day, at a cautious level

    def __post_init__(self):
        levels = (self.p10, self.p25, self.p50, self.p75, self.p90)
        if any(low > high for low, high in zip(levels, levels[1:])):
            raise ValueError(f"forecast levels for {self.day} are out of order: {levels}")
        if self.p10 < 0 or self.cautious_income < 0:
            raise ValueError(f"a balance or an income cannot be negative ({self.day})")

    @property
    def levels(self) -> dict[float, float]:
        """Chance of being under each level -> the level."""
        return {0.10: self.p10, 0.25: self.p25, 0.50: self.p50, 0.75: self.p75, 0.90: self.p90}


@dataclass(frozen=True)
class Forecast:
    user_id: str
    as_of: date  # "today": the last day whose transactions were used
    balance: float  # wallet balance at the end of today
    typical_daily_spending: float  # the user's average daily money out over the last 60 days
    points: tuple[ForecastPoint, ...]  # one per day, starting the day after today

    def __post_init__(self):
        if not self.points:
            raise ValueError("a forecast needs at least one day")
        expected = [self.as_of + timedelta(days=i) for i in range(1, len(self.points) + 1)]
        if [point.day for point in self.points] != expected:
            raise ValueError("forecast days must follow each other, starting the day after today")
        if self.typical_daily_spending <= 0:
            raise ValueError("typical daily spending must be positive")
