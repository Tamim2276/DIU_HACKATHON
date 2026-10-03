from datetime import timedelta

from app.infrastructure.config.settings import settings


def test_test_period_starts_after_the_training_period():
    assert settings.train_end < settings.test_start <= settings.test_end


def test_every_test_forecast_fits_inside_the_data():
    last_forecast_day = settings.test_end + timedelta(days=settings.horizon_days)
    assert settings.start_date < settings.train_end
    assert last_forecast_day <= settings.end_date
