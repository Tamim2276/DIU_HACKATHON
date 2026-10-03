"""Finds the payments a user makes every month, and when the next ones fall due.

A fixed rule, no machine learning. A recipient counts as regular when they
were paid a similar total in at least three of the last four complete months.
"""
from collections import Counter, defaultdict
from datetime import date, timedelta
from statistics import median

from app.domain.entities.regular_payment import DuePayment, RegularPayment
from app.domain.entities.transaction import MONEY_IN, MONEY_OUT, Transaction
from app.domain.services.months import add_months, day_in_month, month_of, previous_months

MONTHS_BACK = 4
MIN_MONTHS = 3
SIMILAR = 0.30  # a month's total may differ from the usual total by this share
SIMILAR_AT_A_SHOP = 0.15  # stricter for shops: a subscription costs the same each month, shopping does not
SAME_DAYS = 5  # a monthly payment falls within this many days of its usual day
# Cash-outs, recharges and bank transfers are everyday spending or saving, never a commitment.
COMMITTED_TYPES = ("send_money", "bill_payment", "merchant_payment")
MONTH_DAYS = 30.4


def find_regular_payments(transactions: list[Transaction], as_of: date) -> list[RegularPayment]:
    """Regular payments seen in the four complete months before the month of `as_of`."""
    months = set(previous_months(as_of, MONTHS_BACK))
    by_recipient: dict[str, dict[tuple, list[Transaction]]] = defaultdict(lambda: defaultdict(list))
    pays_the_user = set()
    for t in transactions:
        if month_of(t.timestamp.date()) not in months:
            continue
        if t.direction == MONEY_IN:
            pays_the_user.add(t.counterparty)
        elif t.direction == MONEY_OUT and t.type in COMMITTED_TYPES:
            by_recipient[t.counterparty][month_of(t.timestamp.date())].append(t)

    found = []
    for recipient, by_month in by_recipient.items():
        if recipient in pays_the_user:
            continue  # money goes both ways: settling up with a contact, not a commitment
        kind = Counter(t.type for paid in by_month.values() for t in paid).most_common(1)[0][0]
        allowed = SIMILAR_AT_A_SHOP if kind == "merchant_payment" else SIMILAR
        totals = {month: sum(t.amount for t in paid) for month, paid in by_month.items()}
        usual_total = median(totals.values())
        similar_months = [month for month, total in totals.items() if abs(total - usual_total) <= allowed * usual_total]
        if len(similar_months) < MIN_MONTHS:
            continue

        payments = [t for month in similar_months for t in by_month[month]]
        per_month = round(median(len(by_month[month]) for month in similar_months))
        usual_day = None
        if per_month == 1:
            usual_day = round(median(t.timestamp.day for t in payments))
            on_time = [m for m in similar_months if any(abs(t.timestamp.day - usual_day) <= SAME_DAYS for t in by_month[m])]
            if len(on_time) < MIN_MONTHS:
                continue  # similar amounts on scattered days: a coincidence, not a commitment
        elif kind == "merchant_payment":
            continue  # a shop visited several times a month is everyday shopping

        found.append(RegularPayment(
            recipient=recipient,
            label=Counter(t.category for t in payments).most_common(1)[0][0],
            type=kind,
            payments_per_month=per_month,
            usual_day=usual_day,
            usual_amount=round(median(t.amount for t in payments), 2),
            monthly_total=round(usual_total, 2),
        ))
    return sorted(found, key=lambda p: (p.usual_day if p.usual_day is not None else 99, p.recipient))


def upcoming_payments(regular: list[RegularPayment], transactions: list[Transaction], as_of: date,
                      days: int = 30) -> list[DuePayment]:
    """The regular payments expected after `as_of`, up to `days` days ahead, soonest first."""
    end = as_of + timedelta(days=days)
    this_month = month_of(as_of)
    paid_out = [t for t in transactions if t.direction == MONEY_OUT and t.timestamp.date() <= as_of]

    due = []
    for payment in regular:
        to_recipient = [t for t in paid_out if t.counterparty == payment.recipient]
        if payment.payments_per_month == 1:
            paid_this_month = any(month_of(t.timestamp.date()) == this_month for t in to_recipient)
            for ahead in range(3):
                month = add_months(this_month, ahead)
                day = day_in_month(month, payment.usual_day)
                if month == this_month:
                    if paid_this_month:
                        continue
                    day = max(day, as_of + timedelta(days=1))  # its day has passed and it is unpaid: expect it now
                if as_of < day <= end:
                    due.append(DuePayment(payment.recipient, payment.label, day, payment.usual_amount))
        else:
            # paid several times a month: keep the same rhythm from the last payment
            last = max((t.timestamp.date() for t in to_recipient), default=as_of)
            every = MONTH_DAYS / payment.payments_per_month
            count = 1
            while (day := last + timedelta(days=round(every * count))) <= end:
                if day > as_of:
                    due.append(DuePayment(payment.recipient, payment.label, day, payment.usual_amount))
                count += 1
    return sorted(due, key=lambda d: (d.due, d.recipient))
