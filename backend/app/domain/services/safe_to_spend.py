"""Safe to spend: how much the user can spend per day and still reach their next income.

A fixed formula, not a model output and not an LLM answer:

    (balance + cautious income - regular payments due - safety cushion - savings set aside)
    / days in the window

The window is the days until the next expected large income, or 14 days for
people whose income is not monthly. The result is never below zero.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.entities.forecast import Forecast
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.services.regular_payments import MONTH_DAYS
from app.domain.services.shortfall import safety_cushion

WINDOW_WITHOUT_PAYDAY = 14  # days to plan for when income is daily or irregular
# Money forecast to arrive in the last days before payday may be the pay itself coming early,
# so it is not counted as extra income.
EARLY_PAY_DAYS = 6


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
    savings: float

    @property
    def left_over(self) -> float:
        """What remains for daily spending over the whole window. Negative when commitments exceed the money."""
        return self.balance + self.cautious_income - self.payments_due - self.cushion - self.savings


def safe_to_spend_per_day(balance: float, cautious_income: float, payments_due: float, cushion: float,
                          window_days: int, savings: float = 0.0) -> float:
    """The formula itself."""
    if window_days < 1:
        raise ValueError("the window must be at least one day")
    return max((balance + cautious_income - payments_due - cushion - savings) / window_days, 0.0)


def plan_safe_to_spend(forecast: Forecast, regular: list[RegularPayment], due: list[DuePayment],
                       income_day: date | None, savings: float = 0.0, cushion: float | None = None) -> SafeToSpend:
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

    last_counted = as_of + timedelta(days=counted_days)
    cautious_income = forecast.points[income_days - 1].cautious_income if income_days else 0.0
    # Monthly payments are counted on their due day. Payments made several times a month, such as a
    # weekly supplier, are spread evenly, so the result does not jump when one falls just outside the window.
    several_a_month = {p.recipient: p for p in regular if p.payments_per_month > 1}
    payments_due = sum(d.amount for d in due if d.recipient not in several_a_month and as_of < d.due <= last_counted)
    payments_due += sum(p.monthly_total for p in several_a_month.values()) * counted_days / MONTH_DAYS
    cushion = safety_cushion(forecast) if cushion is None else cushion

    amount = safe_to_spend_per_day(forecast.balance, cautious_income, payments_due, cushion, window_days, savings)
    return SafeToSpend(
        amount=float(math.floor(amount)),
        window_days=window_days,
        until=as_of + timedelta(days=window_days),
        balance=forecast.balance,
        cautious_income=round(cautious_income, 2),
        payments_due=round(payments_due, 2),
        cushion=round(cushion, 2),
        savings=round(savings, 2),
    )
