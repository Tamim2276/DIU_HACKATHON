"""How a user's income arrives: on a usual day each month, every day, or irregularly.

A fixed rule, no machine learning. It uses only amounts and dates, not labels,
because a wallet provider cannot tell an allowance from a loan between friends.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from app.domain.entities.transaction import MONEY_IN, Transaction
from app.domain.services.months import add_months, day_in_month, month_of, previous_months

MONTHLY, DAILY, IRREGULAR = "monthly", "daily", "irregular"

MONTHS_BACK = 4
MIN_MONTHS = 3
LARGE_SHARE = 0.40  # one payment this large, as a share of the month's money in, is a large income
SAME_DAYS = 6  # a monthly income arrives within this many days of its usual day
SIMILAR = 0.30  # and its amount stays within this share of the usual amount
RECENT_DAYS = 60
DAILY_SHARE = 0.5  # income on at least this share of recent days means "paid daily"
LATE_INCOME_DAYS = 3  # when a monthly income is overdue, expect it within this many days


@dataclass(frozen=True)
class IncomePattern:
    kind: str  # MONTHLY, DAILY or IRREGULAR
    usual_day: int | None = None  # day of the month, for a monthly income
    usual_amount: float | None = None  # taka, for a monthly income


def find_income_pattern(transactions: list[Transaction], as_of: date) -> IncomePattern:
    money_in = [t for t in transactions if t.direction == MONEY_IN and t.timestamp.date() <= as_of]

    # monthly: in most recent months one payment of a steady size makes up a large share of the month,
    # around the same day
    largest = []
    for month in previous_months(as_of, MONTHS_BACK):
        in_month = [t for t in money_in if month_of(t.timestamp.date()) == month]
        if in_month:
            top = max(in_month, key=lambda t: t.amount)
            if top.amount >= LARGE_SHARE * sum(t.amount for t in in_month):
                largest.append(top)
    if len(largest) >= MIN_MONTHS:
        usual_day = round(median(t.timestamp.day for t in largest))
        usual_amount = median(t.amount for t in largest)
        steady = [t for t in largest if abs(t.timestamp.day - usual_day) <= SAME_DAYS
                  and abs(t.amount - usual_amount) <= SIMILAR * usual_amount]
        if len(steady) >= MIN_MONTHS:
            return IncomePattern(MONTHLY, usual_day, round(median(t.amount for t in steady), 2))

    # daily: money comes in on most days
    since = as_of - timedelta(days=RECENT_DAYS)
    income_days = {t.timestamp.date() for t in money_in if t.timestamp.date() > since}
    if len(income_days) >= DAILY_SHARE * RECENT_DAYS:
        return IncomePattern(DAILY)
    return IncomePattern(IRREGULAR)


def next_income_day(pattern: IncomePattern, transactions: list[Transaction], as_of: date) -> date | None:
    """The day the next large income is expected, or None when income is not monthly."""
    if pattern.kind != MONTHLY:
        return None
    this_month = month_of(as_of)
    # this month's income has arrived if a payment of about the usual size came around the usual day or later;
    # a large payment much earlier in the month is something else
    arrived = any(
        t.direction == MONEY_IN and month_of(t.timestamp.date()) == this_month and t.timestamp.date() <= as_of
        and t.amount >= 0.5 * pattern.usual_amount and t.timestamp.day >= pattern.usual_day - SAME_DAYS
        for t in transactions
    )
    if arrived:
        return day_in_month(add_months(this_month, 1), pattern.usual_day)
    expected = day_in_month(this_month, pattern.usual_day)
    if expected > as_of:
        return expected
    return as_of + timedelta(days=LATE_INCOME_DAYS)  # overdue this month: expect it soon
