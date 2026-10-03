"""Daily panel, model inputs and baselines. The leak tests are the important ones."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.infrastructure.config.settings import settings
from app.infrastructure.ml.baselines import BASELINES, baseline_balance, baseline_net_flow
from app.infrastructure.ml.features import (
    FEATURE_NAMES,
    MIN_HISTORY_DAYS,
    build_features,
    future_flows,
    make_calendar,
)
from app.infrastructure.ml.panel import panel_from_frame, panel_from_transactions, read_transactions
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository

TODAY = date(2026, 8, 12)
ONE_OF_EACH_PERSONA = (0, 60, 120, 180, 240)


@pytest.fixture(scope="module")
def frame():
    return read_transactions(settings.data_dir)


@pytest.fixture(scope="module")
def panel(frame):
    return panel_from_frame(frame, settings.start_date, settings.end_date)


@pytest.fixture(scope="module")
def calendar(panel):
    return make_calendar(panel.start, panel.n_days + settings.horizon_days + 1)


# ---------- panel ----------

def test_panel_has_every_user_and_every_day(panel):
    assert len(panel.users) == 300
    assert panel.n_days == 365
    assert panel.inflow.shape == panel.outflow.shape == panel.balance.shape == (300, 365)


def test_panel_balance_matches_the_simulator(panel):
    truth = pd.read_csv(settings.data_dir / "truth_daily.csv.gz")
    recorded = truth["wallet_eod"].to_numpy().reshape(len(panel.users), panel.n_days)
    assert np.abs(panel.balance - recorded).max() < 0.01


def test_one_users_panel_matches_the_full_panel(panel):
    repository = CsvTransactionRepository(settings.data_dir)
    today = panel.day_index(TODAY)
    for u in ONE_OF_EACH_PERSONA:
        transactions = repository.get_transactions(panel.users[u], TODAY)
        single = panel_from_transactions(transactions, settings.start_date, TODAY)
        assert single.n_days == today + 1
        assert np.allclose(single.inflow[0], panel.inflow[u, : today + 1])
        assert np.allclose(single.outflow[0], panel.outflow[u, : today + 1])
        assert np.allclose(single.balance[0], panel.balance[u, : today + 1])


# ---------- no look into the future ----------

@pytest.mark.parametrize("origin_day", [date(2026, 2, 10), date(2026, 5, 31), TODAY])
def test_inputs_do_not_change_when_the_future_changes(panel, calendar, origin_day):
    origin = panel.day_index(origin_day)
    rng = np.random.default_rng(0)
    for u in ONE_OF_EACH_PERSONA:
        inflow, outflow = panel.inflow[u].copy(), panel.outflow[u].copy()
        before = build_features(inflow, outflow, panel.balance[u], calendar, [origin])

        # replace everything after the origin day with random amounts
        inflow[origin + 1:] = rng.uniform(0, 50_000, len(inflow) - origin - 1)
        outflow[origin + 1:] = rng.uniform(0, 50_000, len(outflow) - origin - 1)
        opening = panel.balance[u, 0] - (panel.inflow[u, 0] - panel.outflow[u, 0])
        balance = opening + np.cumsum(inflow - outflow)
        after = build_features(inflow, outflow, balance, calendar, [origin])

        assert np.array_equal(before.X, after.X)
        assert np.array_equal(before.scale, after.scale)
        assert np.array_equal(before.balance, after.balance)


def test_inputs_do_not_change_when_later_transactions_change(frame, panel, calendar):
    changed = frame.copy()
    later = changed["timestamp"] >= pd.Timestamp(TODAY) + pd.Timedelta(days=1)
    changed.loc[later, "amount"] = changed.loc[later, "amount"] * 7 + 123
    changed_panel = panel_from_frame(changed, settings.start_date, settings.end_date)
    origin = panel.day_index(TODAY)
    for u in ONE_OF_EACH_PERSONA:
        before = build_features(panel.inflow[u], panel.outflow[u], panel.balance[u], calendar, [origin])
        after = build_features(changed_panel.inflow[u], changed_panel.outflow[u], changed_panel.balance[u],
                               calendar, [origin])
        assert not np.array_equal(panel.inflow[u], changed_panel.inflow[u])  # the future really changed
        assert np.array_equal(before.X, after.X)


def test_inputs_from_history_cut_at_today_match_the_full_history(panel, calendar):
    origin = panel.day_index(TODAY)
    for u in ONE_OF_EACH_PERSONA:
        full = build_features(panel.inflow[u], panel.outflow[u], panel.balance[u], calendar, [origin])
        cut = build_features(panel.inflow[u, : origin + 1], panel.outflow[u, : origin + 1],
                             panel.balance[u, : origin + 1], calendar, [origin])
        assert np.array_equal(full.X, cut.X)


# ---------- shape and content ----------

def test_one_row_per_origin_and_day_ahead(panel, calendar):
    origins = [200, 250, 300]
    rows = build_features(panel.inflow[0], panel.outflow[0], panel.balance[0], calendar, origins)
    assert rows.X.shape == (len(origins) * settings.horizon_days, len(FEATURE_NAMES))
    assert np.isfinite(rows.X).all()
    assert list(rows.days_ahead[:30]) == list(range(1, 31))
    assert list(np.unique(rows.origin)) == origins


def test_too_little_history_is_rejected(panel, calendar):
    with pytest.raises(ValueError):
        build_features(panel.inflow[0], panel.outflow[0], panel.balance[0], calendar, [MIN_HISTORY_DAYS - 1])


def test_balance_plus_future_net_flow_is_the_future_balance(panel):
    origin = panel.day_index(TODAY)
    for u in ONE_OF_EACH_PERSONA:
        net, money_in = future_flows(panel.inflow[u], panel.outflow[u], [origin])
        assert np.allclose(panel.balance[u, origin] + net, panel.balance[u, origin + 1: origin + 31])
        assert np.allclose(money_in, np.cumsum(panel.inflow[u, origin + 1: origin + 31]))


def test_future_flows_refuse_to_run_past_the_data(panel):
    with pytest.raises(ValueError):
        future_flows(panel.inflow[0], panel.outflow[0], [panel.n_days - 5])


# ---------- baselines, on hand-made users ----------

START = date(2025, 10, 1)


def hand_made(inflow, outflow):
    balance = 5_000 + np.cumsum(inflow - outflow)
    return inflow, outflow, balance, make_calendar(START, len(inflow) + 31, eid_dates=())


def test_every_baseline_is_exact_for_a_perfectly_steady_user():
    # 30 in and 20 out every single day: 10 taka more each day, forever
    inflow, outflow, balance, calendar = hand_made(np.full(220, 30.0), np.full(220, 20.0))
    rows = build_features(inflow, outflow, balance, calendar, [150])
    actual, _ = future_flows(inflow, outflow, [150])
    assert np.allclose(actual, 10.0 * np.arange(1, 31))
    for name in BASELINES:
        assert np.allclose(baseline_net_flow(rows, name), actual), name
        assert np.allclose(baseline_balance(rows, name), balance[151:181]), name


def test_monthly_baselines_follow_a_salary_day_and_the_daily_average_does_not():
    # 3,000 arrives on the 5th of every month and 100 is spent every day
    days = pd.date_range(START, periods=250)
    inflow, outflow, balance, calendar = hand_made(np.where(days.day == 5, 3000.0, 0.0), np.full(250, 100.0))
    origin = (date(2026, 3, 1) - START).days
    rows = build_features(inflow, outflow, balance, calendar, [origin], horizons=[10])
    actual, _ = future_flows(inflow, outflow, [origin], horizons=[10])

    assert actual[0] == 2000.0  # the next ten days hold one salary and ten days of spending
    assert baseline_net_flow(rows, "same period last month")[0] == pytest.approx(2000.0)
    assert baseline_net_flow(rows, "average of the last 3 months")[0] == pytest.approx(2000.0)
    assert baseline_net_flow(rows, "recent daily average")[0] == pytest.approx(0.0, abs=1.0)


def test_baselines_disagree_on_real_users(panel, calendar):
    origin = panel.day_index(TODAY)
    rows = build_features(panel.inflow[60], panel.outflow[60], panel.balance[60], calendar, [origin])
    forecasts = [baseline_net_flow(rows, name) for name in BASELINES]
    assert all(np.isfinite(f).all() for f in forecasts)
    assert not np.allclose(forecasts[0], forecasts[1])
    assert not np.allclose(forecasts[1], forecasts[2])
