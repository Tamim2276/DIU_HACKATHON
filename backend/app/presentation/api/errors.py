"""Turns the application's errors into HTTP answers with a clear message."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.ports.forecaster import NotEnoughHistoryError
from app.application.ports.metrics_store import MetricsUnavailableError
from app.application.ports.transaction_repository import UserNotFoundError
from app.application.use_cases.explain_alert import UnknownLanguageError
from app.application.use_cases.get_forecast import InvalidDayError, InvalidGoalError
from app.application.use_cases.run_what_if import UnknownActionError


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

    @app.exception_handler(InvalidGoalError)
    def invalid_goal(request: Request, error: InvalidGoalError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(UnknownActionError)
    def unknown_action(request: Request, error: UnknownActionError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(UnknownLanguageError)
    def unknown_language(request: Request, error: UnknownLanguageError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(MetricsUnavailableError)
    def metrics_unavailable(request: Request, error: MetricsUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})
