"""Reads the test results that scripts/evaluate_model.py wrote."""
import json
from pathlib import Path

from app.application.ports.metrics_store import MetricsStore, MetricsUnavailableError

METRICS_FILE = "metrics.json"


class JsonMetricsStore(MetricsStore):
    def __init__(self, report_dir: Path):
        self._path = report_dir / METRICS_FILE

    def load(self) -> dict:
        if not self._path.exists():
            raise MetricsUnavailableError("no test results yet; run: python -m scripts.evaluate_model")
        return json.loads(self._path.read_text(encoding="utf-8"))
