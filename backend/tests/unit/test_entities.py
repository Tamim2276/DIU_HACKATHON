from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from app.domain.entities.transaction import MONEY_IN, MONEY_OUT, Transaction
from app.domain.entities.user import User


def make_transaction(**changes) -> Transaction:
    values = dict(
        txn_id="T0000001", user_id="U0001", timestamp=datetime(2026, 8, 12, 10, 30),
        type="cash_out", direction=MONEY_OUT, amount=1000.0, fee=14.0,
        counterparty="A-12345", category="cash", channel="agent", balance_after=3986.0,
    )
    return Transaction(**{**values, **changes})


def test_money_out_lowers_the_balance_by_amount_and_fee():
    assert make_transaction().signed_amount == -1014.0


def test_money_in_raises_the_balance_by_the_amount():
    salary = make_transaction(type="salary", direction=MONEY_IN, amount=16500.0, fee=0.0)
    assert salary.signed_amount == 16500.0


def test_direction_must_be_in_or_out():
    with pytest.raises(ValueError):
        make_transaction(direction="sideways")


def test_amount_must_be_positive():
    with pytest.raises(ValueError):
        make_transaction(amount=0)


def test_transaction_cannot_be_changed_after_creation():
    with pytest.raises(FrozenInstanceError):
        make_transaction().amount = 5.0


def test_user_holds_id_and_persona():
    user = User(user_id="U0001", persona="rider", persona_label="Ride-share rider")
    assert (user.user_id, user.persona, user.persona_label) == ("U0001", "rider", "Ride-share rider")
