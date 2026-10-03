"""Regular payments and income pattern, on small hand-made histories."""
from datetime import date, datetime, time, timedelta

from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.entities.transaction import MONEY_IN, MONEY_OUT, Transaction
from app.domain.services.income_pattern import DAILY, IRREGULAR, MONTHLY, find_income_pattern, next_income_day
from app.domain.services.months import add_months, day_in_month, previous_months
from app.domain.services.regular_payments import find_regular_payments, upcoming_payments

TODAY = date(2026, 8, 12)  # so the four complete months are April, May, June and July


def pay(day: date, amount: float, to: str = "W-RENT", type: str = "send_money", label: str = "house_rent") -> Transaction:
    return Transaction(txn_id="T", user_id="U0001", timestamp=datetime.combine(day, time(12)), type=type,
                       direction=MONEY_OUT, amount=amount, fee=0.0, counterparty=to, category=label,
                       channel="app", balance_after=0.0)


def receive(day: date, amount: float, sender: str = "E-1000", type: str = "salary") -> Transaction:
    return Transaction(txn_id="T", user_id="U0001", timestamp=datetime.combine(day, time(9)), type=type,
                       direction=MONEY_IN, amount=amount, fee=0.0, counterparty=sender, category="income",
                       channel="app", balance_after=0.0)


def monthly(days_and_amounts, **kwargs) -> list[Transaction]:
    """One payment in each of April to July: [(day of month, amount), ...]."""
    return [pay(date(2026, month, day), amount, **kwargs)
            for month, (day, amount) in zip((4, 5, 6, 7), days_and_amounts) if amount]


# ---------- calendar helpers ----------

def test_month_helpers():
    assert previous_months(TODAY, 4) == [(2026, 4), (2026, 5), (2026, 6), (2026, 7)]
    assert add_months((2026, 11), 3) == (2027, 2)
    assert day_in_month((2026, 2), 31) == date(2026, 2, 28)


# ---------- finding regular payments ----------

def test_a_monthly_payment_is_found_with_its_usual_day_and_amount():
    history = monthly([(5, 5000), (5, 5000), (6, 5000), (4, 5000)])
    assert find_regular_payments(history, TODAY) == [
        RegularPayment(recipient="W-RENT", label="house_rent", type="send_money", payments_per_month=1,
                       usual_day=5, usual_amount=5000.0, monthly_total=5000.0)]


def test_three_months_out_of_four_is_enough_and_two_is_not():
    assert len(find_regular_payments(monthly([(5, 5000), (5, 0), (5, 5000), (5, 5000)]), TODAY)) == 1
    assert find_regular_payments(monthly([(5, 5000), (5, 0), (5, 0), (5, 5000)]), TODAY) == []


def test_very_different_amounts_are_not_regular():
    assert find_regular_payments(monthly([(5, 500), (5, 5000), (5, 800), (5, 12000)]), TODAY) == []


def test_similar_amounts_on_scattered_days_are_not_regular():
    assert find_regular_payments(monthly([(2, 5000), (12, 5000), (22, 5000), (28, 5000)]), TODAY) == []


def test_everyday_spending_is_never_a_regular_payment():
    cash = monthly([(5, 2000)] * 4, to="A-11111", type="cash_out", label="cash")
    recharge = monthly([(7, 50)] * 4, to="TELCO", type="mobile_recharge", label="telecom")
    saving = monthly([(9, 3000)] * 4, to="BANK", type="bank_transfer", label="savings")
    assert find_regular_payments(cash + recharge + saving, TODAY) == []


def test_a_subscription_is_regular_but_ordinary_shopping_is_not():
    subscription = monthly([(15, 1500), (15, 1450), (16, 1550), (15, 1500)], to="M-SUB-1", type="merchant_payment",
                           label="subscriptions")
    one_visit_a_month = monthly([(10, 200), (11, 260), (10, 150), (9, 230)], to="M-GRO-1", type="merchant_payment",
                                label="grocery")
    many_visits = [pay(date(2026, month, day), 180, to="M-FOO-1", type="merchant_payment", label="food")
                   for month in (4, 5, 6, 7) for day in (3, 11, 19, 26)]
    found = find_regular_payments(subscription + one_visit_a_month + many_visits, TODAY)
    assert [p.recipient for p in found] == ["M-SUB-1"]


def test_a_contact_who_also_pays_the_user_is_not_a_commitment():
    repayments = monthly([(20, 800)] * 4, to="W-FRIEND", label="p2p")
    loans = [receive(date(2026, month, 2), 800, sender="W-FRIEND", type="receive_money") for month in (4, 5, 6, 7)]
    assert find_regular_payments(repayments + loans, TODAY) == []


def mondays(first: date, last: date) -> list[date]:
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    return [d for d in days if d.weekday() == 0]


def test_a_weekly_supplier_is_found_as_paid_several_times_a_month():
    history = [pay(day, 16000, to="W-SUPPLIER", label="supplier") for day in mondays(date(2026, 4, 1), date(2026, 8, 12))]
    found = find_regular_payments(history, TODAY)
    assert found == [RegularPayment(recipient="W-SUPPLIER", label="supplier", type="send_money", payments_per_month=4,
                                    usual_day=None, usual_amount=16000.0, monthly_total=64000.0)]
    # the last payment was Monday 10 August; the rhythm continues from there
    assert [d.due for d in upcoming_payments(found, history, TODAY)] == [
        date(2026, 8, 18), date(2026, 8, 25), date(2026, 9, 2), date(2026, 9, 9)]


