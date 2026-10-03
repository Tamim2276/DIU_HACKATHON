"""The detection rules checked against what the simulator really did.

The rules see only transactions. The simulator's hidden settings (user_truth.csv)
say which payments were truly regular, so we can count how many the rules find.
"""
import json
from collections import Counter
from datetime import date, timedelta

import pandas as pd
import pytest

from app.domain.services.income_pattern import DAILY, IRREGULAR, MONTHLY, find_income_pattern, next_income_day
from app.domain.services.regular_payments import find_regular_payments, upcoming_payments
from app.infrastructure.config.settings import settings
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository

TODAY = date(2026, 8, 12)


@pytest.fixture(scope="module")
def cases():
    """For every user: persona, transactions up to today, and the truly regular payments."""
    repository = CsvTransactionRepository(settings.data_dir)
    truth = pd.read_csv(settings.data_dir / "user_truth.csv").set_index("user_id")
    return [(user.persona, repository.get_transactions(user.user_id, TODAY),
             {p["counterparty"]: p for p in json.loads(truth.loc[user.user_id, "regular_payments"])})
            for user in repository.list_users()]


def test_most_truly_regular_payments_are_found_and_few_others(cases):
    real, hit, found, amount_close = 0, 0, 0, 0
    for _, transactions, true in cases:
        monthly = {p.recipient: p for p in find_regular_payments(transactions, TODAY) if p.payments_per_month == 1}
        real += len(true)
        found += len(monthly)
        for recipient in set(true) & set(monthly):
            hit += 1
            amount_close += abs(monthly[recipient].usual_amount / true[recipient]["amount"] - 1) <= 0.10
    assert hit / real >= 0.88  # measured: 92%. The rest were paid late, in part, or skipped by a user who was short
    assert hit / found >= 0.95  # measured: 99%
    assert amount_close / hit >= 0.95


def test_weekly_supplier_payments_are_found_for_shop_owners(cases):
    with_supplier = sum(any(p.label == "supplier" and p.payments_per_month > 1 for p in find_regular_payments(t, TODAY))
                        for persona, t, _ in cases if persona == "shopkeeper")
    assert with_supplier >= 50  # of 60


def test_income_pattern_matches_how_each_persona_is_paid(cases):
    kinds = {}
    for persona, transactions, _ in cases:
        kinds.setdefault(persona, Counter())[find_income_pattern(transactions, TODAY).kind] += 1
    assert kinds["rider"] == {DAILY: 60}
    assert kinds["shopkeeper"] == {DAILY: 60}
    assert kinds["garment"] == {MONTHLY: 60}
    assert kinds["student"] == {MONTHLY: 60}
    assert kinds["freelancer"][IRREGULAR] >= 50


def test_garment_salary_day_is_found_near_the_8th(cases):
    days = [find_income_pattern(t, TODAY).usual_day for persona, t, _ in cases if persona == "garment"]
    assert sum(6 <= day <= 12 for day in days) >= 57  # of 60


def test_upcoming_payments_and_next_income_day_are_in_the_future(cases):
    for _, transactions, _ in cases:
        regular = find_regular_payments(transactions, TODAY)
        due = upcoming_payments(regular, transactions, TODAY)
        assert all(TODAY < d.due <= TODAY + timedelta(days=30) and d.amount > 0 for d in due)
        assert [d.due for d in due] == sorted(d.due for d in due)
        pattern = find_income_pattern(transactions, TODAY)
        income_day = next_income_day(pattern, transactions, TODAY)
        assert (income_day is None) == (pattern.kind != MONTHLY)
        assert income_day is None or TODAY < income_day <= TODAY + timedelta(days=40)
