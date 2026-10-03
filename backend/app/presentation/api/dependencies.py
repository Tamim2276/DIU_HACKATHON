"""How the routers reach the use cases.

The use cases are built once in app/main.py and stored on the application.
The routers ask for them here, so nothing in this layer imports a real
repository or model.
"""
from fastapi import Request

from app.application.use_cases.get_forecast import GetForecast
from app.application.use_cases.list_users import ListUsers


def list_users_use_case(request: Request) -> ListUsers:
    return request.app.state.list_users


def get_forecast_use_case(request: Request) -> GetForecast:
    return request.app.state.get_forecast


def app_meta(request: Request) -> dict:
    return request.app.state.meta
