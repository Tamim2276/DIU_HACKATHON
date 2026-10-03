"""The use cases, run with a fake repository and a fake forecaster: no files, no model."""
from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pytest

from app.application.ports.explainer import (
    INCOME_IRREGULAR,
    INCOME_LATER,
    LITTLE_CHANGE,
    LOWERS_CHANCE,
    PAYMENTS_DUE,
    REMOVES_ALERT,
    SPENDING_ABOVE_SAFE,
    Explainer,
)
from app.application.ports.forecaster import Forecaster, NotEnoughHistoryError
from app.application.ports.metrics_store import MetricsStore, MetricsUnavailableError
from app.application.ports.transaction_repository import TransactionRepository, UserNotFoundError
from app.application.use_cases.explain_alert import ExplainAlert, UnknownLanguageError, best_action, gather_facts
from app.application.use_cases.get_forecast import GetForecast, InvalidDayError, assess
from app.application.use_cases.get_metrics import GetMetrics
from app.application.use_cases.list_users import ListUsers
from app.application.use_cases.run_what_if import RunWhatIf, UnknownActionError
from app.domain.entities.action import Action
from app.domain.entities.alert import Alert
from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.entities.regular_payment import DuePayment
from app.domain.entities.transaction import MONEY_OUT, Transaction
from app.domain.entities.user import User
from app.domain.services.income_pattern import MONTHLY, IncomePattern
from app.domain.services.shortfall import find_shortfall

TODAY = date(2026, 8, 12)
LAST_DAY = TODAY + timedelta(days=6)
USER = User("U0001", "student", "University student")


def tx(day_offset: int, balance_after: float, hour: int = 12) -> Transaction:
    return Transaction("T", "U0001", datetime.combine(TODAY + timedelta(days=day_offset), time(hour)),
                       "merchant_payment", MONEY_OUT, 100.0, 0.0, "M-1", "grocery", "app", balance_after)


# before today: two transactions; after today: two on day +2 and one on day +5
HISTORY = [tx(-3, 5000.0), tx(-1, 4000.0), tx(2, 3500.0, hour=9), tx(2, 3000.0, hour=18), tx(5, 2500.0)]


class FakeRepository(TransactionRepository):
    def list_users(self):
        return [USER]

    def get_user(self, user_id):
        if user_id != USER.user_id:
            raise UserNotFoundError(user_id)
        return USER

    def first_day(self):
        return TODAY - timedelta(days=200)

    def last_day(self):
        return LAST_DAY

    def get_transactions(self, user_id, up_to):
        self.get_user(user_id)
        return [t for t in HISTORY if t.timestamp.date() <= up_to]


class FakeForecaster(Forecaster):
    """Returns a fixed forecast and remembers what it was given."""

    def __init__(self, likely: float = 3000.0):
        self.likely = likely
        self.received = []

    def forecast(self, transactions, as_of):
        self.received.append((list(transactions), as_of))
        points = tuple(ForecastPoint(as_of + timedelta(days=d), self.likely * 0.5, self.likely * 0.75, self.likely,
                                     self.likely * 1.25, self.likely * 1.5, cautious_income=0.0) for d in range(1, 31))
        return Forecast("U0001", as_of, balance=transactions[-1].balance_after, typical_daily_spending=400.0, points=points)


def test_list_users_returns_the_repositorys_users():
    assert ListUsers(FakeRepository()).execute() == [USER]


def test_the_forecaster_only_receives_transactions_up_to_today():
    forecaster = FakeForecaster()
    GetForecast(FakeRepository(), forecaster).execute("U0001", TODAY)
    given, as_of = forecaster.received[0]
    assert as_of == TODAY
    assert given == HISTORY[:2]  # the three later transactions never reach it


def test_the_result_holds_the_forecast_and_what_the_rules_made_of_it():
    result = GetForecast(FakeRepository(), FakeForecaster()).execute("U0001", TODAY)
    assessment = result.assessment
    assert result.user == USER
    assert len(assessment.forecast.points) == 30 and assessment.forecast.balance == 4000.0
    assert assessment.cushion == 400.0  # one day of typical spending
    assert assessment.alert == find_shortfall(assessment.forecast) is None  # a comfortable forecast: no alert
    assert not assessment.under_cushion_now
    assert assessment.safe_to_spend.amount >= 0 and assessment.safe_to_spend.window_days == 14
    assert assessment.income.kind == "irregular" and assessment.next_income_day is None


