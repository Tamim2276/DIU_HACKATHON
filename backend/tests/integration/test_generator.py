from dataclasses import replace
from datetime import timedelta

import pandas as pd
import pytest

from app.infrastructure.config.settings import settings
from app.infrastructure.synthetic.generator import generate, save
from app.infrastructure.synthetic.personas import PERSONAS

# Two users per persona keep these tests fast.
SMALL = replace(settings, users_per_persona=2)


@pytest.fixture(scope="module")
def data():
    return generate(SMALL)


def test_same_seed_gives_same_data(data):
    again = generate(SMALL)
    pd.testing.assert_frame_equal(data.transactions, again.transactions)
    pd.testing.assert_frame_equal(data.truth_daily, again.truth_daily)
    pd.testing.assert_frame_equal(data.user_truth, again.user_truth)


def test_different_seed_gives_different_data(data):
    other = generate(replace(SMALL, seed=settings.seed + 1))
    assert not data.transactions["amount"].equals(other.transactions["amount"])


def test_saved_files_are_identical_between_runs(data, tmp_path):
    save(data, tmp_path / "first")
    save(generate(SMALL), tmp_path / "second")
    for name in ("users.csv", "user_truth.csv", "transactions.csv.gz", "truth_daily.csv.gz"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes(), name


def test_every_persona_is_generated(data):
    assert set(data.users["persona"]) == set(PERSONAS)
    assert len(data.users) == 2 * len(PERSONAS)


def test_balance_can_be_rebuilt_from_transactions(data):
    t = data.transactions
    signed = t["amount"].where(t["direction"] == "in", -(t["amount"] + t["fee"]))
    for user_id, rows in t.assign(signed=signed).groupby("user_id"):
        opening = rows["balance_after"].iloc[0] - rows["signed"].iloc[0]
        rebuilt = opening + rows["signed"].cumsum()
        assert (rebuilt - rows["balance_after"]).abs().max() < 0.01, user_id


def test_no_balance_goes_below_zero(data):
    t = data.transactions
    assert t["balance_after"].min() >= 0
    assert data.truth_daily["wallet_eod"].min() >= 0


def test_amounts_are_positive_and_fees_only_on_cash_out(data):
    t = data.transactions
    assert (t["amount"] > 0).all()
    assert (t.loc[t["type"] != "cash_out", "fee"] == 0).all()
    assert (t.loc[t["type"] == "cash_out", "fee"] > 0).all()


def test_transactions_stay_inside_the_simulated_period(data):
    stamps = data.transactions["timestamp"]
    assert stamps.min() >= pd.Timestamp(settings.start_date)
    assert stamps.max() < pd.Timestamp(settings.end_date + timedelta(days=1))


def test_each_users_transactions_are_in_time_order(data):
    for user_id, rows in data.transactions.groupby("user_id"):
        assert rows["timestamp"].is_monotonic_increasing, user_id


def test_truth_has_one_row_per_user_per_day(data):
    days = (settings.end_date - settings.start_date).days + 1
    assert len(data.truth_daily) == len(data.users) * days
