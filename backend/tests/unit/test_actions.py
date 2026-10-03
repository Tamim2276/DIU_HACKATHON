"""Actions and what-if, on a hand-made user with known answers.

The user: today is 12 August, income arrives on 24 August (12 days away).
The forecast falls steadily and is tightest on 23 August, the day before income.
"""
from datetime import date, datetime, time, timedelta

import pytest

from app.domain.entities.action import Action
from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.entities.transaction import MONEY_OUT, Transaction
from app.domain.services.actions import (
    ACTION_IDS,
    KEEP_TO_SAFE_SPEND,
    MOVE_PAYMENT,
    PAY_DIRECTLY,
    apply_actions,
    everyday_spending_per_day,
    lowest_day,
    suggest_actions,
)
from app.domain.services.safe_to_spend import DayCheck, SafeToSpend
from app.domain.services.shortfall import find_shortfall

TODAY = date(2026, 8, 12)
PAYDAY = TODAY + timedelta(days=12)
RENT = RegularPayment("W-RENT", "house_rent", "send_money", 1, 20, 2000.0, 2000.0)
RENT_DUE = DuePayment("W-RENT", "house_rent", TODAY + timedelta(days=8), 2000.0)


def make_forecast() -> Forecast:
    """Most likely balance: 3,300 tomorrow, falling 300 a day to 300 on day 11, then 9,000 once income arrives."""
    points = []
    for d in range(1, 31):
        likely = max(3600.0 - 300.0 * d, 0.0) if d < 12 else 9000.0
        points.append(ForecastPoint(TODAY + timedelta(days=d), likely * 0.5, likely * 0.75, likely, likely * 1.25,
                                    likely * 1.5, cautious_income=0.0))
    return Forecast("U0001", TODAY, balance=3600.0, typical_daily_spending=400.0, points=tuple(points))


def spend(days_ago: int, amount: float, type: str = "merchant_payment", to: str = "M-GRO-1", fee: float = 0.0) -> Transaction:
    return Transaction("T", "U0001", datetime.combine(TODAY - timedelta(days=days_ago), time(12)), type, MONEY_OUT,
                       amount, fee, to, "grocery", "app", 0.0)


def history() -> list[Transaction]:
    """The last 30 days: 300 at shops every day, a 1,000 cash-out with a 14 taka fee every five days, and the rent."""
    shops = [spend(d, 300.0) for d in range(30)]
    cash = [spend(d, 1000.0, type="cash_out", to="A-1", fee=14.0) for d in range(0, 30, 5)]
    rent = [spend(22, 2000.0, type="send_money", to="W-RENT")]
    return shops + cash + rent


def plan(amount: float = 200.0) -> SafeToSpend:
    last_day = DayCheck(day=PAYDAY, days=12, cautious_income=0.0, payments_due=0.0, cushion=400.0, savings=0.0,
                        left_over=3200.0)
    return SafeToSpend(amount=amount, window_days=12, until=PAYDAY, balance=3600.0, cautious_income=0.0,
                       payments_due=0.0, cushion=400.0, savings=0.0, tightest=last_day)


def suggest(**changes) -> dict[str, Action]:
    inputs = dict(forecast=make_forecast(), plan=plan(), regular=[RENT], due=[RENT_DUE], transactions=history(),
                  income_day=PAYDAY)
    inputs.update(changes)
    return {action.id: action for action in suggest_actions(**inputs)}


# ---------- the pieces ----------

def test_the_tightest_day_is_the_day_before_income():
    assert lowest_day(make_forecast()) == 10  # position 10 is day 11, 23 August, at 300 taka


def test_everyday_spending_counts_shops_cash_and_fees_but_not_regular_payments():
    # 30 x 300 at shops + 6 x (1,000 + 14) cash-outs = 15,084 over 30 days; the rent is a commitment, not everyday
    assert everyday_spending_per_day(history(), [RENT], TODAY) == pytest.approx(15084 / 30)


# ---------- each action ----------

def test_keeping_to_the_safe_amount_saves_the_difference_every_day_until_income():
    action = suggest()[KEEP_TO_SAFE_SPEND]
    saving = 15084 / 30 - 200  # usual 502.80 a day, safe 200
    assert action.changes[0] == pytest.approx(saving, abs=0.01)
    assert action.changes[11] == pytest.approx(saving * 12, abs=0.01)  # the last day of the window
    assert action.changes[20] == action.changes[11]  # after income arrives the saving stops growing
    assert action.effect == pytest.approx(saving * 11, abs=0.01)  # on the tightest day, day 11


def test_moving_a_payment_helps_from_its_old_day_until_its_new_day():
    action = suggest()[MOVE_PAYMENT]
    assert action.details["from"] == TODAY + timedelta(days=8)
    assert action.details["to"] == PAYDAY + timedelta(days=1)
    assert action.changes[:7] == (0.0,) * 7  # days 1 to 7: nothing changes yet
    assert action.changes[7:12] == (2000.0,) * 5  # days 8 to 12: the 2,000 is still in the wallet
    assert action.changes[12:] == (0.0,) * 18  # from day 13 it has been paid
    assert action.effect == 2000.0


