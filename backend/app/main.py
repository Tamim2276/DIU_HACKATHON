"""The API application.

This is the one place where the real implementations (data files, trained
model) are connected to the use cases. Run from the backend folder:

    uvicorn app.main:app --reload
"""
import os
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.application.use_cases.get_forecast import GetForecast
from app.application.use_cases.list_users import ListUsers
from app.infrastructure.config.settings import BACKEND_DIR, settings
from app.infrastructure.ml.features import MIN_HISTORY_DAYS
from app.infrastructure.ml.quantile_forecaster import QuantileForecaster
from app.infrastructure.repositories.csv_transaction_repository import CsvTransactionRepository
from app.presentation.api.errors import register_error_handlers
from app.presentation.api.routers import forecast, health, users

DEFAULT_ORIGINS = "http://localhost:5173"


def allowed_origins() -> list[str]:
    """Addresses of the web app that may call this API, from ALLOWED_ORIGINS (comma separated)."""
    return [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if origin.strip()]


def create_app() -> FastAPI:
    load_dotenv(BACKEND_DIR / ".env")
    repository = CsvTransactionRepository(settings.data_dir)
    forecaster = QuantileForecaster(settings.model_dir)

    app = FastAPI(
        title="Agam API",
        description="Forecasts a wallet balance 30 days ahead and warns before a shortfall. All data is synthetic.",
        version="0.1.0",
    )
    app.state.list_users = ListUsers(repository)
    app.state.get_forecast = GetForecast(repository, forecaster)
    app.state.meta = {
        "first_day": repository.first_day() + timedelta(days=MIN_HISTORY_DAYS),
        "last_day": repository.last_day(),
        "default_day": settings.demo_today,
        "horizon_days": settings.horizon_days,
        "data": "synthetic",
    }

    app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_methods=["GET", "POST"],
                       allow_headers=["*"])
    register_error_handlers(app)
    for router in (health.router, users.router, forecast.router):
        app.include_router(router)
    return app


app = create_app()
