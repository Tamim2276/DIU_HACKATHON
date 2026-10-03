import datetime as dt

from fastapi import APIRouter, Depends, Path, Query

from app.application.use_cases.get_forecast import GetForecast
from app.presentation.api.dependencies import app_meta, get_forecast_use_case
from app.presentation.api.schemas.forecast import ForecastOut, goal_from, result_out

router = APIRouter(tags=["forecast"])


@router.get("/users/{user_id}/forecast", response_model=ForecastOut)
def get_forecast(
    user_id: str = Path(description="A user id from the users call.", json_schema_extra={"example": "U0121"}),
    as_of: dt.date | None = Query(None, json_schema_extra={"example": "2026-08-12"},
                                  description="The day to treat as today, as YYYY-MM-DD. Only transactions up to "
                                              "this day are used. Leave empty for the demo day."),
    goal_amount: float | None = Query(None, gt=0, description="A savings goal in taka. Send it together with "
                                                                "goal_date. It lowers the safe-to-spend amount."),
    goal_date: dt.date | None = Query(None, description="The day the savings goal should be reached, as YYYY-MM-DD."),
    use_case: GetForecast = Depends(get_forecast_use_case),
    meta: dict = Depends(app_meta),
) -> ForecastOut:
    """The 30-day balance forecast for one user, with the alert, the safe-to-spend number,
    upcoming regular payments and suggested actions."""
    return result_out(use_case.execute(user_id, as_of or meta["default_day"], goal_from(goal_amount, goal_date)))
