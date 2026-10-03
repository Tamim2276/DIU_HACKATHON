from fastapi import APIRouter, Depends

from app.application.use_cases.get_metrics import GetMetrics
from app.presentation.api.dependencies import get_metrics_use_case

router = APIRouter(tags=["model"])


@router.get("/metrics")
def metrics(use_case: GetMetrics = Depends(get_metrics_use_case)) -> dict:
    """How the forecasting model did on July and August 2026, months it never trained on:
    error against the simple baselines, how honest the range is, and how good the warnings are.
    All results come from synthetic data."""
    return use_case.execute()
