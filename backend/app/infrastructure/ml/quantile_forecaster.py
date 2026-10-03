"""Forecasts with the saved gradient-boosted quantile models."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np

from app.application.ports.forecaster import Forecaster, NotEnoughHistoryError
from app.domain.entities.forecast import Forecast, ForecastPoint
from app.domain.entities.transaction import Transaction
from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.ml.features import FEATURE_NAMES, MIN_HISTORY_DAYS, build_features, make_calendar
from app.infrastructure.ml.panel import panel_from_transactions
from app.infrastructure.ml.training import load_models, predict_cautious_income, predict_net_flow


class QuantileForecaster(Forecaster):
    def __init__(self, model_dir: Path, cfg: Settings = settings):
        self._models = load_models(model_dir)
        if self._models["feature_names"] != FEATURE_NAMES:
            raise RuntimeError("the saved model was trained with different inputs; run: python -m scripts.train_model")
        self._cfg = cfg

    def forecast(self, transactions: list[Transaction], as_of: date) -> Forecast:
        cfg = self._cfg
        if len({t.user_id for t in transactions}) > 1:
            raise ValueError("a forecast is for one user; the transactions belong to several")
        today = (as_of - cfg.start_date).days
        # daily totals up to today only: anything dated later is dropped here
        panel = panel_from_transactions(transactions, cfg.start_date, as_of) if today >= 0 else None
        if panel is None or not panel.users or today < MIN_HISTORY_DAYS:
            raise NotEnoughHistoryError(
                f"a forecast needs {MIN_HISTORY_DAYS} days of history before {as_of}; "
                f"the earliest possible day is {cfg.start_date + timedelta(days=MIN_HISTORY_DAYS)}")

        calendar = make_calendar(cfg.start_date, today + cfg.horizon_days + 2, cfg.eid_dates)
        rows = build_features(panel.inflow[0], panel.outflow[0], panel.balance[0], calendar, [today])

        # The models work in days of the user's typical spending; turn that back into taka.
        scale, balance = float(rows.scale[0]), float(rows.balance[0])
        levels = np.maximum(balance + predict_net_flow(self._models, rows.X) * scale, 0.0)  # a wallet cannot go below zero
        income = np.maximum.accumulate(predict_cautious_income(self._models, rows.X) * scale)  # income to date never falls

        points = tuple(
            ForecastPoint(as_of + timedelta(days=int(ahead)), *(round(float(v), 2) for v in levels[i]),
                          cautious_income=round(float(income[i]), 2))
            for i, ahead in enumerate(rows.days_ahead)
        )
        return Forecast(user_id=panel.users[0], as_of=as_of, balance=round(balance, 2),
                        typical_daily_spending=round(scale, 2), points=points)
