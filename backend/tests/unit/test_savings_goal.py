"""The savings goal rule, on examples worked by hand."""
from datetime import date, timedelta

import pytest

from app.domain.services.savings_goal import SavingsGoal, days_left, per_day, problem_with, set_aside

TODAY = date(2026, 8, 12)


def goal(amount: float, days: int) -> SavingsGoal:
    return SavingsGoal(amount, TODAY + timedelta(days=days))


def test_the_amount_is_spread_evenly_over_the_days_to_the_goal():
    assert days_left(goal(3000, 30), TODAY) == 30
    assert per_day(goal(3000, 30), TODAY) == 100.0
    assert per_day(goal(500, 1), TODAY) == 500.0  # due tomorrow: all of it in one day


def test_only_the_days_inside_the_period_are_set_aside():
    # 100 a day; a 14-day safe-to-spend period carries 14 of the 30 days
    assert set_aside(goal(3000, 30), TODAY, window_days=14) == 1400.0
    # a goal that falls inside the period is set aside in full
    assert set_aside(goal(700, 7), TODAY, window_days=14) == pytest.approx(700.0)
    assert set_aside(goal(1400, 14), TODAY, window_days=14) == pytest.approx(1400.0)


def test_a_goal_that_cannot_be_used_says_why():
    assert problem_with(goal(1000, 10), TODAY) is None
    assert "more than zero" in problem_with(goal(0, 10), TODAY)
    assert "more than zero" in problem_with(goal(-50, 10), TODAY)
    assert "after today" in problem_with(goal(1000, 0), TODAY)
    assert "after today" in problem_with(goal(1000, -3), TODAY)
    assert "within a year" in problem_with(goal(1000, 400), TODAY)