def test_paying_shops_directly_saves_half_the_cash_out_fees():
    action = suggest()[PAY_DIRECTLY]
    per_day = 0.5 * (6 * 14) / 30  # six cash-outs with a 14 taka fee in the last 30 days
    assert action.changes[0] == pytest.approx(per_day, abs=0.01)
    assert action.changes[29] == pytest.approx(per_day * 30, abs=0.01)
    assert action.effect == pytest.approx(per_day * 11, abs=0.01)


# ---------- suggesting ----------

def test_suggestions_are_ordered_by_how_much_they_help_on_the_tightest_day():
    actions = suggest_actions(make_forecast(), plan(), [RENT], [RENT_DUE], history(), PAYDAY)
    assert [a.id for a in actions] == [KEEP_TO_SAFE_SPEND, MOVE_PAYMENT, PAY_DIRECTLY]
    assert [a.effect for a in actions] == sorted((a.effect for a in actions), reverse=True)
    assert all(a.effect > 0 for a in actions)


def test_the_effect_is_the_rise_on_the_tightest_day():
    forecast = make_forecast()
    tightest = lowest_day(forecast)
    for action in suggest().values():
        after = apply_actions(forecast, [action])
        assert after.points[tightest].p50 - forecast.points[tightest].p50 == pytest.approx(action.effect, abs=0.01)


def test_nothing_suggests_a_loan_new_spending_or_a_paid_product():
    actions = suggest()
    assert set(actions) <= set(ACTION_IDS) == {"keep_to_safe_spend", "move_payment", "pay_directly"}
    for action in actions.values():
        words = action.title.lower()
        assert not any(word in words for word in ("loan", "borrow", "credit", "buy", "upgrade", "subscribe"))


def test_no_spending_action_when_the_user_already_spends_less_than_the_safe_amount():
    assert KEEP_TO_SAFE_SPEND not in suggest(plan=plan(amount=900.0))


def test_no_spending_action_when_nothing_is_safe_to_spend():
    assert KEEP_TO_SAFE_SPEND not in suggest(plan=plan(amount=0.0))


def test_no_payment_to_move_without_an_income_day_or_without_a_payment_before_it():
    assert MOVE_PAYMENT not in suggest(income_day=None)
    after_income = DuePayment("W-RENT", "house_rent", PAYDAY + timedelta(days=3), 2000.0)
    assert MOVE_PAYMENT not in suggest(due=[after_income])


def test_a_payment_due_long_before_the_income_is_not_moved():
    # due tomorrow, 11 days before income: moving it that far would mean skipping it
    early = DuePayment("W-RENT", "house_rent", TODAY + timedelta(days=1), 2000.0)
    assert MOVE_PAYMENT not in suggest(due=[early])
    just_close_enough = DuePayment("W-RENT", "house_rent", TODAY + timedelta(days=2), 2000.0)
    assert MOVE_PAYMENT in suggest(due=[just_close_enough])


def test_a_payment_made_several_times_a_month_is_not_moved():
    supplier = RegularPayment("W-S", "supplier", "send_money", 4, None, 16000.0, 64000.0)
    due = [DuePayment("W-S", "supplier", TODAY + timedelta(days=5), 16000.0)]
    assert MOVE_PAYMENT not in suggest(regular=[supplier], due=due)


def test_no_fee_action_without_cash_outs():
    assert PAY_DIRECTLY not in suggest(transactions=[spend(d, 300.0) for d in range(30)])


# ---------- what-if ----------

def test_the_shortfall_disappears_after_the_right_action():
    forecast = make_forecast()
    assert find_shortfall(forecast) is not None  # the balance falls under the 400 taka cushion before income arrives
    after = apply_actions(forecast, [suggest()[KEEP_TO_SAFE_SPEND]])
    assert find_shortfall(after) is None


def test_no_actions_leaves_the_forecast_unchanged():
    assert apply_actions(make_forecast(), []) == make_forecast()


def test_several_actions_add_up_and_levels_stay_in_order():
    forecast, actions = make_forecast(), list(suggest().values())
    after = apply_actions(forecast, actions)
    for i, (before, now) in enumerate(zip(forecast.points, after.points)):
        assert now.p50 - before.p50 == pytest.approx(sum(a.changes[i] for a in actions), abs=0.02)
        assert now.p10 <= now.p25 <= now.p50 <= now.p75 <= now.p90
        assert now.cautious_income == before.cautious_income
    assert after.as_of == forecast.as_of and after.balance == forecast.balance


def test_an_action_can_never_lower_the_balance():
    with pytest.raises(ValueError):
        Action(id=PAY_DIRECTLY, title="x", effect=0.0, changes=(5.0, -1.0))