# ---------- what falls due next ----------

def regular(recipient: str, usual_day: int, amount: float = 1000.0) -> RegularPayment:
    return RegularPayment(recipient, "label", "send_money", 1, usual_day, amount, amount)


def test_a_payment_already_made_this_month_is_next_due_next_month():
    paid = [pay(date(2026, 8, 5), 5000)]
    assert upcoming_payments([regular("W-RENT", 5, 5000)], paid, TODAY) == [
        DuePayment("W-RENT", "label", date(2026, 9, 5), 5000)]


def test_a_payment_still_to_come_this_month_is_due_on_its_usual_day():
    assert upcoming_payments([regular("W-BILL", 20)], [], TODAY) == [DuePayment("W-BILL", "label", date(2026, 8, 20), 1000)]


def test_an_unpaid_payment_whose_day_has_passed_is_expected_tomorrow():
    due = upcoming_payments([regular("W-LATE", 10)], [], TODAY)
    assert [d.due for d in due] == [date(2026, 8, 13), date(2026, 9, 10)]


def test_due_payments_are_soonest_first_and_stay_inside_the_window():
    due = upcoming_payments([regular("W-C", 25), regular("W-A", 14), regular("W-B", 20)], [], TODAY)
    assert [d.recipient for d in due] == ["W-A", "W-B", "W-C"]
    assert all(TODAY < d.due <= TODAY + timedelta(days=30) for d in due)
    assert upcoming_payments([regular("W-A", 14)], [], TODAY, days=1) == []


def test_day_31_falls_on_the_last_day_of_a_shorter_month():
    assert [d.due for d in upcoming_payments([regular("W-X", 31)], [], date(2026, 4, 20))] == [date(2026, 4, 30)]


# ---------- how income arrives ----------

SALARY = [receive(date(2026, 4, 8), 16000), receive(date(2026, 5, 9), 16500), receive(date(2026, 6, 8), 15800),
          receive(date(2026, 7, 13), 16200),  # late in July
          receive(date(2026, 6, 28), 500, sender="W-FRIEND", type="receive_money")]


def test_a_salary_is_a_monthly_income_with_a_usual_day():
    pattern = find_income_pattern(SALARY, TODAY)
    assert pattern.kind == MONTHLY and pattern.usual_day == 8
    assert pattern.usual_amount == 16100.0


def test_next_income_day_before_the_usual_day_is_this_month():
    pattern = find_income_pattern(SALARY, date(2026, 8, 5))
    assert next_income_day(pattern, SALARY, date(2026, 8, 5)) == date(2026, 8, 8)


def test_next_income_day_after_the_salary_arrived_is_next_month():
    history = SALARY + [receive(date(2026, 8, 11), 16000)]
    pattern = find_income_pattern(history, TODAY)
    assert next_income_day(pattern, history, TODAY) == date(2026, 9, 8)


def test_a_large_payment_long_before_the_usual_day_is_not_this_months_salary():
    history = SALARY + [receive(date(2026, 8, 1), 12000, sender="W-OTHER", type="receive_money")]
    pattern = find_income_pattern(history, date(2026, 8, 5))
    assert pattern.usual_day == 8
    assert next_income_day(pattern, history, date(2026, 8, 5)) == date(2026, 8, 8)


def test_an_overdue_salary_is_expected_within_a_few_days():
    pattern = find_income_pattern(SALARY, date(2026, 8, 10))
    assert next_income_day(pattern, SALARY, date(2026, 8, 10)) == date(2026, 8, 13)


def test_income_on_most_days_is_daily():
    start = date(2026, 4, 1)
    history = [receive(start + timedelta(days=i), 900, sender="PLATFORM", type="platform_payout")
               for i in range((TODAY - start).days + 1) if i % 7 != 6]
    pattern = find_income_pattern(history, TODAY)
    assert pattern.kind == DAILY and pattern.usual_day is None
    assert next_income_day(pattern, history, TODAY) is None


def test_large_payments_on_scattered_days_are_irregular():
    history = [receive(date(2026, 4, 3), 12000), receive(date(2026, 4, 25), 6000), receive(date(2026, 5, 17), 30000),
               receive(date(2026, 6, 9), 8000), receive(date(2026, 6, 28), 15000), receive(date(2026, 7, 2), 20000)]
    assert find_income_pattern(history, TODAY).kind == IRREGULAR


def test_the_same_day_with_wildly_different_amounts_is_irregular():
    history = [receive(date(2026, month, 10), amount) for month, amount in ((4, 5000), (5, 20000), (6, 9000), (7, 40000))]
    assert find_income_pattern(history, TODAY).kind == IRREGULAR


def test_no_history_is_irregular():
    assert find_income_pattern([], TODAY).kind == IRREGULAR
    assert find_regular_payments([], TODAY) == []
