"""Tests the trained models on July and August 2026, months they never trained on.

Three questions, each answered against the simple baselines:
  1. How far is the most likely forecast from the real balance?
  2. Is the forecast range honest: does the real balance fall inside P10-P90 about 80% of the time?
  3. Do warnings come before real shortfalls? The real shortfalls come from the
     simulator's hidden truth, which the models never saw.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from app.domain.services.shortfall import ALERT_CHANCE, CUSHION_DAYS, WARNING_DAYS
from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.ml.baselines import BASELINES
from app.infrastructure.ml.features import FEATURE_NAMES
from app.infrastructure.ml.panel import Panel
from app.infrastructure.ml.training import (
    QUANTILES,
    build_dataset,
    calendar_for,
    held_out_users,
    predict_cautious_income,
    predict_net_flow,
)

METRICS_FILE = "metrics.json"
REPORTED_DAYS = (7, 14, 30)
WARNING_WINDOW = WARNING_DAYS  # the warning window, cushion and alert level come from the shortfall rule itself,
ALERT_LEVELS = (0.5, 0.4, 0.3)  # so what is graded here is exactly what the app does; other levels are for comparison
BEST_SIMPLE = "average of the last 3 months"
INCOME_TOLERANCE = 0.5  # days of typical spending


def prob_below(levels: np.ndarray, threshold: float) -> np.ndarray:
    """Chance that the real value is under `threshold`, given the forecast levels on the last axis.

    The levels are P10, P25, P50, P75 and P90. Between two levels the chance is
    read off a straight line; beyond the outer levels the line is continued.
    """
    q = np.array(QUANTILES)
    below = levels[..., :1] - (levels[..., 1:2] - levels[..., :1]) * q[0] / (q[1] - q[0])
    above = levels[..., -1:] + (levels[..., -1:] - levels[..., -2:-1]) * (1 - q[-1]) / (q[-1] - q[-2])
    values = np.concatenate([below, levels, above], axis=-1)
    chances = np.concatenate([[0.0], q, [1.0]])
    j = np.clip((values <= threshold).sum(-1) - 1, 0, values.shape[-1] - 2)
    low = np.take_along_axis(values, j[..., None], -1)[..., 0]
    high = np.take_along_axis(values, j[..., None] + 1, -1)[..., 0]
    share = np.clip((threshold - low) / np.maximum(high - low, 1e-9), 0, 1)
    return np.clip(chances[j] + share * (chances[j + 1] - chances[j]), 0.01, 0.99)


def load_short_days(data_dir: Path, panel: Panel) -> np.ndarray:
    """(users, days) True on the days a user really ran short. Hidden truth: for grading only."""
    truth = pd.read_csv(data_dir / "truth_daily.csv.gz").sort_values(["user_id", "date"], kind="stable")
    if list(pd.unique(truth["user_id"])) != panel.users:
        raise ValueError("the truth file and the panel list different users")
    return truth["squeeze"].to_numpy().reshape(len(panel.users), panel.n_days)


def load_personas(data_dir: Path, panel: Panel) -> tuple[list[str], dict[str, str]]:
    """Each panel user's persona, and the readable label of every persona."""
    users = pd.read_csv(data_dir / "users.csv").set_index("user_id")
    labels = dict(zip(users["persona"], users["persona_label"]))
    return [users.loc[user, "persona"] for user in panel.users], labels


def _share(mask) -> float:
    return round(float(np.mean(mask)), 4)


def _warning_scores(alert, real) -> dict:
    """How good a yes/no warning is, against what really happened."""
    return {
        "caught": _share(alert[real]),  # of the days followed by a real shortfall, share that had a warning
        "right": round(float((alert & real).sum() / max(alert.sum(), 1)), 4),  # of the warnings, share that were right
        "false_alarms": _share(alert[~real]),  # of the days with no shortfall ahead, share that had a warning
    }


