"""A single wallet transaction, as the wallet provider records it."""
from dataclasses import dataclass
from datetime import datetime

MONEY_IN = "in"
MONEY_OUT = "out"


@dataclass(frozen=True)
class Transaction:
    txn_id: str
    user_id: str
    timestamp: datetime
    type: str  # salary, send_money, cash_out, merchant_payment, ...
    direction: str  # MONEY_IN or MONEY_OUT
    amount: float  # taka, always positive
    fee: float  # charged on top of the amount, for example on a cash-out
    counterparty: str
    category: str
    channel: str  # app, ussd or agent
    balance_after: float

    def __post_init__(self):
        if self.direction not in (MONEY_IN, MONEY_OUT):
            raise ValueError(f"direction must be 'in' or 'out', got {self.direction!r}")
        if self.amount <= 0 or self.fee < 0:
            raise ValueError("amount must be positive and fee cannot be negative")

    @property
    def signed_amount(self) -> float:
        """Change in the wallet balance: negative for money out, fee included."""
        return self.amount if self.direction == MONEY_IN else -(self.amount + self.fee)
