"""Trains the forecasting models.

Six gradient-boosted tree models share the same inputs. Five predict money in
minus money out between today and a day ahead, at the 10%, 25%, 50%, 75% and
90% levels. One predicts money in at the 25% level: the cautious income.
All of them work in units of the user's typical daily spending.
"""
from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.ml.features import (
    FEATURE_NAMES,
    MIN_HISTORY_DAYS,
    Calendar,
    build_features,
    future_flows,
    make_calendar,
)
from app.infrastructure.ml.panel import Panel

MODEL_FILE = "forecaster.joblib"
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
CAUTIOUS_INCOME = 0.25

ORIGIN_STEP = 3  # forecasts on neighbouring days are nearly identical, so every third day is enough
CHECK_SHARE = 0.2  # the most recent share of training days, used to decide when to stop
MAX_ROUNDS = 600
MIN_ROUNDS = 20
PATIENCE = 20  # stop after this many rounds without improvement on the check days
# Kept restrained on purpose: small trees and at least 100 examples per leaf.
# A looser model memorises the training users without doing better on new ones.
TREE_SETTINGS = dict(learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=100,
                     l2_regularization=1.0, random_state=settings.seed)


@dataclass(frozen=True)
class Dataset:
    """Inputs and answers for many users. Flows are in days of the user's typical spending."""
    X: np.ndarray
    net: np.ndarray  # what happened: money in minus money out up to each day ahead
    money_in: np.ndarray  # what happened: money in up to each day ahead
    days_ahead: np.ndarray
    origin: np.ndarray  # day index of "today" for each row
    user: np.ndarray  # panel row of each row's user
    scale: np.ndarray  # taka per day of typical spending
    balance: np.ndarray  # balance at the origin, in taka


def calendar_for(panel: Panel, cfg: Settings = settings) -> Calendar:
    return make_calendar(panel.start, panel.n_days + cfg.horizon_days + 1, cfg.eid_dates)


def training_users(panel: Panel, cfg: Settings = settings) -> list[int]:
    """Panel rows of the users the model may learn from."""
    return [u for u in range(len(panel.users)) if u % cfg.holdout_every != cfg.holdout_every - 1]


def held_out_users(panel: Panel, cfg: Settings = settings) -> list[int]:
    """Panel rows of the users the model never sees."""
    return [u for u in range(len(panel.users)) if u % cfg.holdout_every == cfg.holdout_every - 1]


def training_origins(panel: Panel, cfg: Settings = settings) -> np.ndarray:
    """Origin days whose whole forecast window ends on or before the last training day."""
    last = panel.day_index(cfg.train_end) - cfg.horizon_days
    return np.arange(MIN_HISTORY_DAYS, last + 1, ORIGIN_STEP)


def build_dataset(panel: Panel, calendar: Calendar, users, origins) -> Dataset:
    parts = {name: [] for name in ("X", "net", "money_in", "days_ahead", "origin", "user", "scale", "balance")}
    for u in users:
        rows = build_features(panel.inflow[u], panel.outflow[u], panel.balance[u], calendar, origins)
        net, money_in = future_flows(panel.inflow[u], panel.outflow[u], origins)
        parts["X"].append(rows.X)
        parts["net"].append(net / rows.scale)
        parts["money_in"].append(money_in / rows.scale)
        parts["days_ahead"].append(rows.days_ahead)
        parts["origin"].append(rows.origin)
        parts["user"].append(np.full(len(net), u))
        parts["scale"].append(rows.scale)
        parts["balance"].append(rows.balance)
    return Dataset(np.vstack(parts.pop("X")), **{name: np.concatenate(values) for name, values in parts.items()})


def _fit(X, y, quantile: float, later: np.ndarray, max_rounds: int):
    """Train one model in two passes.

    First fit on the earlier training days and watch the error on the later ones,
    to find how many rounds help before the model starts memorising.
    Then train on all the training days for that many rounds.
    """
    trial = HistGradientBoostingRegressor(loss="quantile", quantile=quantile, max_iter=max_rounds,
                                          early_stopping=True, n_iter_no_change=PATIENCE, **TREE_SETTINGS)
    trial.fit(X[~later], y[~later], X_val=X[later], y_val=y[later])
    rounds = max(int(np.argmax(trial.validation_score_)), min(MIN_ROUNDS, max_rounds))
    model = HistGradientBoostingRegressor(loss="quantile", quantile=quantile, max_iter=rounds,
                                          early_stopping=False, **TREE_SETTINGS)
    return model.fit(X, y), rounds


def train(panel: Panel, cfg: Settings = settings, users=None, max_rounds: int = MAX_ROUNDS, log=print) -> dict:
    """Train all six models and return them with a record of how they were trained."""
    users = training_users(panel, cfg) if users is None else list(users)
    origins = training_origins(panel, cfg)
    data = build_dataset(panel, calendar_for(panel, cfg), users, origins)
    later = data.origin >= origins[int(len(origins) * (1 - CHECK_SHARE))]
    log(f"training on {len(data.X):,} rows: {len(users)} users x {len(origins)} days x {cfg.horizon_days} days ahead")
    log(f"rounds are chosen on the last {int(later.sum()):,} rows (the most recent training days)")

    models = {"net": {}, "money_in": None}
    rounds = {}
    for target, answers, quantiles in (("net", data.net, QUANTILES), ("money_in", data.money_in, (CAUTIOUS_INCOME,))):
        for q in quantiles:
            started = time.time()
            model, used = _fit(data.X, answers, q, later, max_rounds)
            label = f"{'net flow' if target == 'net' else 'money in'} P{round(q * 100)}"
            rounds[label] = used
            log(f"  {label}: {used} rounds, {time.time() - started:.0f}s")
            if target == "net":
                models["net"][q] = model
            else:
                models["money_in"] = model

    return {
        **models,
        "feature_names": list(FEATURE_NAMES),
        "quantiles": QUANTILES,
        "rounds": rounds,
        "trained_on": {
            "rows": len(data.X),
            "users": [panel.users[u] for u in users],
            "first_origin": str(panel.start + timedelta(days=int(origins[0]))),
            "last_origin": str(panel.start + timedelta(days=int(origins[-1]))),
            "train_end": str(cfg.train_end),
        },
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__},
    }


def predict_net_flow(models: dict, X: np.ndarray) -> np.ndarray:
    """(rows, quantiles) forecast of money in minus money out, in days of typical spending.
    Sorted along each row so a lower level is never above a higher one."""
    return np.sort(np.column_stack([models["net"][q].predict(X) for q in models["quantiles"]]), axis=1)


def predict_cautious_income(models: dict, X: np.ndarray) -> np.ndarray:
    """Forecast of money in at the cautious level, in days of typical spending. Never negative."""
    return np.maximum(models["money_in"].predict(X), 0.0)


def save_models(models: dict, model_dir: Path) -> Path:
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_dir / MODEL_FILE
    joblib.dump(models, path, compress=3)
    return path


def load_models(model_dir: Path) -> dict:
    return joblib.load(model_dir / MODEL_FILE)
