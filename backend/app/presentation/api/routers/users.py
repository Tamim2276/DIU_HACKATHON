from fastapi import APIRouter, Depends

from app.application.use_cases.list_users import ListUsers
from app.presentation.api.dependencies import list_users_use_case
from app.presentation.api.schemas.users import UserOut

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserOut])
def list_users(use_case: ListUsers = Depends(list_users_use_case)) -> list[UserOut]:
    """The sample users the demo can switch between. All of them are simulated."""
    return [UserOut(user_id=u.user_id, persona=u.persona, persona_label=u.persona_label) for u in use_case.execute()]
