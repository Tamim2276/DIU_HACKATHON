"""The safe-to-spend formula, on examples worked by hand."""
from datetime import date, timedelta

import pytest

from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.services.safe_to_spend import plan_safe_to_spend, safe_to_spend_per_day
from app.domain.services.savings_goal import SavingsGoal

TODAY = date(2026, 8, 12)


# ---------- the formula ----------

def test_the_worked_example():
    # (5,000 + 0 - 2,000 - 600) / 12 = 200
    assert safe_to_spend_per_day(balance=5000, cautious_income=0, payments_due=2000, cushion=600, window_days=12) == 200.0


def test_never_below_zero():
    assert safe_to_spend_per_day(balance=1000, cautious_income=0, payments_due=2000, cushion=600, window_days=12) == 0.0


def test_expected_income_raises_it():
    # (5,000 + 1,200 - 2,000 - 600) / 12 = 300
    assert safe_to_spend_per_day(5000, 1200, 2000, 600, 12) == 300.0


def test_a_savings_goal_lowers_it():
    # (5,000 + 0 - 2,000 - 600 - 600) / 12 = 150
    assert safe_to_spend_per_day(5000, 0, 2000, 600, 12, savings=600) == 150.0


def test_the_window_must_be_at_least_one_day():
    with pytest.raises(ValueError):
        safe_to_spend_per_day(5000, 0, 2000, 600, window_days=0)


# ---------- working it out for a user ----------

def make_forecast(income_by_day: dict[int, float] | None = None, balance: float = 5000.0, spending: float = 600.0) -> Forecast:
    """30 days. `income_by_day` gives the cautious income arriving on a day; the forecast holds the running total."""
    income_by_day, total, points = income_by_day or {}, 0.0, []
    for d in range(1, 31):
        total += income_by_day.get(d, 0.0)
        points.append(ForecastPoint(TODAY + timedelta(days=d), 0.0, 1000.0, 2000.0, 3000.0, 4000.0, cautious_income=total))
    return Forecast(user_id="U0001", as_of=TODAY, balance=balance, typical_daily_spending=spending, points=tuple(points))


def due(days_ahead: int, amount: float) -> DuePayment:
    return DuePayment("W-1", "label", TODAY + timedelta(days=days_ahead), amount)


def test_with_a_payday_only_what_comes_before_it_is_counted():
    payday = TODAY + timedelta(days=12)
    forecast = make_forecast({12: 16000.0})  # the salary itself arrives on day 12
    payments = [due(8, 2000), due(12, 3000), due(18, 500)]  # only the first falls before payday
    plan = plan_safe_to_spend(forecast, [], payments, payday)
    assert plan.window_days == 12 and plan.until == payday
    assert plan.cautious_income == 0.0  # the salary belongs to the next period
    assert plan.payments_due == 2000.0
    assert plan.cushion == 600.0  # one day of typical spending
    assert plan.amount == 200.0  # (5,000 + 0 - 2,000 - 600) / 12
    # with no money coming in, the last day leaves the least to spend, and the cushion is kept on it
    assert plan.tightest.day == payday and plan.tightest.days == 12
    assert plan.tightest.cushion == 600.0 and plan.tightest.left_over == 2400.0


def test_small_income_before_payday_is_counted():
    plan = plan_safe_to_spend(make_forecast({5: 1200.0, 12: 16000.0}), [], [due(8, 2000)], TODAY + timedelta(days=12))
    assert plan.cautious_income == 1200.0
    assert plan.amount == 300.0  # (5,000 + 1,200 - 2,000 - 600) / 12


def test_money_arriving_in_the_last_week_before_payday_is_not_counted():
    # it may be the pay itself coming early, so it is not treated as extra income
    plan = plan_safe_to_spend(make_forecast({9: 4000.0, 12: 16000.0}), [], [due(8, 2000)], TODAY + timedelta(days=12))
    assert plan.cautious_income == 0.0
    assert plan.amount == 200.0


def test_without_a_payday_the_window_is_14_days():
    forecast = make_forecast({d: 500.0 for d in range(1, 31)})  # 500 a day: 7,000 in 14 days
    plan = plan_safe_to_spend(forecast, [], [due(5, 3000), due(20, 9000)], income_day=None)
    assert plan.window_days == 14 and plan.until == TODAY + timedelta(days=14)
    assert plan.cautious_income == 7000.0 and plan.payments_due == 3000.0
    assert plan.amount == 600.0  # (5,000 + 7,000 - 3,000 - 600) / 14


def test_payments_made_several_times_a_month_are_spread_over_the_window():
    supplier = RegularPayment("W-S", "supplier", "send_money", payments_per_month=4, usual_day=None,
                              usual_amount=16000.0, monthly_total=64000.0)
    forecast = make_forecast({d: 3000.0 for d in range(1, 31)})  # 42,000 in 14 days
    one_dated = [DuePayment("W-S", "supplier", TODAY + timedelta(days=8), 16000.0)]
    plan = plan_safe_to_spend(forecast, [supplier], one_dated, income_day=None)
    assert plan.payments_due == pytest.approx(64000 * 14 / 30.4, abs=0.01)  # 29,473.68, not the single dated 16,000
    assert plan.amount == 1209.0  # (5,000 + 42,000 - 29,473.68 - 600) / 14 = 1,209.02


