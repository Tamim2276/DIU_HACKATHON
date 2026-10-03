"""Simulate the same customers with and without Agam's advice and write the results to backend/reports.

Run from the backend folder:  python -m scripts.impact_test
It takes several minutes: Agam makes a forecast for every customer on every day of the test period.
Add a number to test only one customer in that many, for a quick look:  python -m scripts.impact_test 10
"""
import sys
import time

from app.infrastructure.config.settings import settings
from app.infrastructure.synthetic.impact import format_impact, run_impact_test, save_impact


def main():
    started = time.time()
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    results = run_impact_test(settings, every)
    print(format_impact(results))
    if every == 1:
        path = save_impact(results, settings.report_dir)
        print(f"\nwritten to {path} in {time.time() - started:.0f}s")
    else:
        print(f"\none customer in {every}: a quick look, not saved ({time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
