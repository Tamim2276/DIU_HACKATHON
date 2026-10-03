"""How the routers reach the use cases.

The use cases are built once in app/main.py and stored on the application.
The routers ask for them here, so nothing in this layer imports a real
repository or model.
"""
from fastapi import Request

from app.application.use_cases.explain_alert import ExplainAlert
from app.application.use_cases.get_forecast import GetForecast
from app.application.use_cases.get_metrics import GetMetrics
from app.application.use_cases.list_users import ListUsers
from app.application.use_cases.run_what_if import RunWhatIf


def list_users_use_case(request: Request) -> ListUsers:
    return request.app.state.list_users


def get_forecast_use_case(request: Request) -> GetForecast:
    return request.app.state.get_forecast


def run_what_if_use_case(request: Request) -> RunWhatIf:
    return request.app.state.run_what_if


def get_metrics_use_case(request: Request) -> GetMetrics:
    return request.app.state.get_metrics


def get_impact_use_case(request: Request) -> GetMetrics:
    return request.app.state.get_impact


def explain_alert_use_case(request: Request) -> ExplainAlert:
    return request.app.state.explain_alert


def app_meta(request: Request) -> dict:
    return request.app.state.meta