def evaluate(panel: Panel, models: dict, short: np.ndarray, personas: list[str], persona_labels: dict,
             cfg: Settings = settings, origin_step: int = 1) -> dict:
    """All test results as one plain dictionary, ready to print or save as JSON."""
    n_users, days = len(panel.users), cfg.horizon_days
    origins = np.arange(panel.day_index(cfg.test_start), panel.day_index(cfg.test_end) + 1, origin_step)
    data = build_dataset(panel, calendar_for(panel, cfg), range(n_users), origins)
    cube = (n_users, len(origins), days)  # rows are ordered user, then origin day, then days ahead

    levels = predict_net_flow(models, data.X)
    likely = levels[:, QUANTILES.index(0.50)]
    simple = {name: data.X[:, FEATURE_NAMES.index(column)].astype(float) for name, column in BASELINES.items()}
    error = {"model": np.abs(likely - data.net), **{name: np.abs(f - data.net) for name, f in simple.items()}}
    inside_80 = (data.net >= levels[:, 0]) & (data.net <= levels[:, -1])
    inside_50 = (data.net >= levels[:, 1]) & (data.net <= levels[:, -2])

    never_seen_users = held_out_users(panel, cfg)
    never_seen = np.isin(data.user, never_seen_users)
    groups = {"all users": np.ones(len(data.X), bool), "users it trained on": ~never_seen,
              "users it never saw": never_seen}
    persona_of_row = np.array(personas)[data.user]

    def error_row(mask, label_days):
        spending = {name: round(float(e[mask].mean()), 3) for name, e in error.items()}
        taka = {name: round(float((e * data.scale)[mask].mean())) for name, e in error.items()}
        best = min(v for name, v in spending.items() if name != "model")
        return {"days_ahead": label_days, "in_days_of_spending": spending, "in_taka": taka,
                "better_than_best_baseline_by": round(1 - spending["model"] / best, 3)}

    errors, coverage = {}, {}
    for group, in_group in groups.items():
        errors[group] = [error_row(in_group & (data.days_ahead == d), d) for d in REPORTED_DAYS]
        errors[group].append(error_row(in_group, "all 30"))
        coverage[group] = [{"days_ahead": d, "inside_p10_p90": _share(inside_80[in_group & (data.days_ahead == d)]),
                            "inside_p25_p75": _share(inside_50[in_group & (data.days_ahead == d)])}
                           for d in REPORTED_DAYS]
        coverage[group].append({"days_ahead": "all 30", "inside_p10_p90": _share(inside_80[in_group]),
                                "inside_p25_p75": _share(inside_50[in_group])})

    curve = {"days_ahead": list(range(1, days + 1)),
             **{name: [round(float(e[data.days_ahead == d].mean()), 3) for d in range(1, days + 1)]
                for name, e in error.items()}}

    # ---------- early warning, graded against the hidden truth ----------
    today = (data.balance / data.scale).reshape(cube)[:, :, 0]  # balance today, in days of spending
    # cut off at zero, as the forecaster does: a wallet cannot go below zero
    forecast = np.maximum(today[:, :, None, None] + levels.reshape(*cube, len(QUANTILES)), 0.0)
    simple_forecast = today[:, :, None] + simple[BEST_SIMPLE].reshape(cube)
    chance = prob_below(forecast[:, :, :WARNING_WINDOW, :], CUSHION_DAYS).max(axis=2)  # (users, origins)
    simple_lowest = simple_forecast[:, :, :WARNING_WINDOW].min(axis=2)

    total = np.concatenate([np.zeros((n_users, 1)), np.cumsum(short, axis=1)], axis=1)
    short_ahead = (total[:, origins + WARNING_WINDOW + 1] - total[:, origins + 1]) > 0
    short_now = (total[:, origins + 1] - total[:, origins - 2]) > 0  # today or in the two days before
    ask = ~short_now  # a warning only counts while the user is still fine

    real, score = short_ahead[ask], chance[ask]
    simple_alert = (simple_lowest < CUSHION_DAYS)[ask]
    simple_scores = _warning_scores(simple_alert, real)
    matched = float(np.quantile(score[~real], 1 - simple_scores["false_alarms"]))
    points = [{"warning": "simple rule: the 3-month average says the balance goes under the cushion", **simple_scores},
              {"warning": "model, tuned to the same number of false alarms", **_warning_scores(score >= matched, real)}]
    points += [{"warning": f"model, chance of going under the cushion at least {round(level * 100)}%"
                           + (" (used in the app)" if level == ALERT_CHANCE else ""),
                **_warning_scores(score >= level, real)} for level in ALERT_LEVELS]

    # new shortfalls: a short day after at least seven clear days. Was there a warning seven days earlier?
    first_day, last_day = origins[0] + 7, origins[-1] + 7
    days_checked = np.arange(first_day, last_day + 1, origin_step)
    starts = short[:, days_checked] & ((total[:, days_checked] - total[:, days_checked - 7]) == 0)
    at_origin = (days_checked - 7 - origins[0]) // origin_step
    episodes = {
        "new_shortfalls": int(starts.sum()),
        "warned_7_days_before": {
            "simple rule": _share((simple_lowest < CUSHION_DAYS)[:, at_origin][starts]),
            "model, same false alarms": _share((chance >= matched)[:, at_origin][starts]),
            **{f"model, at least {round(level * 100)}%": _share((chance >= level)[:, at_origin][starts])
               for level in ALERT_LEVELS},
        },
    }
    ranking = {"model": round(float(roc_auc_score(real, score)), 3),
               "simple rule": round(float(roc_auc_score(real, -simple_lowest[ask])), 3)}

    # ---------- per persona ----------
    by_persona = []
    at_14 = data.days_ahead == 14
    for persona in sorted(set(personas)):
        rows = persona_of_row == persona
        users = np.array(personas) == persona
        best = min(float(e[rows & at_14].mean()) for name, e in error.items() if name != "model")
        mine = float(error["model"][rows & at_14].mean())
        real_p, score_p = short_ahead[users][ask[users]], chance[users][ask[users]]
        by_persona.append({
            "persona": persona,
            "label": persona_labels[persona],
            "users": int(users.sum()),
            "error_14_days": round(mine, 3),
            "best_baseline_14_days": round(best, 3),
            "better_by": round(1 - mine / best, 3),
            "error_14_days_taka": round(float((error["model"] * data.scale)[rows & at_14].mean())),
            "inside_p10_p90": _share(inside_80[rows]),
            "days_followed_by_a_shortfall": _share(real_p),
            "warning_ranking": round(float(roc_auc_score(real_p, score_p)), 3) if 0 < real_p.mean() < 1 else None,
        })

    # ---------- the cautious income level ----------
    # Many forecasts have no income at all in the window, where the cautious level is just above zero.
    # "Clearly lower" therefore means lower by more than half a day of spending.
    income = predict_cautious_income(models, data.X)
    cautious_income = [{"days_ahead": d,
                        "real_income_clearly_lower": _share((data.money_in < income - INCOME_TOLERANCE)[data.days_ahead == d]),
                        "no_income_in_the_window": _share((data.money_in == 0)[data.days_ahead == d])}
                       for d in REPORTED_DAYS]

    everyone = {row["days_ahead"]: row for row in errors["all users"]}
    checks = {
        "beats_every_baseline_at_7_14_30_days": all(
            everyone[d][unit]["model"] < min(v for name, v in everyone[d][unit].items() if name != "model")
            for d in REPORTED_DAYS for unit in ("in_days_of_spending", "in_taka")),
        "range_is_honest_70_to_90_percent": 0.70 <= coverage["all users"][-1]["inside_p10_p90"] <= 0.90,
        "warnings_beat_the_simple_rule": ranking["model"] > ranking["simple rule"]
        and points[1]["caught"] > points[0]["caught"],
    }

    return {
        "about": {
            "data": "synthetic; see docs/SYNTHETIC_DATA.md",
            "test_period": {"from": str(cfg.test_start), "to": str(cfg.test_end)},
            "trained_up_to": models["trained_on"]["train_end"],
            "users": {"all": n_users, "trained_on": n_users - len(never_seen_users), "never_seen": len(never_seen_users)},
            "forecasts_tested": int(len(data.X)),
            "error_unit": "days of the user's typical spending; lower is better",
            "model": "gradient-boosted trees with quantile loss (scikit-learn HistGradientBoostingRegressor)",
            "rounds": models["rounds"],
        },
        "error": errors,
        "error_by_days_ahead": curve,
        "range": coverage,
        "early_warning": {
            "question": f"On days when the user is not short, will they run short in the next {WARNING_WINDOW} days?",
            "cushion": "one day of the user's typical spending",
            "alert_level_used_in_the_app": ALERT_CHANCE,
            "days_asked": int(ask.sum()),
            "share_followed_by_a_shortfall": _share(real),
            "ranking_quality": ranking,  # 0.5 is guessing, 1.0 is perfect
            "warnings": points,
            **episodes,
        },
        "by_persona": by_persona,
        "cautious_income": cautious_income,
        "checks": checks,
    }


