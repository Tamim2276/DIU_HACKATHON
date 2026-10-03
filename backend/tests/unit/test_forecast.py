from datetime import date, timedelta

import pytest

from app.domain.entities.forecast import Forecast, ForecastPoint

TODAY = date(2026, 8, 12)


def point(days_ahead=1, levels=(100.0, 200.0, 300.0, 400.0, 500.0), income=0.0) -> ForecastPoint:
    return ForecastPoint(TODAY + timedelta(days=days_ahead), *levels, cautious_income=income)


def forecast(points) -> Forecast:
    return Forecast(user_id="U0001", as_of=TODAY, balance=1000.0, typical_daily_spending=400.0, points=tuple(points))


def test_point_gives_its_levels_by_chance():
    assert point().levels == {0.10: 100.0, 0.25: 200.0, 0.50: 300.0, 0.75: 400.0, 0.90: 500.0}


def test_levels_must_be_in_order():
    with pytest.raises(ValueError):
        point(levels=(100.0, 200.0, 150.0, 400.0, 500.0))


def test_balance_and_income_cannot_be_negative():
    with pytest.raises(ValueError):
        point(levels=(-1.0, 200.0, 300.0, 400.0, 500.0))
    with pytest.raises(ValueError):
        point(income=-5.0)


def test_forecast_days_must_start_tomorrow_and_follow_each_other():
    assert len(forecast([point(1), point(2), point(3)]).points) == 3
    with pytest.raises(ValueError):
        forecast([point(2), point(3)])  # does not start the day after today
    with pytest.raises(ValueError):
        forecast([point(1), point(3)])  # skips a day


def test_forecast_needs_at_least_one_day_and_a_positive_spending_level():
    with pytest.raises(ValueError):
        forecast([])
    with pytest.raises(ValueError):
        Forecast(user_id="U0001", as_of=TODAY, balance=0.0, typical_daily_spending=0.0, points=(point(1),))
