"""Shape of the forecast response, and how a use-case result is turned into it."""
import datetime as dt

from pydantic import BaseModel

from app.application.use_cases.get_forecast import Assessment, ForecastResult
from app.domain.entities.user import User


class PointOut(BaseModel):
    date: dt.date
    p10: float  # cautious
    p25: float
    p50: float  # most likely
    p75: float
    p90: float  # optimistic
    actual: float | None  # the real balance on that day, when the data already has it


class AlertOut(BaseModel):
    date: dt.date  # the first day the risk reaches the alert level
    probability: float  # the highest chance of being under the cushion in the warning window
    gap: float  # taka the cautious forecast falls under the cushion
    cushion: float


class DuePaymentOut(BaseModel):
    recipient: str
    label: str
    date: dt.date
    amount: float


class ActionOut(BaseModel):
    id: str
    title: str
    effect: float  # taka it adds on the forecast's tightest day


class IncomeOut(BaseModel):
    kind: str  # monthly, daily or irregular
    usual_day: int | None
    usual_amount: float | None
    next_day: dt.date | None


class SafeToSpendPartsOut(BaseModel):
    """The figures behind the safe-to-spend number: balance + income - payments - cushion - savings."""
    balance: float
    cautious_income: float
    payments_due: float
    cushion: float
    savings: float
    left_over: float


class ForecastOut(BaseModel):
    user_id: str
    persona: str
    persona_label: str
    as_of: dt.date
    balance: float
    typical_daily_spending: float
    cushion: float
    under_cushion_now: bool
    safe_to_spend: float  # taka per day
    window_days: int
    window_until: dt.date
    safe_to_spend_parts: SafeToSpendPartsOut
    income: IncomeOut
    alert: AlertOut | None
    points: list[PointOut]
    regular_payments: list[DuePaymentOut]  # the ones due in the forecast period
    actions: list[ActionOut]


def forecast_out(user: User, assessment: Assessment, actual: dict[dt.date, float]) -> ForecastOut:
    forecast, plan, alert, income = assessment.forecast, assessment.safe_to_spend, assessment.alert, assessment.income
    return ForecastOut(
        user_id=user.user_id,
        persona=user.persona,
        persona_label=user.persona_label,
        as_of=forecast.as_of,
        balance=forecast.balance,
        typical_daily_spending=forecast.typical_daily_spending,
        cushion=assessment.cushion,
        under_cushion_now=assessment.under_cushion_now,
        safe_to_spend=plan.amount,
        window_days=plan.window_days,
        window_until=plan.until,
        safe_to_spend_parts=SafeToSpendPartsOut(
            balance=plan.balance, cautious_income=plan.cautious_income, payments_due=plan.payments_due,
            cushion=plan.cushion, savings=plan.savings, left_over=round(plan.left_over, 2)),
        income=IncomeOut(kind=income.kind, usual_day=income.usual_day, usual_amount=income.usual_amount,
                         next_day=assessment.next_income_day),
        alert=None if alert is None else AlertOut(date=alert.day, probability=alert.chance, gap=alert.gap,
                                                  cushion=alert.cushion),
        points=[PointOut(date=p.day, p10=p.p10, p25=p.p25, p50=p.p50, p75=p.p75, p90=p.p90, actual=actual.get(p.day))
                for p in forecast.points],
        regular_payments=[DuePaymentOut(recipient=d.recipient, label=d.label, date=d.due, amount=d.amount)
                          for d in assessment.due_payments],
        actions=[ActionOut(id=a.id, title=a.title, effect=a.effect) for a in assessment.actions],
    )


def result_out(result: ForecastResult) -> ForecastOut:
    return forecast_out(result.user, result.assessment, result.actual)
