"""The warning, or the all-clear, in sentences a customer can read.

The use case collects the facts: what is likely to happen, why, and what to do.
All of them are already decided here, by the model and the fixed rules. The
explainer only turns them into text.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.application.ports.explainer import (
    INCOME_DAILY,
    INCOME_IRREGULAR,
    INCOME_LATER,
    LANGUAGES,
    LITTLE_CHANGE,
    LOWERS_CHANCE,
    PAYMENTS_DUE,
    REMOVES_ALERT,
    SPENDING_ABOVE_SAFE,
    Explainer,
    Facts,
)
from app.application.use_cases.get_forecast import Assessment, GetForecast, assess
from app.domain.entities.action import Action
from app.domain.entities.alert import Alert
from app.domain.entities.transaction import Transaction
from app.domain.entities.user import User
from app.domain.services.actions import apply_actions, everyday_spending_per_day
from app.domain.services.income_pattern import DAILY, MONTHLY
from app.domain.services.savings_goal import SavingsGoal
from app.domain.services.shortfall import WARNING_DAYS, find_shortfall

NOTICEABLE_DROP = 0.02  # an action "lowers the chance" when the chance falls by at least this much
SMALLEST_AMOUNT = 1.0  # taka; a smaller amount would be written as ৳0, so it is not mentioned


class UnknownLanguageError(ValueError):
    """An explanation was asked for in a language the app does not write."""


@dataclass(frozen=True)
class Explanation:
    user: User
    language: str
    text: str
    facts: Facts  # everything the text was built from
    source: str  # who wrote the text: the fixed sentences or a language model
    question: str | None = None  # the customer's follow-up question, when there was one


def best_action(assessment: Assessment) -> tuple[Action | None, Alert | None]:
    """The suggested action that leaves the lowest chance of a shortfall, and the alert that remains with it.

    Each action is tried on its own, exactly as the what-if call does it.
    """
    best, remaining, lowest = None, assessment.alert, None
    for action in assessment.actions:  # ordered by effect, so the first one wins when two are equally good
        after = find_shortfall(apply_actions(assessment.forecast, [action]), assessment.cushion)
        chance = 0.0 if after is None else after.chance
        if lowest is None or chance < lowest:
            best, remaining, lowest = action, after, chance
    return best, remaining


def gather_facts(assessment: Assessment, history: list[Transaction]) -> Facts:
    """Collect what an explanation may say. `history` is the user's transactions up to the forecast's day."""
    forecast, plan, alert = assessment.forecast, assessment.safe_to_spend, assessment.alert
    as_of, income_day = forecast.as_of, assessment.next_income_day
    usual = everyday_spending_per_day(history, assessment.regular_payments, as_of)

    # The largest payment among those the safe-to-spend amount sets money aside for. With a known income
    # day that amount counts the payments before that day; otherwise the ones up to the last day.
    # A payment made several times a month is spread evenly there, so one is only named when it fits in the total.
    last_counted = plan.until - timedelta(days=1) if income_day == plan.until else plan.until
    counted = [d for d in assessment.due_payments if as_of < d.due <= last_counted and d.amount <= plan.payments_due]
    largest = max(counted, key=lambda d: d.amount, default=None)

    known = dict(
        as_of=as_of,
        balance=forecast.balance,
        cushion=assessment.cushion,
        under_cushion_now=assessment.under_cushion_now,
        warning_days=WARNING_DAYS,
        safe_to_spend=plan.amount,
        window_until=plan.until,
        next_income_day=income_day,
        days_to_income=None if income_day is None else (income_day - as_of).days,
        payments_due=plan.payments_due,
        payment_label=None if largest is None else largest.label,
        payment_day=None if largest is None else largest.due,
        payment_amount=None if largest is None else largest.amount,
        usual_spending=round(usual, 2),
    )
    if alert is None:
        return Facts(**known)

    reasons = []
    if assessment.income.kind == MONTHLY:
        if income_day is not None and income_day > alert.day:
            reasons.append(INCOME_LATER)
    else:
        reasons.append(INCOME_DAILY if assessment.income.kind == DAILY else INCOME_IRREGULAR)
    if plan.payments_due >= SMALLEST_AMOUNT:
        reasons.append(PAYMENTS_DUE)
    if usual >= plan.amount + SMALLEST_AMOUNT:
        reasons.append(SPENDING_ABOVE_SAFE)

    action, after = best_action(assessment)
    if action is None:
        outcome = None
    elif after is None:
        outcome = REMOVES_ALERT
    elif alert.chance - after.chance >= NOTICEABLE_DROP:
        outcome = LOWERS_CHANCE
    else:
        outcome = LITTLE_CHANGE

    return Facts(
        **known,
        alert_day=alert.day,
        alert_chance=alert.chance,
        alert_gap=alert.gap,
        reasons=tuple(reasons),
        action_id=None if action is None else action.id,
        action={} if action is None else dict(action.details),
        outcome=outcome,
        chance_after=after.chance if outcome == LOWERS_CHANCE else None,
    )


class ExplainAlert:
    def __init__(self, get_forecast: GetForecast, explainer: Explainer):
        self._get_forecast = get_forecast
        self._explainer = explainer

    def execute(self, user_id: str, as_of: date, language: str, question: str | None = None,
                goal: SavingsGoal | None = None) -> Explanation:
        """The standard explanation, or with a `question` the answer to it. Both rest on the same facts."""
        if language not in LANGUAGES:
            raise UnknownLanguageError(f"choose a language from: {', '.join(LANGUAGES)}")
        question = (question or "").strip() or None
        user, forecast, history = self._get_forecast.load(user_id, as_of)
        facts = gather_facts(assess(forecast, history, goal), history)
        reply = self._explainer.explain(facts, language, question)
        return Explanation(user, language, reply.text, facts, reply.source, question)
