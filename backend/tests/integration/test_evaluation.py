"""The full evaluation on July and August, and the saved report."""
from datetime import date

import numpy as np
import pytest

from app.domain.services.shortfall import ALERT_CHANCE, WARNING_DAYS, chance_below, find_shortfall, safety_cushion
from app.infrastructure.config.settings import settings
from app.infrastructure.ml.baselines import BASELINES
from app.infrastructure.ml.evaluation import (
    METRICS_FILE,
    evaluate,
    format_report,
    load_metrics,
    load_personas,
    load_short_days,
    prob_below,
    save_metrics,
)
from app.infrastructure.ml.panel import panel_from_frame, read_transactions
from app.infrastructure.ml.quantile_forecaster import QuantileForecaster
from app.infrastructure.ml.training import QUANTILES, load_models
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository


@pytest.fixture(scope="module")
def results():
    panel = panel_from_frame(read_transactions(settings.data_dir), settings.start_date, settings.end_date)
    personas, labels = load_personas(settings.data_dir, panel)
    return evaluate(panel, load_models(settings.model_dir), load_short_days(settings.data_dir, panel), personas, labels)


# ---------- chance of being under a threshold ----------

LEVELS = np.array([[10.0, 20.0, 30.0, 40.0, 50.0]])  # P10, P25, P50, P75, P90


@pytest.mark.parametrize("threshold, chance", [
    (10.0, 0.10), (20.0, 0.25), (30.0, 0.50), (40.0, 0.75), (50.0, 0.90),  # exactly at a level
    (15.0, 0.175), (25.0, 0.375),  # halfway between two levels
    (-1000.0, 0.01), (1000.0, 0.99),  # far outside: never fully certain
])
def test_chance_of_being_under_a_threshold(threshold, chance):
    assert prob_below(LEVELS, threshold)[0] == pytest.approx(chance)


def test_chance_rises_with_the_threshold():
    chances = [prob_below(LEVELS, t)[0] for t in np.linspace(-20, 80, 60)]
    assert all(later >= earlier for earlier, later in zip(chances, chances[1:]))


# ---------- what is graded here is what the app does ----------

def test_the_graded_chance_equals_the_shortfall_rules_chance():
    rng = np.random.default_rng(1)
    for i in range(500):
        levels = np.sort(rng.uniform(0, 5000, 5))
        if i % 4 == 0:
            levels[: rng.integers(1, 4)] = 0.0  # forecasts cut off at zero have equal lower levels
        threshold = float(rng.uniform(-500, 6000))
        by_rule = chance_below(dict(zip(QUANTILES, levels.tolist())), threshold)
        assert prob_below(levels[None, :], threshold)[0] == pytest.approx(by_rule, abs=1e-9)


def test_the_apps_alert_is_the_alert_that_was_graded():
    repository = CsvTransactionRepository(settings.data_dir)
    forecaster = QuantileForecaster(settings.model_dir)
    fired = 0
    for user in repository.list_users()[::12]:
        for today in (date(2026, 7, 6), date(2026, 7, 27), date(2026, 8, 12)):
            forecast = forecaster.forecast(repository.get_transactions(user.user_id, today), today)
            levels = np.array([[p.p10, p.p25, p.p50, p.p75, p.p90] for p in forecast.points[:WARNING_DAYS]])
            graded_chance = prob_below(levels, safety_cushion(forecast)).max()
            alert = find_shortfall(forecast)
            assert (alert is not None) == (graded_chance >= ALERT_CHANCE), (user.user_id, today)
            if alert is not None:
                fired += 1
                assert alert.chance == pytest.approx(graded_chance, abs=1e-4)
    assert 0 < fired < 75  # some of the 75 forecasts alert and some do not


def test_the_alert_level_used_in_the_app_is_one_of_the_graded_levels(results):
    warn = results["early_warning"]
    assert warn["alert_level_used_in_the_app"] == ALERT_CHANCE
    assert sum("(used in the app)" in point["warning"] for point in warn["warnings"]) == 1


# ---------- the three checks that decide whether the model is good enough ----------

def test_model_beats_every_baseline_at_7_14_and_30_days(results):
    for row in results["error"]["all users"]:
        for unit in ("in_days_of_spending", "in_taka"):
            for name in BASELINES:
                assert row[unit]["model"] < row[unit][name], (row["days_ahead"], unit, name)
    assert results["checks"]["beats_every_baseline_at_7_14_30_days"]


def test_model_also_beats_the_baselines_on_users_it_never_saw(results):
    for row in results["error"]["users it never saw"]:
        assert row["better_than_best_baseline_by"] > 0, row["days_ahead"]


def test_the_range_is_honest(results):
    overall = results["range"]["all users"][-1]
    assert 0.70 <= overall["inside_p10_p90"] <= 0.90
    assert 0.40 <= overall["inside_p25_p75"] <= 0.60
    assert results["checks"]["range_is_honest_70_to_90_percent"]


def test_warnings_beat_the_simple_rule(results):
    warn = results["early_warning"]
    simple, matched = warn["warnings"][0], warn["warnings"][1]
    assert warn["ranking_quality"]["model"] > warn["ranking_quality"]["simple rule"]
    assert matched["false_alarms"] == pytest.approx(simple["false_alarms"], abs=0.01)
    assert matched["caught"] > simple["caught"]
    assert results["checks"]["warnings_beat_the_simple_rule"]


def test_cautious_income_is_cautious(results):
    for row in results["cautious_income"]:
        assert row["real_income_clearly_lower"] <= 0.30, row["days_ahead"]


# ---------- the report itself ----------

def test_report_covers_every_group_and_persona(results):
    assert results["about"]["users"] == {"all": 300, "trained_on": 240, "never_seen": 60}
    assert set(results["error"]) == set(results["range"]) == {"all users", "users it trained on", "users it never saw"}
    assert len(results["by_persona"]) == 5
    assert len(results["error_by_days_ahead"]["model"]) == settings.horizon_days


def test_report_prints_as_text(results):
    text = format_report(results)
    assert "FORECAST ERROR" in text and "EARLY WARNING" in text
    assert text.count("[PASS]") + text.count("[FAIL]") == len(results["checks"])


def test_report_survives_saving_and_loading(results, tmp_path):
    save_metrics(results, tmp_path)
    assert load_metrics(tmp_path) == results


def test_the_committed_report_matches_the_current_model(results):
    """Fails when the model or the data changes without running the evaluation again."""
    assert (settings.report_dir / METRICS_FILE).exists(), "run: python -m scripts.evaluate_model"
    assert load_metrics(settings.report_dir) == results
