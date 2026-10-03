"""Safe to spend: how much the user can spend per day and still pay everything on time until their next income.

A fixed formula, not a model output and not an LLM answer. It is worked out
for every day of the window, as if the money only had to last until that day:

    (balance + cautious income by that day - regular payments due by that day
     - savings set aside by that day) / days from today to that day

On the last day of the window the safety cushion is taken off as well. Safe
to spend is the smallest of these answers, so the tightest day decides. Spent
at that rate, the money covers every regular payment on the day it is due and
the cushion is still there when the window ends. The result is never below zero.

The window is the days until the next expected large income, or 14 days for
people whose income is not monthly.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.entities.forecast import Forecast
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.services.regular_payments import MONTH_DAYS
from app.domain.services.savings_goal import SavingsGoal, set_aside
from app.domain.services.shortfall import safety_cushion

WINDOW_WITHOUT_PAYDAY = 14  # days to plan for when income is daily or irregular
# Money forecast to arrive in the last days before payday may be the pay itself coming early,
# so it is not counted as extra income.
EARLY_PAY_DAYS = 6


@dataclass(frozen=True)
class DayCheck:
    """The sum for one day of the window: what is left by then if nothing is spent on everyday things."""
    day: date
    days: int  # from today to this day
    cautious_income: float  # money expected to arrive by this day, at a cautious level
    payments_due: float  # regular payments that fall due by this day
    cushion: float  # kept on the last day of the window, zero on the days before it
    savings: float  # put aside for a savings goal by this day
    left_over: float  # negative when the commitments by this day exceed the money

    @property
    def per_day(self) -> float:
        return self.left_over / self.days


@dataclass(frozen=True)
class SafeToSpend:
    """The number, and every figure that went into it, so it can be explained."""
    amount: float  # taka per day, rounded down to a whole taka
    window_days: int  # the days the money has to last
    until: date  # the last day of the window: the next income day, when there is one
    balance: float
    cautious_income: float  # money expected to arrive before the window ends, at a cautious level
    payments_due: float  # regular payments that fall due before the window ends
    cushion: float
    savings: float  # put aside for a savings goal before the window ends
    tightest: DayCheck  # the day of the window that leaves the least to spend: it sets the amount


def left_over(balance: float, cautious_income: float, payments_due: float, cushion: float, savings: float = 0.0) -> float:
    """What remains for everyday spending, to the paisa. Negative when the commitments exceed the money."""
    return round(balance + cautious_income - payments_due - cushion - savings, 2)


def safe_to_spend_per_day(balance: float, cautious_income: float, payments_due: float, cushion: float,
                          window_days: int, savings: float = 0.0) -> float:
    """The formula for one day of the window."""
    if window_days < 1:
        raise ValueError("the window must be at least one day")
    return max(left_over(balance, cautious_income, payments_due, cushion, savings) / window_days, 0.0)


def plan_safe_to_spend(forecast: Forecast, regular: list[RegularPayment], due: list[DuePayment],
                       income_day: date | None, goal: SavingsGoal | None = None,
                       cushion: float | None = None) -> SafeToSpend:
    """Work the formula out for one user from their forecast, regular payments and next income day.

    With a known income day, the money has to last through that day, and only
    income and payments expected before it are counted: the income itself and
    the payments made from it belong to the next period.
    """
    as_of, horizon = forecast.as_of, len(forecast.points)
    days_to_income = (income_day - as_of).days if income_day is not None else None
    if days_to_income is not None and 1 <= days_to_income <= horizon:
        window_days, counted_days = days_to_income, days_to_income - 1
        income_days = max(counted_days - EARLY_PAY_DAYS, 0)
    elif days_to_income is not None and days_to_income > horizon:
        window_days = counted_days = income_days = horizon  # the next income is beyond the forecast: plan for all of it
    else:
        window_days = counted_days = income_days = min(WINDOW_WITHOUT_PAYDAY, horizon)

    # Monthly payments are counted on their due day. Payments made several times a month, such as a
    # weekly supplier, are spread evenly, so the result does not jump when one falls just outside the window.
    several_a_month = {p.recipient: p for p in regular if p.payments_per_month > 1}
    spread_per_day = sum(p.monthly_total for p in several_a_month.values()) / MONTH_DAYS
    dated = [d for d in due if d.recipient not in several_a_month]
    cushion = safety_cushion(forecast) if cushion is None else cushion

    def check(days: int) -> DayCheck:
        """The sum for the day `days` from today."""
        with_income, with_payments = min(days, income_days), min(days, counted_days)
        income = round(forecast.points[with_income - 1].cautious_income if with_income else 0.0, 2)
        last_counted = as_of + timedelta(days=with_payments)
        payments = round(sum(d.amount for d in dated if as_of < d.due <= last_counted) + spread_per_day * with_payments, 2)
        kept = round(cushion if days == window_days else 0.0, 2)
        savings = round(set_aside(goal, as_of, days) if goal is not None else 0.0, 2)
        return DayCheck(day=as_of + timedelta(days=days), days=days, cautious_income=income, payments_due=payments,
                        cushion=kept, savings=savings,
                        left_over=left_over(forecast.balance, income, payments, kept, savings))

    checks = [check(days) for days in range(1, window_days + 1)]
    tightest, whole = min(checks, key=lambda c: c.per_day), checks[-1]
    amount = safe_to_spend_per_day(forecast.balance, tightest.cautious_income, tightest.payments_due,
                                   tightest.cushion, tightest.days, tightest.savings)
    return SafeToSpend(
        amount=float(math.floor(amount)),
        window_days=window_days,
        until=whole.day,
        balance=forecast.balance,
        cautious_income=whole.cautious_income,
        payments_due=whole.payments_due,
        cushion=round(cushion, 2),
        savings=whole.savings,
        tightest=tightest,
    )
