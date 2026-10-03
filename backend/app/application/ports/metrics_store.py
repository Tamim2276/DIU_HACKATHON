"""What the use cases need from wherever the model's test results are kept."""
from abc import ABC, abstractmethod


class MetricsUnavailableError(LookupError):
    """The model has not been tested yet, so there are no results to show."""


class MetricsStore(ABC):
    @abstractmethod
    def load(self) -> dict:
        """The saved test results. Raises MetricsUnavailableError when there are none."""