def test_a_forecast_that_runs_low_gives_an_alert():
    result = GetForecast(FakeRepository(), FakeForecaster(likely=200.0)).execute("U0001", TODAY)
    assert result.assessment.alert is not None
    assert result.assessment.alert.day == TODAY + timedelta(days=1)


def test_a_balance_under_the_cushion_today_is_flagged():
    forecaster = FakeForecaster()
    result = GetForecast(FakeRepository(), forecaster).execute("U0001", TODAY + timedelta(days=5))
    assert forecaster.received[0][0][-1].balance_after == 2500.0
    assert not result.assessment.under_cushion_now  # 2,500 is above the 400 cushion

    class LowBalance(FakeForecaster):
        def forecast(self, transactions, as_of):
            base = super().forecast(transactions, as_of)
            return Forecast(base.user_id, base.as_of, 150.0, base.typical_daily_spending, base.points)

    assert GetForecast(FakeRepository(), LowBalance()).execute("U0001", TODAY).assessment.under_cushion_now


def test_actual_balances_come_from_what_happened_after_today():
    result = GetForecast(FakeRepository(), FakeForecaster()).execute("U0001", TODAY)
    days = {offset: TODAY + timedelta(days=offset) for offset in range(1, 8)}
    assert result.actual == {
        days[1]: 4000.0,  # nothing happened: yesterday's balance carries over
        days[2]: 3000.0,  # the last transaction of the day counts
        days[3]: 3000.0,
        days[4]: 3000.0,
        days[5]: 2500.0,
        days[6]: 2500.0,  # the last day of data; later days are unknown
    }
    assert days[7] not in result.actual


def test_unknown_user_is_refused():
    with pytest.raises(UserNotFoundError):
        GetForecast(FakeRepository(), FakeForecaster()).execute("U9999", TODAY)


def test_a_day_outside_the_data_is_refused():
    use_case = GetForecast(FakeRepository(), FakeForecaster())
    with pytest.raises(InvalidDayError):
        use_case.execute("U0001", LAST_DAY + timedelta(days=1))
    with pytest.raises(InvalidDayError):
        use_case.execute("U0001", TODAY - timedelta(days=201))


def test_too_little_history_is_passed_on():
    class Refuses(Forecaster):
        def forecast(self, transactions, as_of):
            raise NotEnoughHistoryError("not enough history")

    with pytest.raises(NotEnoughHistoryError):
        GetForecast(FakeRepository(), Refuses()).execute("U0001", TODAY)


# ---------- what-if ----------

def spent(days_ago: int, amount: float, type: str = "merchant_payment", to: str = "M-GRO-1", fee: float = 0.0) -> Transaction:
    return Transaction("T", "U0001", datetime.combine(TODAY - timedelta(days=days_ago), time(12)), type, MONEY_OUT,
                       amount, fee, to, "grocery", "app", 2000.0)


class SpenderRepository(FakeRepository):
    """A user who spends 300 at shops every day and cashes out 1,000 (fee 14) every five days. Balance 2,000."""

    def get_transactions(self, user_id, up_to):
        self.get_user(user_id)
        history = [spent(d, 300.0) for d in range(30, 0, -1)]
        history += [spent(d, 1000.0, type="cash_out", to="A-1", fee=14.0) for d in (27, 22, 17, 12, 7, 2)]
        return sorted((t for t in history if t.timestamp.date() <= up_to), key=lambda t: t.timestamp)


def what_if(actions):
    """A forecast stuck at 300 taka, under the 400 cushion, for the spender above."""
    return RunWhatIf(GetForecast(SpenderRepository(), FakeForecaster(likely=300.0))).execute("U0001", TODAY, actions)


def test_what_if_with_no_actions_is_the_plain_forecast():
    outcome = what_if([])
    plain = GetForecast(SpenderRepository(), FakeForecaster(likely=300.0)).execute("U0001", TODAY)
    assert outcome.applied == []
    assert outcome.result == plain
    assert outcome.alert_before == plain.assessment.alert is not None


def test_the_spender_is_offered_two_actions():
    assert [a.id for a in what_if([]).result.assessment.actions] == ["keep_to_safe_spend", "pay_directly"]


