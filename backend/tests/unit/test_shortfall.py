"""The shortfall rule, on hand-made forecasts with known answers."""
from datetime import date, timedelta

import pytest

from app.domain.entities.alert import Alert
from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.services.shortfall import ALERT_CHANCE, chance_below, find_shortfall, safety_cushion

TODAY = date(2026, 8, 12)
COMFORTABLE = (2000.0, 2500.0, 3000.0, 3500.0, 4000.0)  # every level far above a 400 taka cushion
LEVELS = {0.10: 10.0, 0.25: 20.0, 0.50: 30.0, 0.75: 40.0, 0.90: 50.0}


def make_forecast(days: dict[int, tuple], length: int = 30, spending: float = 400.0) -> Forecast:
    """A forecast that is comfortable every day except the days given as {days ahead: (p10, p25, p50, p75, p90)}."""
    points = tuple(ForecastPoint(TODAY + timedelta(days=d), *days.get(d, COMFORTABLE), cautious_income=0.0)
                   for d in range(1, length + 1))
    return Forecast(user_id="U0001", as_of=TODAY, balance=5000.0, typical_daily_spending=spending, points=points)


# ---------- chance of being under a threshold ----------

@pytest.mark.parametrize("threshold, chance", [
    (10.0, 0.10), (20.0, 0.25), (30.0, 0.50), (40.0, 0.75), (50.0, 0.90),  # exactly at a level
    (15.0, 0.175), (25.0, 0.375), (45.0, 0.825),  # halfway between two levels
    (-1000.0, 0.01), (1000.0, 0.99),  # far outside: never fully certain
])
def test_chance_of_being_under_a_threshold(threshold, chance):
    assert chance_below(LEVELS, threshold) == pytest.approx(chance)


def test_chance_rises_with_the_threshold():
    chances = [chance_below(LEVELS, t / 2) for t in range(-40, 160)]
    assert all(later >= earlier for earlier, later in zip(chances, chances[1:]))


def test_chance_when_the_lower_levels_are_all_zero():
    # a wallet forecast is cut off at zero, so the lower levels can be equal
    levels = {0.10: 0.0, 0.25: 0.0, 0.50: 2000.0, 0.75: 3000.0, 0.90: 4000.0}
    assert chance_below(levels, 500.0) == pytest.approx(0.25 + 0.25 * 500 / 2000)


# ---------- the rule ----------

def test_cushion_is_one_day_of_typical_spending():
    assert safety_cushion(make_forecast({}, spending=479.0)) == 479.0


def test_no_alert_when_the_balance_stays_comfortable():
    assert find_shortfall(make_forecast({})) is None


def test_alert_names_the_day_the_chance_and_the_gap():
    # day 4: a 400 taka cushion sits a third of the way from p50 (300) to p75 (600)
    forecast = make_forecast({4: (100.0, 200.0, 300.0, 600.0, 900.0)})
    alert = find_shortfall(forecast)
    assert isinstance(alert, Alert)
    assert alert.day == TODAY + timedelta(days=4)
    assert alert.chance == pytest.approx(0.5 + 0.25 / 3, abs=1e-4)
    assert alert.gap == 200.0  # cushion 400 minus the cautious level 200
    assert alert.cushion == 400.0


def test_alert_day_is_the_first_risky_day_but_chance_and_gap_are_the_worst_in_the_window():
    forecast = make_forecast({
        6: (100.0, 200.0, 300.0, 600.0, 900.0),  # first day at risk
        9: (0.0, 50.0, 100.0, 200.0, 300.0),  # the worst day: every level under the cushion
    })
    alert = find_shortfall(forecast)
    assert alert.day == TODAY + timedelta(days=6)
    assert alert.chance == 0.99
    assert alert.gap == 350.0  # cushion 400 minus the lowest cautious level, 50


def test_alert_fires_just_above_the_level_and_not_just_below():
    # the cushion of 400 sits between p25 and p50; moving p50 moves the chance across 40%
    just_above = make_forecast({3: (0.0, 100.0, 590.0, 2000.0, 3000.0)})  # chance about 40.3%
    just_below = make_forecast({3: (0.0, 100.0, 620.0, 2000.0, 3000.0)})  # chance about 39.4%
    assert chance_below(just_above.points[2].levels, 400.0) > ALERT_CHANCE
    assert chance_below(just_below.points[2].levels, 400.0) < ALERT_CHANCE
    assert find_shortfall(just_above) is not None
    assert find_shortfall(just_below) is None


def test_a_dip_beyond_the_warning_window_does_not_alert_yet():
    forecast = make_forecast({20: (0.0, 50.0, 100.0, 200.0, 300.0)})
    assert find_shortfall(forecast) is None
    assert find_shortfall(forecast, warning_days=30).day == TODAY + timedelta(days=20)


def test_a_larger_cushion_can_be_set_by_the_user():
    forecast = make_forecast({5: (500.0, 800.0, 1200.0, 1600.0, 2000.0)})
    assert find_shortfall(forecast) is None  # default cushion 400: no risk
    alert = find_shortfall(forecast, cushion=1500.0)
    assert alert.day == TODAY + timedelta(days=5)
    assert alert.cushion == 1500.0 and alert.gap == 700.0


def test_alert_level_can_be_changed():
    forecast = make_forecast({3: (0.0, 100.0, 620.0, 2000.0, 3000.0)})  # chance about 39.4%
    assert find_shortfall(forecast) is None
    assert find_shortfall(forecast, alert_chance=0.30) is not None
