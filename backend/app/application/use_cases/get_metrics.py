"""The model's test results, for the model report screen."""
from app.application.ports.metrics_store import MetricsStore


class GetMetrics:
    def __init__(self, store: MetricsStore):
        self._store = store

    def execute(self) -> dict:
        return self._store.load()
