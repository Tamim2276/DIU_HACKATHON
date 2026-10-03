"""Reads a file of saved test results: the model's (scripts/evaluate_model.py) or the impact test's."""
import json
from pathlib import Path

from app.application.ports.metrics_store import MetricsStore, MetricsUnavailableError

METRICS_FILE = "metrics.json"


class JsonMetricsStore(MetricsStore):
    def __init__(self, report_dir: Path, file_name: str = METRICS_FILE, made_by: str = "scripts.evaluate_model"):
        self._path = report_dir / file_name
        self._made_by = made_by

    def load(self) -> dict:
        if not self._path.exists():
            raise MetricsUnavailableError(f"no results yet; run: python -m {self._made_by}")
        return json.loads(self._path.read_text(encoding="utf-8"))
