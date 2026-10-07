"""Simulate the same customers at 25%, 50%, 75% and 100% adoption of Agam's advice.

The main impact test (scripts/impact_test.py) assumes every warned customer follows the
advice in full. This answers the obvious objection to that: what if only a share of
customers actually do?

Run from the backend folder:  python -m scripts.impact_sensitivity
It takes several minutes, about four times as long as impact_test.py (one simulation per
adoption level). Add a number to test only one customer in that many, for a quick look:
python -m scripts.impact_sensitivity 10
"""
import sys
import time

from app.infrastructure.config.settings import settings
from app.infrastructure.synthetic.impact import ADOPTION_FILE, format_adoption_sensitivity, run_adoption_sensitivity, save_impact


def main():
    started = time.time()
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    results = run_adoption_sensitivity(settings, every)
    print(format_adoption_sensitivity(results))
    if every == 1:
        path = save_impact(results, settings.report_dir, ADOPTION_FILE)
        print(f"\nwritten to {path} in {time.time() - started:.0f}s")
    else:
        print(f"\none customer in {every}: a quick look, not saved ({time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
