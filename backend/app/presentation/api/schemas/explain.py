"""Shape of the explanation request and response."""
import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.application.use_cases.explain_alert import Explanation


class ExplainIn(BaseModel):
    as_of: dt.date | None = None  # the day to treat as today; the demo day when left out
    language: Literal["bn", "en"] = "bn"  # Bangla or English

    # What the docs page pre-fills, so "Try it out" works without editing. Use it with user U0121.
    model_config = {"json_schema_extra": {"examples": [{"as_of": "2026-08-12", "language": "bn"}]}}


class ExplainOut(BaseModel):
    user_id: str
    as_of: dt.date
    language: str
    has_alert: bool  # False: the text is the all-clear
    text: str  # lines are separated by a line break, paragraphs by an empty line
    facts: dict  # every figure the text was built from


def explain_out(explanation: Explanation) -> ExplainOut:
    facts = explanation.facts
    return ExplainOut(
        user_id=explanation.user.user_id,
        as_of=facts.as_of,
        language=explanation.language,
        has_alert=facts.alert_day is not None,
        text=explanation.text,
        facts=facts.as_dict(),
    )
