"""Project settings: folders, dates and the assumptions behind the synthetic data."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = BACKEND_DIR / "data"
    model_dir: Path = BACKEND_DIR / "models"
    report_dir: Path = BACKEND_DIR / "reports"

    # Synthetic data
    seed: int = 42
    users_per_persona: int = 60
    start_date: date = date(2025, 10, 1)
    end_date: date = date(2026, 9, 30)
    # Assumed for the simulation. Not an official upay tariff.
    cash_out_fee_rate: float = 0.014
    # Approximate. The real dates depend on the moon sighting.
    eid_dates: tuple[date, ...] = (date(2026, 3, 20), date(2026, 5, 27))

    # Forecast
    horizon_days: int = 30
    # Clean split: no training forecast looks past train_end,
    # and every test forecast starts between test_start and test_end.
    train_end: date = date(2026, 6, 30)
    test_start: date = date(2026, 7, 1)
    test_end: date = date(2026, 8, 31)
    # Every fifth user is kept out of training, to test on users the model never saw.
    holdout_every: int = 5

    # The "today" the app opens on: inside the test period, with 30 real days after it to compare with.
    demo_today: date = date(2026, 8, 12)


settings = Settings()
