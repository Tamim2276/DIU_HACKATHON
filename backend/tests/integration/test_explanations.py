"""Explanations written for generated users, with the real data and the real model.

Every third user, on two days, in both languages: each text must be complete
and contain no number that is not among its facts.
"""
import re
from collections import Counter
from datetime import date

import pytest

from app.application.ports.explainer import LANGUAGES, OUTCOMES, REASONS, numbers_in, unknown_numbers
from app.application.use_cases.explain_alert import gather_facts
from app.application.use_cases.get_forecast import GetForecast, assess
from app.infrastructure.config.settings import settings
from app.infrastructure.llm.template_explainer import TemplateExplainer
from app.infrastructure.ml.quantile_forecaster import QuantileForecaster
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository

DAYS = (date(2026, 8, 12), date(2026, 3, 18))


@pytest.fixture(scope="module")
def explained():
    """(facts, {language: text}) for every third user on each day."""
    repository = CsvTransactionRepository(settings.data_dir)
    get_forecast, explainer = GetForecast(repository, QuantileForecaster(settings.model_dir)), TemplateExplainer()
    cases = []
    for day in DAYS:
        for user in repository.list_users()[::3]:
            _, forecast, history = get_forecast.load(user.user_id, day)
            facts = gather_facts(assess(forecast, history), history)
            cases.append((facts, {language: explainer.explain(facts, language).text for language in LANGUAGES}))
    return cases


def test_no_text_contains_a_number_that_is_not_a_fact(explained):
    assert len(explained) == 200
    for facts, texts in explained:
        for language, text in texts.items():
            assert unknown_numbers(text, facts) == [], (language, text)


def test_every_text_is_complete(explained):
    for _, texts in explained:
        for text in texts.values():
            assert "{" not in text and "None" not in text
            assert not re.search(r"৳(?![0-9০-৯])", text)  # every taka sign is followed by an amount
        assert sorted(numbers_in(texts["bn"])) == sorted(numbers_in(texts["en"]))  # both say the same figures


def test_the_users_cover_warnings_and_all_clears_and_every_kind_of_reason(explained):
    with_warning = [facts for facts, _ in explained if facts.alert_day is not None]
    assert 30 <= len(with_warning) <= 120  # some of each
    assert {reason for facts in with_warning for reason in facts.reasons} == set(REASONS)
    assert {facts.outcome for facts in with_warning if facts.outcome} == set(OUTCOMES)
    assert all(facts.reasons == () and facts.action_id is None
               for facts, _ in explained if facts.alert_day is None)


def test_a_warning_always_has_something_to_say_about_why(explained):
    reasons = Counter(len(facts.reasons) for facts, _ in explained if facts.alert_day is not None)
    assert 0 not in reasons and max(reasons) <= 3