def test_switching_an_action_on_raises_the_forecast_and_can_remove_the_alert():
    before, after = what_if([]), what_if(["keep_to_safe_spend"])
    action = after.applied[0]
    assert action.id == "keep_to_safe_spend"
    for i, (was, now) in enumerate(zip(before.result.assessment.forecast.points, after.result.assessment.forecast.points)):
        assert now.p50 - was.p50 == pytest.approx(action.changes[i], abs=0.01)
    assert after.alert_before is not None  # there was a shortfall
    assert after.result.assessment.alert is None  # and the action removes it
    # everything except the forecast and the alert stays as it was
    assert after.result.assessment.safe_to_spend == before.result.assessment.safe_to_spend
    assert after.result.assessment.actions == before.result.assessment.actions


def test_several_actions_add_up_and_a_repeated_one_counts_once():
    one = what_if(["keep_to_safe_spend"]).result.assessment.forecast.points[5].p50
    both = what_if(["keep_to_safe_spend", "pay_directly", "pay_directly"])
    assert [a.id for a in both.applied] == ["keep_to_safe_spend", "pay_directly"]
    assert both.result.assessment.forecast.points[5].p50 > one


def test_an_action_that_was_not_suggested_is_refused():
    with pytest.raises(UnknownActionError) as error:
        what_if(["move_payment"])  # a real kind of action, but not suggested to this user
    assert "keep_to_safe_spend" in str(error.value)
    with pytest.raises(UnknownActionError):
        what_if(["take_a_loan"])


# ---------- explanation ----------

class FakeExplainer(Explainer):
    """Writes nothing real: it returns the language and remembers the facts it was given."""

    def __init__(self):
        self.received = []

    def explain(self, facts, language):
        self.received.append((facts, language))
        return f"text in {language}"


def spender_assessment():
    """The spender above with a forecast stuck at 300 taka, under the 400 cushion."""
    history = SpenderRepository().get_transactions("U0001", TODAY)
    return assess(FakeForecaster(likely=300.0).forecast(history, TODAY), history), history


def raise_by(taka: float) -> Action:
    """A made-up action that adds the same amount to the balance on every forecast day."""
    return Action("made_up", "A made-up action.", taka, (taka,) * 30, {})


def test_the_explainer_is_given_the_facts_and_the_language():
    explainer = FakeExplainer()
    use_case = ExplainAlert(GetForecast(SpenderRepository(), FakeForecaster(likely=300.0)), explainer)
    explanation = use_case.execute("U0001", TODAY, "bn")
    assert explanation.user == USER and explanation.language == "bn" and explanation.text == "text in bn"
    assert explainer.received == [(explanation.facts, "bn")]
    assert explanation.facts == gather_facts(*spender_assessment())


def test_the_facts_for_a_user_with_a_warning():
    facts = gather_facts(*spender_assessment())
    assert facts.as_of == TODAY and facts.balance == 2000.0 and facts.cushion == 400.0 and not facts.under_cushion_now
    assert facts.warning_days == 14
    # what: 300 is under the 400 cushion from the first day; the cautious level, 225, is 175 under it
    assert facts.alert_day == TODAY + timedelta(days=1) and facts.alert_chance == 0.8 and facts.alert_gap == 175.0
    # why: no income on record, and about 493 a day spent against a safe amount of 114
    assert facts.reasons == (INCOME_IRREGULAR, SPENDING_ABOVE_SAFE)
    assert facts.next_income_day is None and facts.days_to_income is None
    assert facts.safe_to_spend == 114.0 and facts.window_until == TODAY + timedelta(days=14)
    assert facts.usual_spending == 492.8
    assert facts.payments_due == 0.0 and facts.payment_label is None
    # what to do: keeping to the safe amount removes the warning
    assert facts.action_id == "keep_to_safe_spend" and facts.outcome == REMOVES_ALERT and facts.chance_after is None
    assert facts.action["safe_per_day"] == 114.0


def test_the_facts_for_a_comfortable_user_have_no_warning_reasons_or_action():
    explanation = ExplainAlert(GetForecast(FakeRepository(), FakeForecaster()), FakeExplainer()).execute("U0001", TODAY, "en")
    facts = explanation.facts
    assert facts.alert_day is None and facts.alert_chance is None and facts.alert_gap is None
    assert facts.reasons == () and facts.action_id is None and facts.action == {} and facts.outcome is None
    assert facts.balance == 4000.0 and facts.safe_to_spend == 257.0


def test_the_best_action_is_the_one_that_leaves_the_lowest_chance():
    assessment, history = spender_assessment()
    assert [action.id for action in assessment.actions] == ["keep_to_safe_spend", "pay_directly"]
    backwards = replace(assessment, actions=assessment.actions[::-1])
    action, remaining = best_action(backwards)
    assert action.id == "keep_to_safe_spend" and remaining is None
    assert gather_facts(backwards, history).action_id == "keep_to_safe_spend"