def test_income_expected_tomorrow_leaves_one_day_to_cover():
    plan = plan_safe_to_spend(make_forecast({1: 16000.0}), [], [due(1, 3000)], TODAY + timedelta(days=1))
    assert plan.window_days == 1
    assert plan.cautious_income == 0.0 and plan.payments_due == 0.0
    assert plan.amount == 4400.0  # (5,000 - 600) / 1


def test_a_payday_beyond_the_forecast_plans_for_the_whole_forecast():
    plan = plan_safe_to_spend(make_forecast({10: 900.0}), [], [due(25, 1500)], TODAY + timedelta(days=45))
    assert plan.window_days == 30
    assert plan.cautious_income == 900.0 and plan.payments_due == 1500.0
    assert plan.amount == 126.0  # (5,000 + 900 - 1,500 - 600) / 30 = 126.67, rounded down


def test_commitments_larger_than_the_money_give_zero_and_a_negative_left_over():
    plan = plan_safe_to_spend(make_forecast(balance=1000.0), [], [due(3, 2500)], TODAY + timedelta(days=10))
    assert plan.amount == 0.0
    assert plan.tightest.days == 3  # the day the payment is due
    assert plan.tightest.left_over == -1500.0  # 1,000 - 2,500


def test_cushion_and_savings_goal_can_be_set():
    goal = SavingsGoal(1000.0, TODAY + timedelta(days=10))
    plan = plan_safe_to_spend(make_forecast(), [], [], TODAY + timedelta(days=10), goal, cushion=1500.0)
    assert plan.cushion == 1500.0 and plan.savings == 1000.0
    assert plan.amount == 250.0  # (5,000 - 1,500 - 1,000) / 10


# ---------- every day of the window is checked ----------

def test_a_payment_due_before_the_income_arrives_cannot_be_averaged_away():
    # A rider with 100 taka who earns 900 a day and owes 7,300 the day after tomorrow.
    # Over the whole 14 days the money adds up: (100 + 12,600 - 7,300 - 600) / 14 = 342 a day.
    # But by day 2 only 1,800 has come in, so the payment cannot be made whatever is spent.
    forecast = make_forecast({d: 900.0 for d in range(1, 31)}, balance=100.0)
    plan = plan_safe_to_spend(forecast, [], [due(2, 7300)], income_day=None)
    assert plan.amount == 0.0
    assert plan.tightest.days == 2 and plan.tightest.day == TODAY + timedelta(days=2)
    assert plan.tightest.cautious_income == 1800.0 and plan.tightest.payments_due == 7300.0
    assert plan.tightest.left_over == -5400.0  # 100 + 1,800 - 7,300
    # the figures for the whole window are kept, for the explanation
    assert plan.window_days == 14 and plan.cautious_income == 12600.0 and plan.payments_due == 7300.0


def test_the_day_before_money_arrives_can_be_the_tightest():
    # 2,000 today, 1,600 due on day 4, and 6,000 arriving on day 10.
    forecast = make_forecast({10: 6000.0}, balance=2000.0)
    plan = plan_safe_to_spend(forecast, [], [due(4, 1600)], income_day=None)
    # day 4: 400 / 4 = 100.  day 9: 400 / 9 = 44.  day 10: 6,400 / 10 = 640.  day 14: 5,800 / 14 = 414.
    assert plan.amount == 44.0
    assert plan.tightest.days == 9 and plan.tightest.left_over == 400.0


def test_the_cushion_is_kept_on_the_last_day_only():
    early = plan_safe_to_spend(make_forecast({10: 6000.0}, balance=2000.0), [], [due(4, 1600)], income_day=None)
    assert early.tightest.days < early.window_days and early.tightest.cushion == 0.0
    assert early.cushion == 600.0  # still reported, and still kept when the window ends
    last = plan_safe_to_spend(make_forecast(), [], [], income_day=None)
    assert last.tightest.days == last.window_days == 14 and last.tightest.cushion == 600.0
    assert last.amount == 314.0  # (5,000 - 600) / 14


def test_it_is_never_more_than_the_whole_window_allows():
    for income, payments in [({d: 900.0 for d in range(1, 31)}, [due(2, 7300)]), ({10: 6000.0}, [due(4, 1600)]),
                             ({}, [due(8, 2000)]), ({3: 500.0, 12: 800.0}, [due(1, 300), due(13, 4000)])]:
        plan = plan_safe_to_spend(make_forecast(income), [], payments, income_day=None)
        whole = safe_to_spend_per_day(plan.balance, plan.cautious_income, plan.payments_due, plan.cushion, 14)
        assert plan.amount <= whole


def test_savings_are_counted_day_by_day():
    # 700 by day 7 is 100 a day for the first week and nothing after it
    goal = SavingsGoal(700.0, TODAY + timedelta(days=7))
    forecast = make_forecast({10: 6000.0}, balance=2000.0)
    plan = plan_safe_to_spend(forecast, [], [due(4, 1600)], income_day=None, goal=goal)
    assert plan.savings == 700.0
    # day 4: (2,000 - 1,600 - 400) / 4 = 0.  day 7: (2,000 - 1,600 - 700) / 7 is below zero, so nothing is safe
    assert plan.amount == 0.0 and plan.tightest.days == 7
    assert plan.tightest.savings == 700.0 and plan.tightest.left_over == -300.0
