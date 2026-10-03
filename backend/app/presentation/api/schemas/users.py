"""Shapes of the user and status responses."""
import datetime as dt

from pydantic import BaseModel


class UserOut(BaseModel):
    user_id: str
    persona: str
    persona_label: str


class MetaOut(BaseModel):
    first_day: dt.date  # the earliest day a forecast can be made for
    last_day: dt.date  # the last day of data
    default_day: dt.date  # the "today" the app opens on
    horizon_days: int
    data: str
