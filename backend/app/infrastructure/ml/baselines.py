"""Three simple forecasts with no machine learning. The model has to beat them.

Each baseline is one of the model's own inputs, used directly as the forecast.
The comparison therefore shows what the model adds on top of these inputs.
"""
from __future__ import annotations

import numpy as np

from app.infrastructure.ml.features import FEATURE_NAMES, FeatureRows

# baseline name -> the input it uses as its forecast
BASELINES = {
    "same period last month": "same_days_1_month_ago",
    "average of the last 3 months": "same_days_average",
    "recent daily average": "pace_last_30_days",
}


def baseline_net_flow(rows: FeatureRows, name: str) -> np.ndarray:
    """The baseline's forecast of money in minus money out, in taka, for each row."""
    column = FEATURE_NAMES.index(BASELINES[name])
    return rows.X[:, column].astype(float) * rows.scale


def baseline_balance(rows: FeatureRows, name: str) -> np.ndarray:
    """The baseline's forecast of the wallet balance, in taka, for each row."""
    return rows.balance + baseline_net_flow(rows, name)
