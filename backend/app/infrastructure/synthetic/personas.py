"""The five simulated kinds of wallet customer.

All amounts are rough guesses in taka, not measured figures.
See docs/SYNTHETIC_DATA.md for the reasoning behind them.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Income:
    kind: str  # "daily", "monthly" or "lumpy"
    type: str  # the transaction type the income arrives as
    mean: float  # taka per payment
    sigma: float  # how much the amount varies
    work_prob: float = 0.0  # daily: chance of earning on a given day
    day: int = 0  # monthly: usual day of the month
    late_prob: float = 0.0  # monthly: chance the payment comes several days late
    per_month: float = 0.0  # lumpy: average number of payments in a month


@dataclass(frozen=True)
class Obligation:
    """A payment the user makes every month."""
    name: str
    type: str
    day: int  # usual day of the month
    amount: float


@dataclass(frozen=True)
class Persona:
    key: str
    label: str
    income: Income
    obligations: tuple[Obligation, ...]
    cash_share: float  # share of daily spending paid in cash
    ussd_share: float  # share of users on a feature phone
    tightness: tuple[float, float] = (0.93, 1.07)  # desired spending as a share of income
    side_income: Income | None = None
    side_prob: float = 0.0  # share of users who have the side income
    supplier_share: float = 0.0  # shops: share of sales that goes to suppliers
    eid_bonus: float = 0.0  # festival bonus as a share of one month's income


PERSONAS = {
    persona.key: persona
    for persona in (
        Persona(
            key="rider",
            label="Ride-share rider",
            income=Income(kind="daily", type="platform_payout", mean=900, sigma=0.35, work_prob=0.87),
            obligations=(
                Obligation("house_rent", "send_money", 5, 5000),
                Obligation("send_home", "send_money", 8, 6000),
                Obligation("bike_installment", "bill_payment", 15, 3000),
            ),
            cash_share=0.75,
            ussd_share=0.3,
        ),
        Persona(
            key="garment",
            label="Garment worker",
            income=Income(kind="monthly", type="salary", mean=16500, sigma=0.10, day=8, late_prob=0.25),
            obligations=(
                Obligation("house_rent", "send_money", 10, 3500),
                Obligation("send_home", "send_money", 11, 5000),
                Obligation("savings_samity", "send_money", 12, 1000),
            ),
            cash_share=0.8,
            ussd_share=0.6,
            eid_bonus=0.6,
        ),
        Persona(
            key="student",
            label="University student",
            income=Income(kind="monthly", type="receive_money", mean=11000, sigma=0.08, day=3, late_prob=0.3),
            side_income=Income(kind="monthly", type="receive_money", mean=4000, sigma=0.15, day=12),
            side_prob=0.6,
            obligations=(
                Obligation("mess_rent", "send_money", 5, 3500),
                Obligation("internet", "bill_payment", 7, 500),
            ),
            cash_share=0.5,
            ussd_share=0.05,
            tightness=(0.90, 1.03),
        ),
        Persona(
            key="shopkeeper",
            label="Small shop owner",
            income=Income(kind="daily", type="merchant_receipt", mean=3400, sigma=0.30, work_prob=0.93),
            supplier_share=0.72,
            obligations=(
                Obligation("shop_rent", "send_money", 5, 9000),
                Obligation("electricity", "bill_payment", 12, 2500),
            ),
            cash_share=0.7,
            ussd_share=0.25,
        ),
        Persona(
            key="freelancer",
            label="Freelancer",
            income=Income(kind="lumpy", type="remittance", mean=15000, sigma=0.5, per_month=2.2),
            obligations=(
                Obligation("house_rent", "send_money", 5, 10000),
                Obligation("internet", "bill_payment", 8, 1200),
                Obligation("electricity", "bill_payment", 12, 1500),
                Obligation("subscriptions", "merchant_payment", 15, 1500),
            ),
            cash_share=0.4,
            ussd_share=0.0,
            tightness=(0.80, 0.97),  # lumpy earners keep a larger cushion
        ),
    )
}

MERCHANT_CATEGORIES = ["grocery", "food", "transport", "pharmacy", "shopping"]
MERCHANT_WEIGHTS = [0.35, 0.30, 0.15, 0.08, 0.12]
RECHARGE_AMOUNTS = [20, 30, 50, 100]
