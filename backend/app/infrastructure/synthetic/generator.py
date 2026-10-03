"""Simulates wallet history for the personas, one user and one day at a time.

Everything it produces is synthetic. Besides the transactions a wallet provider
would see, it records the hidden truth for every day (unmet need, borrowing).
The hidden truth is used only to grade the forecast model, never to train it.
The assumptions are listed in docs/SYNTHETIC_DATA.md.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.synthetic.personas import (
    MERCHANT_CATEGORIES,
    MERCHANT_WEIGHTS,
    PERSONAS,
    RECHARGE_AMOUNTS,
    Persona,
)

MONTH_DAYS = 30.4

TRANSACTION_COLUMNS = ["user_id", "timestamp", "type", "direction", "amount", "fee",
                       "counterparty", "category", "channel", "balance_after"]
TRUTH_COLUMNS = ["user_id", "date", "wallet_eod", "cash_in_hand", "desired_spend", "unmet_need",
                 "squeeze", "borrowed", "pending_payments", "missed_payments"]
# A fixed timestamp inside the gzip file, so the same data always gives the same bytes.
GZIP = {"method": "gzip", "mtime": 0}


@dataclass(frozen=True)
class SyntheticData:
    users: pd.DataFrame
    transactions: pd.DataFrame
    truth_daily: pd.DataFrame  # hidden truth per user and day
    user_truth: pd.DataFrame  # hidden settings per user


def _lognormal(rng, sigma: float) -> float:
    """Random multiplier with mean 1."""
    return math.exp(rng.normal(-sigma * sigma / 2, sigma))


def _wallet_id(rng) -> str:
    return f"W-{rng.integers(100000, 1000000)}"


def expected_monthly_net(persona: Persona, has_side: bool) -> float:
    """Money a user of this persona can expect to keep in a month, before spending."""
    income = persona.income
    if income.kind == "daily":
        net = income.mean * income.work_prob * MONTH_DAYS * (1 - persona.supplier_share)
    elif income.kind == "monthly":
        net = income.mean
    else:
        net = income.mean * income.per_month
    return net + (persona.side_income.mean if has_side else 0.0)


def _schedule(persona: Persona, rng, cfg: Settings, n_days: int, scale: float, has_side: bool,
              obligations: list[dict], pay_offset: int, payer: str, side_payer: str) -> dict[int, list[tuple]]:
    """Dated income and due-payment events for one user, keyed by day index."""
    events: dict[int, list[tuple]] = {}

    def put(day: date, event: tuple):
        i = (day - cfg.start_date).days
        if 0 <= i < n_days:
            events.setdefault(i, []).append(event)

    income = persona.income
    for month in pd.period_range(cfg.start_date, cfg.end_date, freq="M"):
        y, m, dim = month.year, month.month, month.days_in_month
        if income.kind == "monthly":
            late = rng.random() < income.late_prob
            delay = int(rng.integers(2, 7)) if late else int(rng.integers(0, 2))
            day = min(max(income.day + pay_offset + delay, 1), dim)
            amount = round(income.mean * scale * _lognormal(rng, income.sigma), -1)
            put(date(y, m, day), ("income", income.type, amount, payer))
        elif income.kind == "lumpy":
            for day in rng.integers(1, dim + 1, rng.poisson(income.per_month)):
                amount = max(round(income.mean * scale * _lognormal(rng, income.sigma), -2), 1000.0)
                put(date(y, m, int(day)), ("income", income.type, amount, payer))
        if has_side:
            side = persona.side_income
            day = min(max(side.day + int(rng.integers(-2, 3)), 1), dim)
            amount = round(side.mean * scale * _lognormal(rng, side.sigma), -2)
            put(date(y, m, day), ("income", side.type, amount, side_payer))
        for ob in obligations:
            day = min(max(ob["day"] + int(rng.choice([-1, 0, 0, 0, 1])), 1), dim)
            # transfers to a person are a fixed amount; bills vary a little each month
            amount = ob["amount"] if ob["type"] == "send_money" else round(ob["amount"] * rng.uniform(0.9, 1.1), -1)
            put(date(y, m, day), ("due", ob["name"], ob["type"], amount, ob["counterparty"]))

    if persona.eid_bonus:
        for eid in cfg.eid_dates:
            bonus = round(persona.eid_bonus * income.mean * scale, -2)
            put(eid - timedelta(days=8), ("income", income.type, bonus, payer))
    return events


def simulate_user(uid: str, persona: Persona, rng: np.random.Generator, cfg: Settings, eid_window: np.ndarray,
                  advisor=None, trace: list | None = None):
    """One user's transactions, hidden daily truth and hidden settings.

    `advisor` and `trace` are used only by the impact test (impact.py). An advisor is called each
    day with the day number, the user's transactions up to yesterday and the amount the user wants
    to spend today, and returns the amount they will try to spend instead. With no advisor the
    simulation runs exactly as before and produces the same data.
    """
    n_days = len(eid_window)
    income = persona.income

    # hidden settings of this user
    scale = math.exp(rng.normal(0, 0.18))  # how large this user's money flows are
    tightness = rng.uniform(*persona.tightness)  # desired spending relative to income
    payday_boost = rng.uniform(0.1, 0.9) if income.kind != "daily" else 0.0  # overspending after income
    cash_out_days = int(rng.integers(2, 6))  # days of cash taken per cash-out
    p_recharge = rng.uniform(0.15, 0.35)
    p_digital = rng.uniform(0.25, 0.6)
    has_side = persona.side_income is not None and rng.random() < persona.side_prob
    channel = "ussd" if rng.random() < persona.ussd_share else "app"
    pay_offset = int(rng.integers(-1, 2))
    supplier_day = int(rng.integers(0, 7))

    obligations = [
        {
            "name": ob.name,
            "type": ob.type,
            "day": int(np.clip(ob.day + rng.integers(-2, 3), 1, 27)),
            "amount": round(ob.amount * scale * rng.uniform(0.85, 1.15), -2),
            "counterparty": _wallet_id(rng),
        }
        for ob in persona.obligations
    ]
    rent_before_income = income.kind == "monthly" and rng.random() < 0.25
    if rent_before_income:
        obligations[0]["day"] = max(1, income.day - int(rng.integers(3, 7)))

    monthly_net = expected_monthly_net(persona, has_side) * scale
    fixed = sum(ob["amount"] for ob in obligations)
    daily_base = max((tightness * monthly_net - fixed) / MONTH_DAYS, 80.0)

    payer = {"salary": f"E-{rng.integers(1000, 10000)}", "remittance": "REMIT"}.get(income.type, _wallet_id(rng))
    side_payer, lender, supplier = _wallet_id(rng), _wallet_id(rng), _wallet_id(rng)
    agents = [f"A-{rng.integers(10000, 100000)}" for _ in range(2)]
    merchants = {c: [f"M-{c[:3].upper()}-{rng.integers(1000, 10000)}" for _ in range(3)] for c in MERCHANT_CATEGORIES}
    events = _schedule(persona, rng, cfg, n_days, scale, has_side, obligations, pay_offset, payer, side_payer)

    wallet = float(round(monthly_net * rng.uniform(0.15, 0.45)))
    cash = float(round(daily_base * rng.uniform(0.5, 2.0)))
    rows, truth, day_rows = [], [], []
    pending: list[list] = []  # [name, type, amount, counterparty, days deferred]
    revenue = [0.0] * n_days
    borrowed_out, borrow_day, squeeze_streak, last_big_income, gap = 0.0, -99, 0, -99, 0
    midnight = datetime.combine(cfg.start_date, time())

    def tx(kind, direction, amount, fee=0.0, counterparty="", category=""):
        nonlocal wallet
        wallet = round(wallet + (amount if direction == "in" else -(amount + fee)), 2)
        day_rows.append([kind, direction, float(amount), float(fee), counterparty, category,
                         "agent" if kind == "cash_out" else channel, wallet])

    for i in range(n_days):
        day_rows.clear()
        eid = bool(eid_window[i])
        weekday = (cfg.start_date + timedelta(days=i)).weekday()

        # 1. Income
        if income.kind == "daily":
            if gap > 0:
                gap -= 1  # illness, repairs, strike: no earnings
            elif rng.random() < 0.008:
                gap = int(rng.integers(3, 7))
            elif rng.random() < income.work_prob:
                amount = income.mean * scale * _lognormal(rng, income.sigma)
                if persona.supplier_share:  # a shop: several customer payments in a day
                    amount *= 1.5 if eid else 1.0
                    for part in rng.dirichlet(np.ones(1 + rng.poisson(4))) * amount:
                        part = max(round(part), 10)
                        tx(income.type, "in", part, counterparty=f"C-{rng.integers(100000, 1000000)}", category="sales")
                        revenue[i] += part
                else:
                    tx(income.type, "in", round(amount), counterparty="PLATFORM", category="income")
        for event in events.get(i, ()):
            if event[0] == "income":
                _, kind, amount, counterparty = event
                tx(kind, "in", amount, counterparty=counterparty, category="income")
                if amount >= 0.25 * monthly_net:
                    last_big_income = i
            else:
                _, name, kind, amount, counterparty = event
                pending.append([name, kind, amount, counterparty, 0])
        if persona.supplier_share and i >= 7 and i % 7 == supplier_day:
            amount = round(persona.supplier_share * sum(revenue[i - 7:i]), -2)
            if amount > 0:
                pending.append(["supplier", "send_money", amount, supplier, 0])
        if rng.random() < 0.004:  # a rare emergency nobody can predict
            amount = round(rng.uniform(1500, 6000) * scale, -2)
            pending.append(["medical", "merchant_payment", amount, merchants["pharmacy"][0], 0])

        # 2. Repay earlier borrowing once there is room
        if borrowed_out > 0 and i - borrow_day >= 2 and wallet >= 2 * borrowed_out:
            tx("send_money", "out", borrowed_out, counterparty=lender, category="p2p")
            borrowed_out = 0.0

        # 3. Due payments come before daily spending; unpaid ones roll to the next day
        still_due, missed = [], 0
        for item in pending:
            name, kind, amount, counterparty, deferred = item
            if wallet >= amount:
                tx(kind, "out", amount, counterparty=counterparty, category=name)
            elif deferred >= 7:  # a week late: pay what is there and give up on the rest
                part = math.floor(wallet / 100) * 100
                if part >= 500:
                    tx(kind, "out", part, counterparty=counterparty, category=name)
                missed += 1
            else:
                item[4] += 1
                still_due.append(item)
        pending = still_due

        # 4. Daily spending, limited by what is actually available
        boost = 1 + payday_boost * math.exp(-(i - last_big_income) / 4)
        level = daily_base * boost * (1.15 if weekday in (4, 5) else 1.0) * (1.45 if eid else 1.0)
        level *= _lognormal(rng, 0.35)
        digital_today = rng.random() < p_digital
        wanted_level = level  # what the user wants to spend today, before any advice
        if advisor is not None:
            level = advisor(i, rows, level)
        need_cash = level * persona.cash_share
        need_digital = level * (1 - persona.cash_share) / p_digital if digital_today else 0.0
        desired = need_cash + need_digital

        paid = 0.0
        if rng.random() < p_recharge:
            recharge = float(rng.choice(RECHARGE_AMOUNTS))
            if wallet >= recharge:
                tx("mobile_recharge", "out", recharge, counterparty="TELCO", category="telecom")
                paid += recharge
        purchase = min(round(max(need_digital - paid, 0.0)), math.floor(wallet))
        if purchase >= 20:
            category = str(rng.choice(MERCHANT_CATEGORIES, p=MERCHANT_WEIGHTS))
            shop = merchants[category][int(rng.integers(0, 3))]
            tx("merchant_payment", "out", purchase, counterparty=shop, category=category)
            paid += purchase
        if cash < need_cash:
            lump = math.ceil(need_cash * cash_out_days / 500) * 500
            affordable = math.floor(wallet / (1 + cfg.cash_out_fee_rate) / 50) * 50
            amount = min(lump, affordable)
            if amount >= 100:
                fee = round(amount * cfg.cash_out_fee_rate, 2)
                tx("cash_out", "out", amount, fee=fee, counterparty=agents[int(rng.integers(0, 2))], category="cash")
                cash += amount
        spent_cash = min(need_cash, cash)
        cash -= spent_cash
        unmet = (need_cash - spent_cash) + max(need_digital - paid, 0.0)
        squeeze = unmet > 0.25 * desired

        # 5. Two squeezed days in a row: borrow from a contact
        squeeze_streak = squeeze_streak + 1 if squeeze else 0
        borrowed = 0.0
        if squeeze_streak >= 2 and borrowed_out == 0:
            borrowed = max(round(level * rng.uniform(3, 6), -2), 300.0)
            tx("receive_money", "in", borrowed, counterparty=lender, category="p2p")
            borrowed_out, borrow_day, squeeze_streak = borrowed, i, 0

        # 6. Savers move a large surplus out of the wallet
        if wallet > 1.6 * monthly_net:
            tx("bank_transfer", "out", round(wallet - monthly_net, -2), counterparty="BANK", category="savings")

        seconds = np.sort(rng.integers(7 * 3600, 23 * 3600, len(day_rows)))
        for second, row in zip(seconds, day_rows):
            rows.append((uid, midnight + timedelta(days=i, seconds=int(second)), *row))
        truth.append((uid, cfg.start_date + timedelta(days=i), wallet, round(cash, 2), round(desired, 2),
                      round(unmet, 2), squeeze, borrowed, len(pending), missed))
        if trace is not None:
            wanted = desired * wanted_level / level if level > 0 else 0.0  # the day's need had no advice been followed
            trace.append((i, wanted, desired, spent_cash + paid, squeeze, borrowed, len(pending), missed))

    hidden = {
        "user_id": uid,
        "persona": persona.key,
        "scale": round(scale, 3),
        "tightness": round(tightness, 3),
        "payday_boost": round(payday_boost, 3),
        "cash_out_days": cash_out_days,
        "rent_before_income": rent_before_income,
        "has_side_income": has_side,
        "monthly_net_income": round(monthly_net),
        "regular_payments": json.dumps(obligations),
    }
    return rows, truth, hidden


def eid_window(cfg: Settings) -> np.ndarray:
    """For every simulated day: is it one of the ten days before an Eid? Those carry extra spending and shop sales."""
    n_days = (cfg.end_date - cfg.start_date).days + 1
    return np.array([
        any(0 < (eid - (cfg.start_date + timedelta(days=i))).days <= 10 for eid in cfg.eid_dates)
        for i in range(n_days)
    ])


def generate(cfg: Settings = settings) -> SyntheticData:
    """The full synthetic data set. The same settings always give the same data."""
    window = eid_window(cfg)
    master = np.random.default_rng(cfg.seed)
    rows, truth, hidden = [], [], []
    for persona in PERSONAS.values():
        for _ in range(cfg.users_per_persona):
            uid = f"U{len(hidden) + 1:04d}"
            rng = np.random.default_rng(master.integers(1 << 32))
            user_rows, user_truth, user_hidden = simulate_user(uid, persona, rng, cfg, window)
            rows += user_rows
            truth += user_truth
            hidden.append(user_hidden)

    transactions = pd.DataFrame(rows, columns=TRANSACTION_COLUMNS)
    transactions.insert(0, "txn_id", [f"T{i:07d}" for i in range(1, len(transactions) + 1)])
    user_truth = pd.DataFrame(hidden)
    users = user_truth[["user_id", "persona"]].copy()
    users["persona_label"] = users["persona"].map({key: p.label for key, p in PERSONAS.items()})
    return SyntheticData(users, transactions, pd.DataFrame(truth, columns=TRUTH_COLUMNS), user_truth)


def save(data: SyntheticData, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    data.users.to_csv(data_dir / "users.csv", index=False, lineterminator="\n")
    data.user_truth.to_csv(data_dir / "user_truth.csv", index=False, lineterminator="\n")
    data.transactions.to_csv(data_dir / "transactions.csv.gz", index=False, lineterminator="\n", compression=GZIP)
    data.truth_daily.to_csv(data_dir / "truth_daily.csv.gz", index=False, lineterminator="\n", compression=GZIP)


def summarize(data: SyntheticData, cfg: Settings = settings) -> pd.DataFrame:
    """Per persona: average money in, cash-out fees, and how often users ran short."""
    months = ((cfg.end_date - cfg.start_date).days + 1) / MONTH_DAYS
    persona = data.user_truth.set_index("user_id")["persona"]
    t, truth = data.transactions, data.truth_daily
    money_in = t[t["direction"] == "in"].groupby("user_id")["amount"].sum()
    borrowed = truth.groupby("user_id")["borrowed"].sum()
    fees = t.groupby("user_id")["fee"].sum()
    return pd.DataFrame({
        "users": persona.groupby(persona).size(),
        "money_in_per_month": ((money_in - borrowed) / months).groupby(persona).mean().round(),
        "cash_out_fees_per_month": (fees / months).groupby(persona).mean().round(),
        "share_of_days_short": truth.groupby("user_id")["squeeze"].mean().groupby(persona).mean().round(3),
        "share_of_users_who_borrowed": (borrowed > 0).groupby(persona).mean().round(2),
    })
