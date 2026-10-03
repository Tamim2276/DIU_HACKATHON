"""Actions the user could take, and what each would do to the forecast.

Fixed rules, no machine learning. Every action either saves money or shifts
the timing of a payment. The list is closed: nothing here suggests a loan,
new spending or a paid product.
"""
from datetime import date, timedelta

from app.domain.entities.action import Action
from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.entities.transaction import MONEY_OUT, Transaction
from app.domain.services.safe_to_spend import SafeToSpend

KEEP_TO_SAFE_SPEND = "keep_to_safe_spend"
MOVE_PAYMENT = "move_payment"
PAY_DIRECTLY = "pay_directly"
ACTION_IDS = (KEEP_TO_SAFE_SPEND, MOVE_PAYMENT, PAY_DIRECTLY)

EVERYDAY_TYPES = ("cash_out", "merchant_payment", "mobile_recharge")
RECENT_DAYS = 30  # "usual" spending and fees are measured over this many days
REPLACED_SHARE = 0.5  # assumed share of cash-outs that could become direct payments at shops
MAX_MOVE_DAYS = 10  # a payment is only moved if it falls at most this many days before the income
MAX_ACTIONS = 3
SMALLEST_EFFECT = 1.0  # taka; anything smaller is not worth suggesting


def lowest_day(forecast: Forecast) -> int:
    """Position of the forecast day with the lowest most-likely balance: the tightest day."""
    return min(range(len(forecast.points)), key=lambda i: forecast.points[i].p50)


def everyday_spending_per_day(transactions: list[Transaction], regular: list[RegularPayment], as_of: date) -> float:
    """Average taka a day spent on everyday things (cash, shops, recharge) over the last 30 days."""
    committed = {payment.recipient for payment in regular}
    since = as_of - timedelta(days=RECENT_DAYS)
    spent = sum(t.amount + t.fee for t in transactions
                if t.direction == MONEY_OUT and t.type in EVERYDAY_TYPES and t.counterparty not in committed
                and since < t.timestamp.date() <= as_of)
    return spent / RECENT_DAYS


def _day(day: date) -> str:
    return f"{day.day} {day:%b}"


def _action(forecast: Forecast, id: str, title: str, changes: list[float], details: dict) -> Action | None:
    changes = tuple(round(change, 2) for change in changes)
    effect = changes[lowest_day(forecast)]
    if effect < SMALLEST_EFFECT:
        return None  # it does not help on the tightest day, so it is not suggested
    return Action(id=id, title=title, effect=effect, changes=changes, details=details)


def _keep_to_safe_spend(forecast: Forecast, plan: SafeToSpend, everyday: float) -> Action | None:
    """Spend the safe amount each day instead of the usual amount. The saving builds up until the window ends."""
    saving = everyday - plan.amount
    if plan.amount <= 0 or saving <= 0:
        return None
    changes = [saving * min(i + 1, plan.window_days) for i in range(len(forecast.points))]
    title = (f"Keep everyday spending to ৳{plan.amount:,.0f} a day until {_day(plan.until)}. "
             f"You usually spend about ৳{everyday:,.0f}.")
    return _action(forecast, KEEP_TO_SAFE_SPEND, title, changes,
                   {"safe_per_day": plan.amount, "usual_per_day": round(everyday, 2),
                    "saving_per_day": round(saving, 2), "until": plan.until})


def _move_payment(forecast: Forecast, regular: list[RegularPayment], due: list[DuePayment],
                  income_day: date | None) -> Action | None:
    """Pay the largest monthly payment that falls shortly before the income day on the day after it instead.

    Only a payment due within a few days of the income is offered. Moving one by
    weeks would mean skipping it, which is not a change of date.
    """
    if income_day is None:
        return None
    monthly = {payment.recipient for payment in regular if payment.payments_per_month == 1}
    before_income = [d for d in due if d.recipient in monthly and forecast.as_of < d.due < income_day
                     and (income_day - d.due).days <= MAX_MOVE_DAYS]
    if not before_income:
        return None
    payment = max(before_income, key=lambda d: d.amount)
    new_day = income_day + timedelta(days=1)
    changes = [payment.amount if payment.due <= point.day < new_day else 0.0 for point in forecast.points]
    name = payment.label.replace("_", " ")
    title = (f"Move the {name} payment of ৳{payment.amount:,.0f} from {_day(payment.due)} "
             f"to {_day(new_day)}, after your income arrives.")
    return _action(forecast, MOVE_PAYMENT, title, changes,
                   {"recipient": payment.recipient, "label": payment.label, "amount": payment.amount,
                    "from": payment.due, "to": new_day})


def _pay_directly(forecast: Forecast, transactions: list[Transaction]) -> Action | None:
    """Pay shops from the wallet instead of cashing out first, which saves the cash-out fee."""
    since = forecast.as_of - timedelta(days=RECENT_DAYS)
    fees = sum(t.fee for t in transactions
               if t.type == "cash_out" and since < t.timestamp.date() <= forecast.as_of)
    saving = REPLACED_SHARE * fees / RECENT_DAYS
    if saving <= 0:
        return None
    changes = [saving * (i + 1) for i in range(len(forecast.points))]
    title = (f"Pay shops straight from your wallet instead of cashing out first. Doing this for half of "
             f"your cash-outs saves about ৳{saving * RECENT_DAYS:,.0f} a month in fees.")
    return _action(forecast, PAY_DIRECTLY, title, changes,
                   {"fees_last_30_days": round(fees, 2), "saving_per_day": round(saving, 2),
                    "replaced_share": REPLACED_SHARE})


def suggest_actions(forecast: Forecast, plan: SafeToSpend, regular: list[RegularPayment], due: list[DuePayment],
                    transactions: list[Transaction], income_day: date | None) -> list[Action]:
    """Up to three actions for this user, the one that helps most on the tightest day first."""
    everyday = everyday_spending_per_day(transactions, regular, forecast.as_of)
    candidates = [
        _keep_to_safe_spend(forecast, plan, everyday),
        _move_payment(forecast, regular, due, income_day),
        _pay_directly(forecast, transactions),
    ]
    actions = [action for action in candidates if action is not None]
    return sorted(actions, key=lambda action: action.effect, reverse=True)[:MAX_ACTIONS]


def apply_actions(forecast: Forecast, actions: list[Action]) -> Forecast:
    """The forecast as it would look if the user took these actions."""
    points = []
    for i, point in enumerate(forecast.points):
        extra = sum(action.changes[i] for action in actions)
        points.append(ForecastPoint(point.day, *(round(level + extra, 2) for level in
                                                 (point.p10, point.p25, point.p50, point.p75, point.p90)),
                                    cautious_income=point.cautious_income))
    return Forecast(forecast.user_id, forecast.as_of, forecast.balance, forecast.typical_daily_spending, tuple(points))
