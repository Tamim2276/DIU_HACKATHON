"""Reads users and transactions from the generated CSV files."""
from datetime import date
from pathlib import Path

import pandas as pd

from app.application.ports.transaction_repository import TransactionRepository, UserNotFoundError
from app.domain.entities.transaction import Transaction
from app.domain.entities.user import User

# Columns with a handful of repeated values; storing them as categories keeps memory low.
REPEATED = {name: "category" for name in ("type", "direction", "category", "channel")}


class CsvTransactionRepository(TransactionRepository):
    def __init__(self, data_dir: Path):
        users = pd.read_csv(data_dir / "users.csv")
        self._users = {row.user_id: User(row.user_id, row.persona, row.persona_label) for row in users.itertuples()}
        frame = pd.read_csv(data_dir / "transactions.csv.gz", parse_dates=["timestamp"], dtype=REPEATED)
        frame = frame.sort_values(["user_id", "timestamp"], kind="stable")
        self._by_user = {user_id: rows for user_id, rows in frame.groupby("user_id", sort=False)}

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def get_user(self, user_id: str) -> User:
        try:
            return self._users[user_id]
        except KeyError:
            raise UserNotFoundError(user_id) from None

    def get_transactions(self, user_id: str, up_to: date) -> list[Transaction]:
        self.get_user(user_id)
        rows = self._by_user.get(user_id)
        if rows is None:
            return []
        rows = rows[rows["timestamp"] < pd.Timestamp(up_to) + pd.Timedelta(days=1)]
        return [
            Transaction(
                txn_id=row.txn_id,
                user_id=row.user_id,
                timestamp=row.timestamp.to_pydatetime(),
                type=row.type,
                direction=row.direction,
                amount=float(row.amount),
                fee=float(row.fee),
                counterparty=row.counterparty,
                category=row.category,
                channel=row.channel,
                balance_after=float(row.balance_after),
            )
            for row in rows.itertuples(index=False)
        ]
