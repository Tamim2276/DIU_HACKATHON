"""A savings goal: an amount the user wants to have put aside by a date.

A fixed rule, no machine learning. The amount is spread evenly over the days
from today to the goal date. The part that falls inside the safe-to-spend
period is taken out of the money available for everyday spending, so a goal
can only lower the safe-to-spend number.
"""
from dataclasses import dataclass
from datetime import date

LONGEST_GOAL_DAYS = 366  # a goal further away than this is refused


@dataclass(frozen=True)
class SavingsGoal:
    amount: float  # taka
    by: date  # the day the amount should be put aside by


@dataclass(frozen=True)
class SavingsPlan:
    """What a goal asks of the user, and what it does to the safe-to-spend number."""
    goal: SavingsGoal
    per_day: float  # taka to put aside each day from tomorrow to the goal date
    set_aside: float  # taka put aside inside the safe-to-spend period
    safe_before: float  # safe to spend per day without the goal


def days_left(goal: SavingsGoal, as_of: date) -> int:
    return (goal.by - as_of).days


def problem_with(goal: SavingsGoal, as_of: date) -> str | None:
    """Why a goal cannot be used, or None when it can."""
    if goal.amount <= 0:
        return "the amount of a savings goal must be more than zero"
    if days_left(goal, as_of) < 1:
        return "the date of a savings goal must be after today"
    if days_left(goal, as_of) > LONGEST_GOAL_DAYS:
        return "the date of a savings goal must be within a year"
    return None


def per_day(goal: SavingsGoal, as_of: date) -> float:
    """Taka to put aside each day to reach the goal on time."""
    return goal.amount / days_left(goal, as_of)


def set_aside(goal: SavingsGoal, as_of: date, window_days: int) -> float:
    """Taka the goal takes out of a safe-to-spend period of `window_days` days."""
    return per_day(goal, as_of) * min(window_days, days_left(goal, as_of))