def test_what_the_action_does_to_the_warning():
    assessment, history = spender_assessment()
    # 30 taka more: the chance of being under 400 falls from 80% to about 73%, and the warning stays
    lowers = gather_facts(replace(assessment, actions=[raise_by(30.0)]), history)
    assert lowers.outcome == LOWERS_CHANCE and lowers.chance_after == pytest.approx(0.7333, abs=0.0001)
    # 1 taka more changes the chance by less than a point
    little = gather_facts(replace(assessment, actions=[raise_by(1.0)]), history)
    assert little.outcome == LITTLE_CHANGE and little.chance_after is None
    nothing = gather_facts(replace(assessment, actions=[]), history)
    assert nothing.action_id is None and nothing.outcome is None and nothing.alert_day is not None


def test_the_income_day_is_a_reason_only_when_it_comes_after_the_shortfall():
    assessment, history = spender_assessment()
    monthly = replace(assessment, income=IncomePattern(MONTHLY, 20, 9000.0), next_income_day=TODAY + timedelta(days=8))
    facts = gather_facts(monthly, history)
    assert facts.reasons[0] == INCOME_LATER and facts.days_to_income == 8
    late_alert = replace(monthly, alert=Alert(TODAY + timedelta(days=10), 0.5, 100.0, 400.0))
    assert INCOME_LATER not in gather_facts(late_alert, history).reasons


def test_payments_due_are_a_reason_and_the_largest_one_is_named():
    assessment, history = spender_assessment()
    plan = replace(assessment.safe_to_spend, payments_due=2500.0)  # the window runs to 26 August
    due = [DuePayment("W-RENT", "house_rent", TODAY + timedelta(days=5), 2000.0),
           DuePayment("B-NET", "internet", TODAY + timedelta(days=9), 500.0),
           DuePayment("W-RENT", "house_rent", TODAY + timedelta(days=20), 2000.0)]  # after the window
    facts = gather_facts(replace(assessment, safe_to_spend=plan, due_payments=due), history)
    assert PAYMENTS_DUE in facts.reasons and facts.payments_due == 2500.0
    assert (facts.payment_label, facts.payment_day, facts.payment_amount) == ("house_rent", TODAY + timedelta(days=5), 2000.0)

    # a payment larger than the total set aside (a weekly one, spread over the month) is not named
    weekly = [DuePayment("W-SUP", "supplier", TODAY + timedelta(days=3), 9000.0)] + due
    assert gather_facts(replace(assessment, safe_to_spend=plan, due_payments=weekly), history).payment_label == "house_rent"

    # with a known income day, only payments before that day are counted, so one due on the day is not named
    payday = plan.until
    on_payday = [DuePayment("W-RENT", "house_rent", payday, 2000.0), due[1]]
    facts = gather_facts(replace(assessment, safe_to_spend=plan, due_payments=on_payday, next_income_day=payday,
                                 income=IncomePattern(MONTHLY, payday.day, 9000.0)), history)
    assert facts.payment_label == "internet"


def test_an_unknown_language_is_refused_before_anything_is_worked_out():
    forecaster, explainer = FakeForecaster(), FakeExplainer()
    with pytest.raises(UnknownLanguageError) as error:
        ExplainAlert(GetForecast(FakeRepository(), forecaster), explainer).execute("U0001", TODAY, "fr")
    assert "bn" in str(error.value) and "en" in str(error.value)
    assert forecaster.received == [] and explainer.received == []


def test_explaining_refuses_an_unknown_user_or_day():
    use_case = ExplainAlert(GetForecast(FakeRepository(), FakeForecaster()), FakeExplainer())
    with pytest.raises(UserNotFoundError):
        use_case.execute("U9999", TODAY, "en")
    with pytest.raises(InvalidDayError):
        use_case.execute("U0001", LAST_DAY + timedelta(days=1), "en")


# ---------- model report ----------

class FakeStore(MetricsStore):
    def __init__(self, results=None):
        self.results = results

    def load(self):
        if self.results is None:
            raise MetricsUnavailableError("no test results yet")
        return self.results


def test_metrics_come_from_the_store():
    assert GetMetrics(FakeStore({"checks": {"ok": True}})).execute() == {"checks": {"ok": True}}


def test_missing_metrics_are_reported():
    with pytest.raises(MetricsUnavailableError):
        GetMetrics(FakeStore()).execute()
