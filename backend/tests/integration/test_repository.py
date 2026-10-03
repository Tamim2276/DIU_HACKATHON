"""Runs against the generated files in backend/data."""
from datetime import date, timedelta

import pytest

from app.application.ports.transaction_repository import UserNotFoundError
from app.domain.entities.transaction import Transaction
from app.infrastructure.config.settings import settings
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository
from app.infrastructure.synthetic.personas import PERSONAS

TODAY = date(2026, 8, 12)


@pytest.fixture(scope="module")
def repository():
    return CsvTransactionRepository(settings.data_dir)


def test_lists_every_generated_user(repository):
    users = repository.list_users()
    assert len(users) == 300
    assert users[0].user_id == "U0001"
    assert {user.persona for user in users} == set(PERSONAS)


def test_returns_nothing_after_the_requested_day(repository):
    transactions = repository.get_transactions("U0001", TODAY)
    assert transactions
    assert all(isinstance(t, Transaction) and t.user_id == "U0001" for t in transactions)
    assert max(t.timestamp.date() for t in transactions) <= TODAY


def test_includes_the_requested_day_itself(repository):
    everything = repository.get_transactions("U0001", settings.end_date)
    day = everything[len(everything) // 2].timestamp.date()
    assert repository.get_transactions("U0001", day)[-1].timestamp.date() == day
    assert repository.get_transactions("U0001", day - timedelta(days=1))[-1].timestamp.date() < day


def test_transactions_are_oldest_first(repository):
    stamps = [t.timestamp for t in repository.get_transactions("U0001", TODAY)]
    assert stamps == sorted(stamps)


def test_a_later_day_returns_more(repository):
    earlier = repository.get_transactions("U0001", TODAY)
    later = repository.get_transactions("U0001", settings.end_date)
    assert len(later) > len(earlier)
    assert later[: len(earlier)] == earlier


def test_a_day_before_the_data_starts_returns_nothing(repository):
    assert repository.get_transactions("U0001", settings.start_date - timedelta(days=1)) == []


def test_unknown_user_raises(repository):
    with pytest.raises(UserNotFoundError):
        repository.get_transactions("U9999", TODAY)
    with pytest.raises(UserNotFoundError):
        repository.get_user("U9999")
