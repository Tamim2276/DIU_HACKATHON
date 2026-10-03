"""What the use cases need from wherever wallet data is stored."""
from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.transaction import Transaction
from app.domain.entities.user import User


class UserNotFoundError(LookupError):
    """No user has the requested id."""


class TransactionRepository(ABC):
    @abstractmethod
    def list_users(self) -> list[User]:
        """Every user, in a stable order."""

    @abstractmethod
    def get_user(self, user_id: str) -> User:
        """Raises UserNotFoundError for an unknown id."""

    @abstractmethod
    def first_day(self) -> date:
        """The first day the data covers."""

    @abstractmethod
    def last_day(self) -> date:
        """The last day the data covers."""

    @abstractmethod
    def get_transactions(self, user_id: str, up_to: date) -> list[Transaction]:
        """The user's transactions dated on or before `up_to`, oldest first.

        Nothing after `up_to` is returned, so a forecast made as of that day
        cannot see what happened later. Raises UserNotFoundError for an unknown id.
        """
