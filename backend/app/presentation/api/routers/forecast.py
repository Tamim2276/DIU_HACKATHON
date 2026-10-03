import datetime as dt

from fastapi import APIRouter, Depends, Query

from app.application.use_cases.get_forecast import GetForecast
from app.presentation.api.dependencies import app_meta, get_forecast_use_case
from app.presentation.api.schemas.forecast import ForecastOut, result_out

router = APIRouter(tags=["forecast"])


@router.get("/users/{user_id}/forecast", response_model=ForecastOut)
def get_forecast(
    user_id: str,
    as_of: dt.date | None = Query(None, description="The day to treat as today, as YYYY-MM-DD. "
                                                    "Only transactions up to this day are used."),
    use_case: GetForecast = Depends(get_forecast_use_case),
    meta: dict = Depends(app_meta),
) -> ForecastOut:
    """The 30-day balance forecast for one user, with the alert, the safe-to-spend number,
    upcoming regular payments and suggested actions."""
    return result_out(use_case.execute(user_id, as_of or meta["default_day"]))
