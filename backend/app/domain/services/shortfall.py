"""The shortfall rule: when does a forecast become a warning?

A fixed business rule, kept apart from the forecasting model. The model says
what the balance will probably be; this file decides what counts as a problem.
"""
from app.domain.entities.alert import Alert
from app.domain.entities.forecast import Forecast

CUSHION_DAYS = 1.0  # the safety cushion is this many days of the user's typical spending
WARNING_DAYS = 14  # a warning looks this many days ahead
# Warn when the chance of being under the cushion reaches this level on some day.
# Chosen from the test on July and August 2026 (reports/metrics.json): at 40% the
# warning caught about half of the real shortfalls with about 1 false alarm in 10.
ALERT_CHANCE = 0.40
CAUTIOUS_LEVEL = 0.25  # the forecast level used to measure the size of the gap


def safety_cushion(forecast: Forecast) -> float:
    """The default cushion in taka: one day of the user's typical spending."""
    return CUSHION_DAYS * forecast.typical_daily_spending


def chance_below(levels: dict[float, float], threshold: float) -> float:
    """Chance that the real value is under `threshold`.

    `levels` maps a chance to the value the forecast gives for it, for example
    {0.10: 200, 0.50: 900, 0.90: 2000}. Between two known levels the chance is
    read off a straight line. Beyond the outer levels the line is continued.
    The result is kept between 1% and 99%: a forecast is never certain.
    """
    known = sorted(levels.items())
    chances = [chance for chance, _ in known]
    values = [value for _, value in known]
    below = values[0] - (values[1] - values[0]) * chances[0] / (chances[1] - chances[0])
    above = values[-1] + (values[-1] - values[-2]) * (1 - chances[-1]) / (chances[-1] - chances[-2])
    values = [below, *values, above]
    chances = [0.0, *chances, 1.0]

    # the last known value at or under the threshold starts the line we read from
    start = sum(1 for value in values if value <= threshold) - 1
    start = max(0, min(start, len(values) - 2))
    width = max(values[start + 1] - values[start], 1e-9)
    share = min(max((threshold - values[start]) / width, 0.0), 1.0)
    chance = chances[start] + share * (chances[start + 1] - chances[start])
    return min(max(chance, 0.01), 0.99)


def find_shortfall(forecast: Forecast, cushion: float | None = None, alert_chance: float = ALERT_CHANCE,
                   warning_days: int = WARNING_DAYS) -> Alert | None:
    """The warning for this forecast, or None when the risk stays under the alert level.

    Looks at the next `warning_days` days. The alert names the first day the
    chance of being under the cushion reaches the alert level, the highest
    chance seen, and how far the cautious forecast falls under the cushion.
    """
    cushion = safety_cushion(forecast) if cushion is None else cushion
    window = forecast.points[:warning_days]
    chances = [chance_below(point.levels, cushion) for point in window]
    at_risk = [point for point, chance in zip(window, chances) if chance >= alert_chance]
    if not at_risk:
        return None
    lowest_cautious = min(point.levels[CAUTIOUS_LEVEL] for point in window)
    return Alert(day=at_risk[0].day, chance=round(max(chances), 4),
                 gap=round(max(cushion - lowest_cautious, 0.0), 2), cushion=round(cushion, 2))
