"""Training on a small slice of users, plus checks on the saved model."""
import numpy as np
import pytest
import sklearn

from app.infrastructure.config.settings import settings
from app.infrastructure.ml.features import FEATURE_NAMES
from app.infrastructure.ml.panel import panel_from_frame, read_transactions
from app.infrastructure.ml.training import (
    MODEL_FILE,
    QUANTILES,
    build_dataset,
    calendar_for,
    held_out_users,
    load_models,
    predict_cautious_income,
    predict_net_flow,
    save_models,
    train,
    training_origins,
    training_users,
)


@pytest.fixture(scope="module")
def panel():
    return panel_from_frame(read_transactions(settings.data_dir), settings.start_date, settings.end_date)


@pytest.fixture(scope="module")
def small_models(panel):
    # a few users of every persona and few rounds: enough to test the code, not to judge accuracy
    users = [u for u in training_users(panel) if u % 6 == 0]
    return train(panel, users=users, max_rounds=40, log=lambda line: None), users


def test_every_fifth_user_is_kept_out_of_training(panel):
    learn, never_seen = training_users(panel), held_out_users(panel)
    assert len(learn) == 240 and len(never_seen) == 60
    assert not set(learn) & set(never_seen)
    assert sorted(learn + never_seen) == list(range(300))


def test_no_training_forecast_looks_past_the_last_training_day(panel):
    origins = training_origins(panel)
    assert origins.max() + settings.horizon_days <= panel.day_index(settings.train_end)
    assert origins.max() < panel.day_index(settings.test_start)


def test_training_returns_six_models(small_models):
    models, users = small_models
    assert list(models["net"]) == list(QUANTILES)
    assert models["money_in"] is not None
    assert models["feature_names"] == FEATURE_NAMES
    assert len(models["trained_on"]["users"]) == len(users)
    assert models["trained_on"]["last_origin"] <= "2026-05-31"


def test_forecast_levels_are_in_order_and_income_is_not_negative(panel, small_models):
    models, users = small_models
    data = build_dataset(panel, calendar_for(panel), users[:5], [panel.day_index(settings.test_start)])
    levels = predict_net_flow(models, data.X)
    assert levels.shape == (len(data.X), len(QUANTILES))
    assert (np.diff(levels, axis=1) >= 0).all()
    assert (predict_cautious_income(models, data.X) >= 0).all()


def test_even_a_small_model_beats_guessing_no_change(panel, small_models):
    models, _ = small_models
    data = build_dataset(panel, calendar_for(panel), held_out_users(panel), [panel.day_index(settings.test_start)])
    likely = predict_net_flow(models, data.X)[:, list(QUANTILES).index(0.50)]
    assert np.abs(likely - data.net).mean() < np.abs(data.net).mean()


def test_saved_models_predict_the_same_after_loading(panel, small_models, tmp_path):
    models, users = small_models
    data = build_dataset(panel, calendar_for(panel), users[:3], [panel.day_index(settings.test_start)])
    save_models(models, tmp_path)
    loaded = load_models(tmp_path)
    assert np.array_equal(predict_net_flow(models, data.X), predict_net_flow(loaded, data.X))
    assert np.array_equal(predict_cautious_income(models, data.X), predict_cautious_income(loaded, data.X))


def test_the_committed_model_matches_the_current_code(panel):
    """Fails when the inputs or the scikit-learn version change without retraining."""
    assert (settings.model_dir / MODEL_FILE).exists(), "run: python -m scripts.train_model"
    models = load_models(settings.model_dir)
    assert models["feature_names"] == FEATURE_NAMES
    assert models["versions"]["scikit-learn"] == sklearn.__version__
    assert models["trained_on"]["users"] == [panel.users[u] for u in training_users(panel)]
