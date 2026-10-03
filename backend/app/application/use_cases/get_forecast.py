"""Everything the app shows for one user on one day.

The use case reads the user's history, asks the forecaster for a forecast,
and runs the fixed rules on it: alert, regular payments, safe to spend, actions.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.application.ports.forecaster import Forecaster
from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.action import Action
from app.domain.entities.alert import Alert
from app.domain.entities.forecast import Forecast
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.entities.transaction import Transaction
from app.domain.entities.user import User
from app.domain.services.actions import everyday_spending_per_day, suggest_actions
from app.domain.services.income_pattern import IncomePattern, find_income_pattern, next_income_day
from app.domain.services.regular_payments import find_regular_payments, upcoming_payments
from app.domain.services.safe_to_spend import SafeToSpend, plan_safe_to_spend
from app.domain.services.savings_goal import SavingsGoal, SavingsPlan, per_day, problem_with, set_aside
from app.domain.services.shortfall import find_shortfall, safety_cushion


class InvalidDayError(ValueError):
    """The requested day is outside the days the data covers."""


class InvalidGoalError(ValueError):
    """The savings goal has no amount, or a date that cannot be used."""


@dataclass(frozen=True)
class Assessment:
    """What the rules conclude from a forecast and the history behind it."""
    forecast: Forecast
    cushion: float
    alert: Alert | None
    under_cushion_now: bool  # the balance is already under the cushion today
    safe_to_spend: SafeToSpend
    income: IncomePattern
    next_income_day: date | None
    regular_payments: list[RegularPayment]
    due_payments: list[DuePayment]
    actions: list[Action]
    usual_spending: float = 0.0  # taka a day on everyday things over the last 30 days
    savings: SavingsPlan | None = None  # the user's savings goal, when they set one


@dataclass(frozen=True)
class ForecastResult:
    user: User
    assessment: Assessment
    actual: dict[date, float]  # the real end-of-day balance on forecast days the data already covers


def assess(forecast: Forecast, history: list[Transaction], goal: SavingsGoal | None = None) -> Assessment:
    """Run every rule on one forecast. `history` is the user's transactions up to the forecast's day.

    With a savings goal, the money it sets aside is taken out of the safe-to-spend amount,
    and the actions are worked out from that lower amount.
    """
    as_of = forecast.as_of
    regular = find_regular_payments(history, as_of)
    due = upcoming_payments(regular, history, as_of, days=len(forecast.points))
    income = find_income_pattern(history, as_of)
    income_day = next_income_day(income, history, as_of)
    plan = plan_safe_to_spend(forecast, regular, due, income_day)
    savings = None
    if goal is not None:
        problem = problem_with(goal, as_of)
        if problem:
            raise InvalidGoalError(problem)
        aside = set_aside(goal, as_of, plan.window_days)
        savings = SavingsPlan(goal, round(per_day(goal, as_of), 2), round(aside, 2), plan.amount)
        plan = plan_safe_to_spend(forecast, regular, due, income_day, savings=aside)
    cushion = safety_cushion(forecast)
    return Assessment(
        forecast=forecast,
        cushion=round(cushion, 2),
        alert=find_shortfall(forecast, cushion),
        under_cushion_now=forecast.balance < cushion,
        safe_to_spend=plan,
        income=income,
        next_income_day=income_day,
        regular_payments=regular,
        due_payments=due,
        actions=suggest_actions(forecast, plan, regular, due, history, income_day),
        usual_spending=round(everyday_spending_per_day(history, regular, as_of), 2),
        savings=savings,
    )


def actual_balances(later: list[Transaction], forecast: Forecast, last_day: date) -> dict[date, float]:
    """The real end-of-day balance on each forecast day up to `last_day`, from the transactions after today."""
    closing = {t.timestamp.date(): t.balance_after for t in later}  # oldest first, so the day's last one wins
    actual, balance = {}, forecast.balance
    for point in forecast.points:
        if point.day > last_day:
            break
        balance = closing.get(point.day, balance)
        actual[point.day] = balance
    return actual


class GetForecast:
    def __init__(self, repository: TransactionRepository, forecaster: Forecaster):
        self._repository = repository
        self._forecaster = forecaster

    def load(self, user_id: str, as_of: date) -> tuple[User, Forecast, list[Transaction]]:
        """The user, their forecast as of that day, and the history it was made from."""
        user = self._repository.get_user(user_id)
        first, last = self._repository.first_day(), self._repository.last_day()
        if not first <= as_of <= last:
            raise InvalidDayError(f"choose a day between {first} and {last}")
        history = self._repository.get_transactions(user_id, as_of)
        return user, self._forecaster.forecast(history, as_of), history

    def execute(self, user_id: str, as_of: date, goal: SavingsGoal | None = None) -> ForecastResult:
        user, forecast, history = self.load(user_id, as_of)
        # What happened afterwards is only shown next to the forecast. It never reaches the forecaster.
        through = forecast.points[-1].day
        later = self._repository.get_transactions(user_id, through)[len(history):]
        return ForecastResult(user, assess(forecast, history, goal),
                              actual_balances(later, forecast, self._repository.last_day()))
