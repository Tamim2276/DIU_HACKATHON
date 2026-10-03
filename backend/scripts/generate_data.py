"""Generate the synthetic wallet data and write it to backend/data.

Run from the backend folder:  python -m scripts.generate_data
"""
import time

from app.infrastructure.config.settings import settings
from app.infrastructure.synthetic.generator import generate, save, summarize


def main():
    started = time.time()
    data = generate(settings)
    save(data, settings.data_dir)
    print(f"{len(data.users)} users, {len(data.transactions):,} transactions, "
          f"{settings.start_date} to {settings.end_date}, in {time.time() - started:.0f}s")
    print(f"written to {settings.data_dir}")
    print()
    print(summarize(data, settings).to_string())


if __name__ == "__main__":
    main()
