from fastapi import APIRouter, Depends, Path

from app.application.use_cases.explain_alert import ExplainAlert
from app.presentation.api.dependencies import app_meta, explain_alert_use_case
from app.presentation.api.schemas.explain import ExplainIn, ExplainOut, explain_out
from app.presentation.api.schemas.forecast import goal_from

router = APIRouter(tags=["explanation"])


@router.post("/users/{user_id}/explain", response_model=ExplainOut)
def explain(
    body: ExplainIn,
    user_id: str = Path(description="A user id from the users call.", json_schema_extra={"example": "U0121"}),
    use_case: ExplainAlert = Depends(explain_alert_use_case),
    meta: dict = Depends(app_meta),
) -> ExplainOut:
    """The warning in plain sentences, in Bangla (`bn`) or English (`en`): what is likely to happen,
    why, and what to do. A user with no warning gets the all-clear. `facts` holds every figure the
    text was built from; the text contains no other number.

    With a `question`, a language model answers it from the same facts (`source` is `llm`). Its answer
    is only shown if every number in it is one of the facts. Without a key for the model, or when the
    answer fails that check, the standard explanation is returned instead (`source` is `template`)."""
    goal = goal_from(body.goal_amount, body.goal_date)
    return explain_out(use_case.execute(user_id, body.as_of or meta["default_day"], body.language, body.question, goal))
