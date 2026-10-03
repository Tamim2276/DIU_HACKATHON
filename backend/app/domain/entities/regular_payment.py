"""Payments a user makes regularly, and the ones coming up."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RegularPayment:
    """A recipient the user pays every month: rent, money sent home, a bill, a supplier."""
    recipient: str
    label: str  # the name saved for this recipient, for example "house_rent"
    type: str  # transaction type, for example "send_money"
    payments_per_month: int  # 1 for a monthly payment; more for something like a weekly supplier
    usual_day: int | None  # usual day of the month; None when it is paid several times a month
    usual_amount: float  # usual size of one payment, in taka
    monthly_total: float  # usual total per month, in taka


@dataclass(frozen=True)
class DuePayment:
    """One expected payment on one future day."""
    recipient: str
    label: str
    due: date
    amount: float
