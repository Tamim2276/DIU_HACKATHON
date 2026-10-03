"""What the use cases need from whatever produces forecasts."""
from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.forecast import Forecast
from app.domain.entities.transaction import Transaction


class NotEnoughHistoryError(ValueError):
    """The user has too little history before the requested day to forecast from."""


class Forecaster(ABC):
    @abstractmethod
    def forecast(self, transactions: list[Transaction], as_of: date) -> Forecast:
        """Forecast one user's balance for the days after `as_of`.

        Only transactions dated on or before `as_of` are used; later ones are ignored.
        Raises NotEnoughHistoryError when there is too little history.
        """
