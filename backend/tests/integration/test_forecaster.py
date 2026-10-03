"""The forecaster the app calls: one user, one day, the saved model."""
import time
from dataclasses import replace
from datetime import date, timedelta

import numpy as np
import pytest

from app.application.ports.forecaster import NotEnoughHistoryError
from app.infrastructure.config.settings import settings
from app.infrastructure.ml.panel import panel_from_frame, read_transactions
from app.infrastructure.ml.quantile_forecaster import QuantileForecaster
from app.infrastructure.ml.training import build_dataset, calendar_for, load_models, predict_net_flow
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository

TODAY = date(2026, 8, 12)
ONE_OF_EACH_PERSONA = ("U0001", "U0061", "U0121", "U0181", "U0241")


@pytest.fixture(scope="module")
def repository():
    return CsvTransactionRepository(settings.data_dir)


@pytest.fixture(scope="module")
def forecaster():
    return QuantileForecaster(settings.model_dir)


@pytest.mark.parametrize("user_id", ONE_OF_EACH_PERSONA)
def test_forecast_covers_the_next_30_days_with_levels_in_order(repository, forecaster, user_id):
    forecast = forecaster.forecast(repository.get_transactions(user_id, TODAY), TODAY)
    assert forecast.user_id == user_id and forecast.as_of == TODAY
    assert [p.day for p in forecast.points] == [TODAY + timedelta(days=i) for i in range(1, 31)]
    for p in forecast.points:
        assert 0 <= p.p10 <= p.p25 <= p.p50 <= p.p75 <= p.p90
    income = [p.cautious_income for p in forecast.points]
    assert income == sorted(income) and income[0] >= 0


def test_forecast_starts_from_todays_balance(repository, forecaster):
    transactions = repository.get_transactions("U0061", TODAY)
    forecast = forecaster.forecast(transactions, TODAY)
    assert forecast.balance == transactions[-1].balance_after
    assert forecast.typical_daily_spending > 0


def test_forecast_does_not_change_when_later_transactions_exist(repository, forecaster):
    up_to_today = repository.get_transactions("U0061", TODAY)
    everything = repository.get_transactions("U0061", settings.end_date)
    assert len(everything) > len(up_to_today)
    expected = forecaster.forecast(up_to_today, TODAY)
    assert forecaster.forecast(everything, TODAY) == expected

    # and when what happens later is completely different
    changed = [replace(t, amount=t.amount * 9 + 100) if t.timestamp.date() > TODAY else t for t in everything]
    assert forecaster.forecast(changed, TODAY) == expected


def test_forecast_matches_the_model_that_was_tested(repository, forecaster):
    """The app's forecast is the same forecast the evaluation in step 9 graded."""
    panel = panel_from_frame(read_transactions(settings.data_dir), settings.start_date, settings.end_date)
    models = load_models(settings.model_dir)
    for user_id in ONE_OF_EACH_PERSONA:
        u = panel.users.index(user_id)
        data = build_dataset(panel, calendar_for(panel), [u], [panel.day_index(TODAY)])
        graded = np.maximum(data.balance[:, None] + predict_net_flow(models, data.X) * data.scale[:, None], 0.0)
        forecast = forecaster.forecast(repository.get_transactions(user_id, TODAY), TODAY)
        served = np.array([[p.p10, p.p25, p.p50, p.p75, p.p90] for p in forecast.points])
        assert np.allclose(served, graded, atol=0.01), user_id


def test_one_forecast_takes_well_under_two_seconds(repository, forecaster):
    transactions = repository.get_transactions("U0181", TODAY)
    forecaster.forecast(transactions, TODAY)  # the first call warms things up
    started = time.perf_counter()
    forecaster.forecast(transactions, TODAY)
    assert time.perf_counter() - started < 2.0


def test_forecast_works_on_the_last_day_of_data(repository, forecaster):
    forecast = forecaster.forecast(repository.get_transactions("U0001", settings.end_date), settings.end_date)
    assert forecast.points[-1].day == settings.end_date + timedelta(days=30)


def test_too_little_history_is_refused(repository, forecaster):
    early = date(2025, 12, 1)
    with pytest.raises(NotEnoughHistoryError):
        forecaster.forecast(repository.get_transactions("U0001", early), early)


def test_no_transactions_is_refused(forecaster):
    with pytest.raises(NotEnoughHistoryError):
        forecaster.forecast([], TODAY)


def test_transactions_of_two_users_are_refused(repository, forecaster):
    mixed = repository.get_transactions("U0001", TODAY) + repository.get_transactions("U0061", TODAY)
    with pytest.raises(ValueError):
        forecaster.forecast(mixed, TODAY)
