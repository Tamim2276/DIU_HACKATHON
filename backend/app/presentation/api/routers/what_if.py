from fastapi import APIRouter, Depends

from app.application.use_cases.run_what_if import RunWhatIf
from app.presentation.api.dependencies import app_meta, run_what_if_use_case
from app.presentation.api.schemas.forecast import WhatIfIn, WhatIfOut, what_if_out

router = APIRouter(tags=["forecast"])


@router.post("/users/{user_id}/what-if", response_model=WhatIfOut)
def what_if(
    user_id: str,
    body: WhatIfIn,
    use_case: RunWhatIf = Depends(run_what_if_use_case),
    meta: dict = Depends(app_meta),
) -> WhatIfOut:
    """The forecast again, as it would look if the user took the chosen actions.
    `actions` holds ids from the `actions` list of the forecast call. Nothing is changed or stored."""
    return what_if_out(use_case.execute(user_id, body.as_of or meta["default_day"], body.actions))
