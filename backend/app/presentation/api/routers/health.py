from fastapi import APIRouter, Depends

from app.presentation.api.dependencies import app_meta
from app.presentation.api.schemas.users import MetaOut

router = APIRouter(tags=["status"])


@router.get("/health")
def health() -> dict:
    """Says the service is up. Hosts and the web app call this first."""
    return {"status": "ok"}


@router.get("/meta", response_model=MetaOut)
def meta(values: dict = Depends(app_meta)) -> MetaOut:
    """The days a forecast can be asked for, the day the app opens on, and the settings of the warning rule."""
    return MetaOut(**values)
