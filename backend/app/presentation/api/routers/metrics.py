from fastapi import APIRouter, Depends

from app.application.use_cases.get_metrics import GetMetrics
from app.presentation.api.dependencies import get_impact_use_case, get_metrics_use_case

router = APIRouter(tags=["model"])


@router.get("/metrics")
def metrics(use_case: GetMetrics = Depends(get_metrics_use_case)) -> dict:
    """How the forecasting model did on July and August 2026, months it never trained on:
    error against the simple baselines, how honest the range is, and how good the warnings are.
    All results come from synthetic data."""
    return use_case.execute()


@router.get("/impact")
def impact(use_case: GetMetrics = Depends(get_impact_use_case)) -> dict:
    """The impact test: the same simulated customers with and without Agam's advice, over July and
    August 2026. It compares hard days, borrowing and overdue payments. All results come from synthetic data."""
    return use_case.execute()
