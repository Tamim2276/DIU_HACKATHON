"""The impact test, on a few of the generated customers.

The full test (scripts/impact_test.py) takes several minutes, so these run one customer in sixty.
"""
import json
from datetime import timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from app.infrastructure.config.settings import settings
from app.infrastructure.synthetic import impact
from app.infrastructure.synthetic.impact import (
    EVERY_DAY,
    IMPACT_FILE,
    LEAST_SHARE,
    WHEN_WARNED,
    WITHOUT,
    Follower,
    compare,
    simulate,
    summarize,
)

EVERY = 60  # customers U0001, U0061, U0121, U0181 and U0241: one of each kind


@pytest.fixture(scope="module")
def without():
    return simulate(WITHOUT, settings, EVERY)


@pytest.fixture(scope="module")
def warned():
    return simulate(WHEN_WARNED, settings, EVERY)


def test_without_advice_the_simulation_repeats_the_saved_data(without):
    truth = pd.read_csv(settings.data_dir / "truth_daily.csv.gz", parse_dates=["date"])
    period = truth[(truth["date"].dt.date >= settings.test_start) & (truth["date"].dt.date <= settings.test_end)]
    assert [run.user_id for run in without] == ["U0001", "U0061", "U0121", "U0181", "U0241"]
    for run in without:
        saved = period[period["user_id"] == run.user_id]
        assert len(run.wanted) == len(saved) == (settings.test_end - settings.test_start).days + 1
        assert (run.short_of_plan == saved["squeeze"].to_numpy()).all()
        assert np.allclose(run.borrowed, saved["borrowed"].to_numpy())
        assert np.allclose(run.wanted, saved["desired_spend"].to_numpy(), atol=0.01)  # nothing was cut
        assert run.days_warned == run.days_followed == 0


def test_following_the_advice_changes_what_a_warned_customer_spends(without, warned):
    assert [run.user_id for run in warned] == [run.user_id for run in without]
    assert sum(run.days_warned for run in warned) > 0
    assert sum(run.days_followed for run in warned) > 0
    assert all(run.days_followed <= run.days_warned for run in warned)  # advice is only followed on warned days


def test_adoption_changes_how_many_customers_the_advice_reaches(warned):
    none = simulate(WHEN_WARNED, settings, EVERY, adoption=0.0)
    all_ = simulate(WHEN_WARNED, settings, EVERY, adoption=1.0)
    assert sum(run.days_followed for run in none) == 0
    assert sum(run.days_followed for run in all_) == sum(run.days_followed for run in warned)


def test_a_run_is_summed_up_in_shares_between_zero_and_one(without, warned):
    for runs in (without, warned):
        figures = summarize(runs)
        assert figures["very_hard_days"] <= figures["hard_days"]  # a very hard day is also a hard day
        for name in ("very_hard_days", "hard_days", "days_short_of_plan", "spending_met", "customers_who_borrowed",
                     "days_with_a_payment_overdue", "days_warned", "days_advice_changed_spending"):
            assert 0 <= figures[name] <= 1, name
        assert figures["borrowed_per_customer"] >= 0
    assert summarize(without)["days_advice_changed_spending"] == 0


def test_the_comparison_gives_each_change_with_its_range(without, warned):
    results = compare(without, {WHEN_WARNED: warned}, settings)
    assert set(results) == {"about", "runs", "changes", "by_persona"}
    assert set(results["runs"]) == {WITHOUT, WHEN_WARNED}
    assert results["about"]["customers"] == 5 and results["about"]["days_each"] == 62
    for change in results["changes"][WHEN_WARNED].values():
        assert change["low"] <= change["change"] <= change["high"]
    assert [row["persona"] for row in results["by_persona"]] == ["rider", "garment", "student", "shopkeeper", "freelancer"]
    json.dumps(results)  # everything in it can be written to a file


# ---------- the customer who follows Agam, with a made-up Agam ----------

def follower(policy: str, warning: bool, safe: float, monkeypatch) -> Follower:
    """A follower whose Agam always says the same thing."""
    answer = SimpleNamespace(alert=object() if warning else None, safe_to_spend=SimpleNamespace(amount=safe))
    monkeypatch.setattr(impact, "assess", lambda forecast, history: answer)
    forecaster = SimpleNamespace(forecast=lambda transactions, as_of: None)
    return Follower(forecaster, settings, policy)


FIRST = (settings.test_start - settings.start_date).days


def test_outside_the_test_period_nothing_is_changed(monkeypatch):
    customer = follower(EVERY_DAY, warning=True, safe=10.0, monkeypatch=monkeypatch)
    assert customer(FIRST - 1, [], 400.0) == 400.0
    assert customer((settings.test_end - settings.start_date).days + 1, [], 400.0) == 400.0
    assert customer.days_warned == customer.days_followed == 0


def test_a_warned_customer_keeps_to_the_safe_amount(monkeypatch):
    customer = follower(WHEN_WARNED, warning=True, safe=300.0, monkeypatch=monkeypatch)
    assert customer(FIRST, [], 400.0) == 300.0
    assert customer(FIRST + 1, [], 250.0) == 250.0  # already under the safe amount: nothing to cut
    assert customer.days_warned == 2 and customer.days_followed == 1


def test_nobody_cuts_below_half_of_the_days_need(monkeypatch):
    customer = follower(WHEN_WARNED, warning=True, safe=0.0, monkeypatch=monkeypatch)
    assert customer(FIRST, [], 400.0) == LEAST_SHARE * 400.0


def test_without_a_warning_only_the_every_day_follower_cuts(monkeypatch):
    assert follower(WHEN_WARNED, warning=False, safe=100.0, monkeypatch=monkeypatch)(FIRST, [], 400.0) == 400.0
    assert follower(EVERY_DAY, warning=False, safe=300.0, monkeypatch=monkeypatch)(FIRST, [], 400.0) == 300.0


def test_agam_is_asked_about_yesterday_with_the_transactions_so_far(monkeypatch):
    seen = []
    monkeypatch.setattr(impact, "assess", lambda forecast, history: SimpleNamespace(alert=None, safe_to_spend=SimpleNamespace(amount=0.0)))
    forecaster = SimpleNamespace(forecast=lambda transactions, as_of: seen.append((len(transactions), as_of)))
    customer = Follower(forecaster, settings, WHEN_WARNED)
    stamp = pd.Timestamp(settings.test_start - timedelta(days=1)).to_pydatetime()
    rows = [("U0001", stamp, "merchant_payment", "out", 100.0, 0.0, "M-1", "grocery", "app", 900.0)]
    customer(FIRST, rows, 400.0)
    customer(FIRST + 1, rows + rows, 400.0)
    assert seen == [(1, settings.test_start - timedelta(days=1)), (2, settings.test_start)]


def test_the_saved_results_can_be_read_by_the_api():
    path = settings.report_dir / IMPACT_FILE
    if not path.exists():
        pytest.skip("the full impact test has not been run: python -m scripts.impact_test")
    results = json.loads(path.read_text(encoding="utf-8"))
    assert results["about"]["customers"] == 300
    assert set(results["runs"]) == {WITHOUT, WHEN_WARNED, EVERY_DAY}
