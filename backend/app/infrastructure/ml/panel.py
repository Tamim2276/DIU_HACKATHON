"""Daily money in, money out and end-of-day balance for each user."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from app.domain.entities.transaction import Transaction

COLUMNS = ["user_id", "timestamp", "direction", "amount", "fee", "balance_after"]


@dataclass(frozen=True)
class Panel:
    users: list[str]  # one row per user, in this order
    start: date  # the day of column 0
    inflow: np.ndarray  # (users, days) taka received each day
    outflow: np.ndarray  # (users, days) taka paid each day, fees included
    balance: np.ndarray  # (users, days) wallet balance at the end of each day

    @property
    def n_days(self) -> int:
        return self.inflow.shape[1]

    def day_index(self, day: date) -> int:
        return (day - self.start).days


def read_transactions(data_dir: Path) -> pd.DataFrame:
    """The columns the panel needs, for every user."""
    return pd.read_csv(data_dir / "transactions.csv.gz", usecols=COLUMNS, parse_dates=["timestamp"])


def panel_from_frame(frame: pd.DataFrame, start: date, end: date) -> Panel:
    """Daily totals from `start` to `end` inclusive. Transactions outside that period are ignored."""
    n_days = (end - start).days + 1
    first_moment, after_last = pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1)
    frame = frame[(frame["timestamp"] >= first_moment) & (frame["timestamp"] < after_last)]
    frame = frame.sort_values(["user_id", "timestamp"], kind="stable")
    users = list(pd.unique(frame["user_id"]))
    if not users:
        empty = np.zeros((0, n_days))
        return Panel([], start, empty, empty.copy(), empty.copy())

    row = frame["user_id"].map({user: i for i, user in enumerate(users)}).to_numpy()
    day = (frame["timestamp"].dt.normalize() - first_moment).dt.days.to_numpy()
    is_in = (frame["direction"] == "in").to_numpy()
    amount = frame["amount"].to_numpy(float)
    moved = np.where(is_in, amount, amount + frame["fee"].to_numpy(float))

    inflow = np.zeros((len(users), n_days))
    outflow = np.zeros((len(users), n_days))
    np.add.at(inflow, (row[is_in], day[is_in]), moved[is_in])
    np.add.at(outflow, (row[~is_in], day[~is_in]), moved[~is_in])

    # opening balance = the balance just before each user's first transaction
    is_first = np.r_[True, row[1:] != row[:-1]]
    opening = frame["balance_after"].to_numpy(float)[is_first] - np.where(is_in, moved, -moved)[is_first]
    balance = opening[:, None] + np.cumsum(inflow - outflow, axis=1)
    return Panel(users, start, inflow, outflow, balance)


def panel_from_transactions(transactions: list[Transaction], start: date, end: date) -> Panel:
    """The same daily totals, built from one user's transactions. Used when forecasting for a single user."""
    frame = pd.DataFrame({
        "user_id": [t.user_id for t in transactions],
        "timestamp": pd.to_datetime([t.timestamp for t in transactions]),
        "direction": [t.direction for t in transactions],
        "amount": [t.amount for t in transactions],
        "fee": [t.fee for t in transactions],
        "balance_after": [t.balance_after for t in transactions],
    })
    return panel_from_frame(frame, start, end)