def save_metrics(results: dict, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / METRICS_FILE
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return path


def load_metrics(report_dir: Path) -> dict:
    return json.loads((report_dir / METRICS_FILE).read_text(encoding="utf-8"))


def format_report(results: dict) -> str:
    """The results as plain text tables."""
    about, lines = results["about"], []
    users = about["users"]
    lines.append(f"Tested on {about['forecasts_tested']:,} forecasts made between {about['test_period']['from']} and "
                 f"{about['test_period']['to']}; the models saw nothing after {about['trained_up_to']}.")
    lines.append(f"{users['all']} users: {users['trained_on']} the models trained on, {users['never_seen']} they never saw. "
                 "All data is synthetic.")

    lines.append("\n1. FORECAST ERROR, in days of the user's typical spending (lower is better)")
    for group, rows in results["error"].items():
        table = pd.DataFrame([{"days ahead": r["days_ahead"], **r["in_days_of_spending"],
                               "model better by": f"{r['better_than_best_baseline_by']:.0%}"} for r in rows])
        lines.append(f"\n  {group}\n" + _indent(table.to_string(index=False)))
    taka = pd.DataFrame([{"days ahead": r["days_ahead"], **r["in_taka"]} for r in results["error"]["all users"]])
    lines.append("\n  all users, the same error in taka\n" + _indent(taka.to_string(index=False)))

    lines.append("\n2. IS THE RANGE HONEST? Share of real balances inside the range (targets: 80% and 50%)")
    for group, rows in results["range"].items():
        table = pd.DataFrame([{"days ahead": r["days_ahead"], "inside P10-P90": f"{r['inside_p10_p90']:.0%}",
                               "inside P25-P75": f"{r['inside_p25_p75']:.0%}"} for r in rows])
        lines.append(f"\n  {group}\n" + _indent(table.to_string(index=False)))

    warn = results["early_warning"]
    lines.append(f"\n3. EARLY WARNING. {warn['question']}")
    lines.append(f"  Asked on {warn['days_asked']:,} user-days; {warn['share_followed_by_a_shortfall']:.0%} of them were followed "
                 "by a real shortfall.")
    lines.append(f"  Ranking quality (0.5 = guessing, 1.0 = perfect): model {warn['ranking_quality']['model']}, "
                 f"simple rule {warn['ranking_quality']['simple rule']}")
    table = pd.DataFrame([{"warning": p["warning"], "shortfalls caught": f"{p['caught']:.0%}",
                           "warnings that were right": f"{p['right']:.0%}", "false alarms": f"{p['false_alarms']:.0%}"}
                          for p in warn["warnings"]])
    lines.append(_indent(table.to_string(index=False)))
    lines.append(f"  New shortfalls (a short day after seven clear days): {warn['new_shortfalls']:,}. Warned seven days before:")
    for name, share in warn["warned_7_days_before"].items():
        lines.append(f"    {name}: {share:.0%}")

    lines.append("\n4. PER PERSONA (error 14 days ahead, in days of spending)")
    table = pd.DataFrame([{"persona": p["label"], "model": p["error_14_days"], "best baseline": p["best_baseline_14_days"],
                           "better by": f"{p['better_by']:.0%}", "error in taka": p["error_14_days_taka"],
                           "inside P10-P90": f"{p['inside_p10_p90']:.0%}",
                           "days followed by a shortfall": f"{p['days_followed_by_a_shortfall']:.0%}",
                           "warning ranking": p["warning_ranking"]} for p in results["by_persona"]])
    lines.append(_indent(table.to_string(index=False)))

    lines.append("\n5. CAUTIOUS INCOME. Real income should be clearly lower than the cautious level at most about 25% of the time.")
    for c in results["cautious_income"]:
        lines.append(f"  {c['days_ahead']} days ahead: clearly lower in {c['real_income_clearly_lower']:.0%} of forecasts "
                     f"({c['no_income_in_the_window']:.0%} of forecasts had no income at all in the window)")

    lines.append("\nCHECKS")
    for name, passed in results["checks"].items():
        lines.append(f"  [{'PASS' if passed else 'FAIL'}] {name.replace('_', ' ')}")
    return "\n".join(lines)


def _indent(text: str) -> str:
    return "\n".join("  " + line for line in text.splitlines())
