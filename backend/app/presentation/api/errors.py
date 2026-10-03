"""Turns the application's errors into HTTP answers with a clear message."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.ports.forecaster import NotEnoughHistoryError
from app.application.ports.transaction_repository import UserNotFoundError
from app.application.use_cases.get_forecast import InvalidDayError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(UserNotFoundError)
    def user_not_found(request: Request, error: UserNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": f"no user with id {error}"})

    @app.exception_handler(NotEnoughHistoryError)
    def not_enough_history(request: Request, error: NotEnoughHistoryError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(InvalidDayError)
    def invalid_day(request: Request, error: InvalidDayError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})
