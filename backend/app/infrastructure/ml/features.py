"""The model's inputs.

One row asks one question: for this user, as of this day (the origin), what
happens over the next h days? Every input uses data up to and including the
origin day only. Money amounts are divided by the user's own typical daily
spending, so one model can serve wallets of very different size.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from app.infrastructure.config.settings import settings

# name -> what it tells the model
FEATURES = {
    "days_ahead": "How many days ahead the question looks.",
    "day_of_month": "Day of the month today.",
    "day_of_week": "Day of the week today.",
    "target_day_of_month": "Day of the month on the day being forecast.",
    "days_to_month_end": "Days left in this month.",
    "pre_eid_days": "How many of the days ahead fall in the ten days before Eid.",
    "balance": "Wallet balance today.",
    "same_days_1_month_ago": "Money in minus money out over the same days one month ago.",
    "same_days_2_months_ago": "The same, two months ago.",
    "same_days_3_months_ago": "The same, three months ago.",
    "same_days_average": "Average of those three months.",
    "same_days_spread": "How much those three months differ from each other.",
    "same_days_money_in": "Average money in over the same days in the last three months.",
    "same_days_money_out": "Average money out over the same days in the last three months.",
    "pace_last_7_days": "The last 7 days' daily net flow, continued for the days ahead.",
    "pace_last_30_days": "The last 30 days' daily net flow, continued for the days ahead.",
    "money_in_pace_30_days": "The last 30 days' daily money in, continued for the days ahead.",
    "money_out_pace_30_days": "The last 30 days' daily money out, continued for the days ahead.",
    "money_in_unevenness": "How uneven daily money in was over the last 30 days.",
    "money_out_unevenness": "How uneven daily money out was over the last 30 days.",
    "money_in_this_month": "Money in so far this month.",
    "money_out_this_month": "Money out so far this month.",
    "money_in_vs_usual": "Money in so far this month, compared with the same point in earlier months.",
    "money_out_vs_usual": "Money out so far this month, compared with the same point in earlier months.",
    "money_in_still_expected": "A usual month's money in, minus what has arrived so far.",
    "money_out_still_expected": "A usual month's money out, minus what has been paid so far.",
    "days_since_large_income": "Days since the last large income (at most 60).",
    "last_large_income": "Size of the last large income.",
    "low_balance_days": "Days in the last 30 on which the balance was under one day of spending.",
}
FEATURE_NAMES = list(FEATURES)

MIN_HISTORY_DAYS = 95  # enough for the same days in each of the last three months
HORIZONS = np.arange(1, settings.horizon_days + 1)


@dataclass(frozen=True)
class Calendar:
    """Facts about each day that are known in advance."""
    day_of_month: np.ndarray
    day_of_week: np.ndarray
    days_to_month_end: np.ndarray
    month_start: np.ndarray  # index of the first day of this day's month
    month_end: np.ndarray  # index of the last day of this day's month
    months_back: dict  # k -> index of the same day k months earlier
    pre_eid_before: np.ndarray  # number of pre-Eid days before each index


def make_calendar(start: date, n_days: int, eid_dates: tuple = settings.eid_dates) -> Calendar:
    """Calendar for `n_days` days from `start`. Pass more days than the data has, so forecasts can look ahead."""
    dates = pd.date_range(start, periods=n_days)
    dom = dates.day.to_numpy()
    dim = dates.days_in_month.to_numpy()
    index = np.arange(n_days)
    month_start = np.maximum(index - (dom - 1), 0)
    months_back = {k: ((dates - pd.DateOffset(months=k)) - dates[0]).days.to_numpy() for k in (1, 2, 3)}
    pre_eid = np.zeros(n_days)
    for eid in eid_dates:
        gap = (pd.Timestamp(eid) - dates).days.to_numpy()
        pre_eid[(gap > 0) & (gap <= 10)] = 1
    return Calendar(dom, dates.dayofweek.to_numpy(), dim - dom, month_start, index - (dom - 1) + dim - 1,
                    months_back, np.concatenate([[0.0], np.cumsum(pre_eid)]))


@dataclass(frozen=True)
class FeatureRows:
    """Inputs for one user: one row per (origin, days ahead), origins in the outer loop."""
    X: np.ndarray  # (rows, features), in units of the user's typical daily spending
    origin: np.ndarray  # day index of "today" for each row
    days_ahead: np.ndarray
    scale: np.ndarray  # the user's typical daily spending at the origin, in taka
    balance: np.ndarray  # balance at the origin, in taka


def _running_total(values: np.ndarray) -> np.ndarray:
    """total[i] = sum of the first i values, so a sum over days a..b is total[b + 1] - total[a]."""
    return np.concatenate([[0.0], np.cumsum(values)])


def build_features(inflow, outflow, balance, calendar: Calendar, origins, horizons=None) -> FeatureRows:
    """Inputs for one user at the given origin day indices. Reads nothing after each origin."""
    O = np.asarray(origins, dtype=int)
    H = HORIZONS if horizons is None else np.asarray(horizons, dtype=int)
    if O.min() < MIN_HISTORY_DAYS:
        raise ValueError(f"a forecast needs {MIN_HISTORY_DAYS} days of history before its origin day")
    if O.max() >= len(inflow):
        raise ValueError("the origin day is after the last day of data")
    if O.max() + H.max() >= len(calendar.day_of_month):
        raise ValueError("the calendar does not reach the last forecast day")

    Og, Hg = O[:, None], H[None, :]
    total_net, total_in, total_out = (_running_total(a) for a in (inflow - outflow, inflow, outflow))

    def daily_rate(total, days, at=O):
        """Average per day over the `days` days ending at each index."""
        return (total[at + 1] - total[np.maximum(at + 1 - days, 0)]) / days

    def unevenness(values, days):
        mean = daily_rate(_running_total(values), days)
        return np.sqrt(np.maximum(daily_rate(_running_total(values * values), days) - mean * mean, 0.0))

    scale = np.maximum(daily_rate(total_out, 60), 1.0)  # the user's typical daily spending
    per_row = scale[:, None]

    # The same days ahead, one, two and three months earlier. A window never passes the origin.
    past_net, past_in, past_out = [], [], []
    to_date_in, to_date_out, month_in, month_out = [], [], [], []
    for k in (1, 2, 3):
        then = calendar.months_back[k][O]
        window_end = np.minimum(then[:, None] + Hg, Og)
        for total, into in ((total_net, past_net), (total_in, past_in), (total_out, past_out)):
            into.append(total[window_end + 1] - total[then + 1][:, None])
        first, last = calendar.month_start[then], calendar.month_end[then]
        to_date_in.append(total_in[then + 1] - total_in[first])
        to_date_out.append(total_out[then + 1] - total_out[first])
        month_in.append(total_in[last + 1] - total_in[first])
        month_out.append(total_out[last + 1] - total_out[first])
    past_net = np.stack(past_net) / per_row

    first = calendar.month_start[O]
    in_so_far = total_in[O + 1] - total_in[first]
    out_so_far = total_out[O + 1] - total_out[first]

    # The most recent large income: a salary, an allowance, a client payment.
    every_day = np.arange(len(inflow))
    is_large = inflow >= 6 * np.maximum(daily_rate(total_out, 60, every_day), 1.0)
    last_large = np.maximum.accumulate(np.where(is_large, every_day, -1))[O]
    has_large = last_large >= 0

    def each_origin(values):
        return np.repeat(values, len(H))

    columns = {
        "days_ahead": np.tile(H, len(O)),
        "day_of_month": each_origin(calendar.day_of_month[O]),
        "day_of_week": each_origin(calendar.day_of_week[O]),
        "target_day_of_month": calendar.day_of_month[Og + Hg].ravel(),
        "days_to_month_end": each_origin(calendar.days_to_month_end[O]),
        "pre_eid_days": (calendar.pre_eid_before[Og + Hg + 1] - calendar.pre_eid_before[Og + 1]).ravel(),
        "balance": each_origin(balance[O] / scale),
        "same_days_1_month_ago": past_net[0].ravel(),
        "same_days_2_months_ago": past_net[1].ravel(),
        "same_days_3_months_ago": past_net[2].ravel(),
        "same_days_average": past_net.mean(0).ravel(),
        "same_days_spread": past_net.std(0).ravel(),
        "same_days_money_in": (np.mean(past_in, 0) / per_row).ravel(),
        "same_days_money_out": (np.mean(past_out, 0) / per_row).ravel(),
        "pace_last_7_days": ((daily_rate(total_net, 7) / scale)[:, None] * Hg).ravel(),
        "pace_last_30_days": ((daily_rate(total_net, 30) / scale)[:, None] * Hg).ravel(),
        "money_in_pace_30_days": ((daily_rate(total_in, 30) / scale)[:, None] * Hg).ravel(),
        "money_out_pace_30_days": ((daily_rate(total_out, 30) / scale)[:, None] * Hg).ravel(),
        "money_in_unevenness": each_origin(unevenness(inflow, 30) / scale),
        "money_out_unevenness": each_origin(unevenness(outflow, 30) / scale),
        "money_in_this_month": each_origin(in_so_far / scale),
        "money_out_this_month": each_origin(out_so_far / scale),
        "money_in_vs_usual": each_origin((in_so_far - np.mean(to_date_in, 0)) / scale),
        "money_out_vs_usual": each_origin((out_so_far - np.mean(to_date_out, 0)) / scale),
        "money_in_still_expected": each_origin((np.mean(month_in, 0) - in_so_far) / scale),
        "money_out_still_expected": each_origin((np.mean(month_out, 0) - out_so_far) / scale),
        "days_since_large_income": each_origin(np.where(has_large, np.minimum(O - last_large, 60), 60)),
        "last_large_income": each_origin(np.where(has_large, inflow[np.maximum(last_large, 0)], 0.0) / scale),
        "low_balance_days": each_origin((balance[Og - np.arange(30)[None, :]] < per_row).sum(1)),
    }
    X = np.column_stack([columns[name] for name in FEATURE_NAMES]).astype(np.float32)
    return FeatureRows(X, each_origin(O), columns["days_ahead"], each_origin(scale), each_origin(balance[O]))


def future_flows(inflow, outflow, origins, horizons=None) -> tuple[np.ndarray, np.ndarray]:
    """What really happened after each origin, in taka: (money in minus money out, money in),
    added up from the day after the origin to each day ahead. These are the answers the model learns from."""
    O = np.asarray(origins, dtype=int)
    H = HORIZONS if horizons is None else np.asarray(horizons, dtype=int)
    if O.max() + H.max() >= len(inflow):
        raise ValueError("the data ends before the last forecast day")
    Og, Hg = O[:, None], H[None, :]
    total_net, total_in = _running_total(inflow - outflow), _running_total(inflow)
    net = total_net[Og + Hg + 1] - total_net[Og + 1]
    money_in = total_in[Og + Hg + 1] - total_in[Og + 1]
    return net.ravel(), money_in.ravel()
