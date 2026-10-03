"""Test the saved models on July and August 2026 and write the results to backend/reports.

Run from the backend folder:  python -m scripts.evaluate_model
"""
import time

from app.infrastructure.config.settings import settings
from app.infrastructure.ml.evaluation import evaluate, format_report, load_personas, load_short_days, save_metrics
from app.infrastructure.ml.panel import panel_from_frame, read_transactions
from app.infrastructure.ml.training import load_models


def main():
    started = time.time()
    panel = panel_from_frame(read_transactions(settings.data_dir), settings.start_date, settings.end_date)
    personas, labels = load_personas(settings.data_dir, panel)
    results = evaluate(panel, load_models(settings.model_dir), load_short_days(settings.data_dir, panel),
                       personas, labels, settings)
    path = save_metrics(results, settings.report_dir)
    print(format_report(results))
    print(f"\nwritten to {path} in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
