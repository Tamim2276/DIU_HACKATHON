"""The impact test: the same simulated customers, once as they were and once following Agam.

Every customer is simulated twice from the same starting point and the same random seed. Up to
the first test day the two runs are identical. From then on, in the second run, the customer
opens Agam each morning and follows it. Agam sees only the transactions up to the day before,
exactly as the app does, and its model saw nothing from the test period while it was trained.

Two ways of following are tested:

- when warned: on a day Agam shows a shortfall warning, the customer keeps everyday spending
  to the safe-to-spend amount. On other days they spend as they like.
- every day: the customer keeps to the safe-to-spend amount every day.

Nobody can cut spending to nothing, so a customer never plans under half of the day's need.

After the first day on which a customer acts differently, the two runs draw different random
numbers (a different day's sales, a different emergency). One customer's result is therefore
noisy. Only the totals over all customers mean something, and each comes with a range.

All of this is synthetic. It shows what the advice does to the simulated customers we wrote,
not to real people.
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import numpy as np

from app.application.use_cases.get_forecast import assess
from app.domain.entities.transaction import Transaction
from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.ml.quantile_forecaster import QuantileForecaster
from app.infrastructure.synthetic.generator import eid_window, simulate_user
from app.infrastructure.synthetic.personas import PERSONAS

WITHOUT = "without"  # the customers as they were
WHEN_WARNED = "when_warned"
EVERY_DAY = "every_day"
POLICIES = (WHEN_WARNED, EVERY_DAY)

LEAST_SHARE = 0.5  # the smallest share of a day's need a customer will plan to spend
HARD_DAY = 0.5  # a day is hard when less than this share of the day's need was paid for
# A follower who cuts to half sits right on that line, so some hard days in the followed runs are chosen ones.
# A very hard day cannot be chosen: nobody plans under half, so under a quarter means the money was not there.
VERY_HARD_DAY = 0.25
IMPACT_FILE = "impact.json"
RESAMPLES = 2000  # for the range around each difference


class Follower:
    """A customer who opens Agam each morning of the test period and does what it says."""

    def __init__(self, forecaster: QuantileForecaster, cfg: Settings, policy: str):
        self._forecaster, self._cfg, self._policy = forecaster, cfg, policy
        self._first = (cfg.test_start - cfg.start_date).days
        self._last = (cfg.test_end - cfg.start_date).days
        self._transactions: list[Transaction] = []
        self._seen = 0
        self.days_warned = 0
        self.days_followed = 0

    def __call__(self, day: int, rows: list, level: float) -> float:
        """The amount the customer will try to spend today, given what they want to spend."""
        if not self._first <= day <= self._last:
            return level
        for row in rows[self._seen:]:
            self._transactions.append(Transaction("T", *row))
        self._seen = len(rows)

        yesterday = self._cfg.start_date + timedelta(days=day - 1)  # the newest day Agam can know about
        assessment = assess(self._forecaster.forecast(self._transactions, yesterday), self._transactions)
        warned = assessment.alert is not None
        self.days_warned += warned
        if self._policy == WHEN_WARNED and not warned:
            return level
        planned = min(level, max(assessment.safe_to_spend.amount, LEAST_SHARE * level))
        self.days_followed += planned < level
        return planned


@dataclass(frozen=True)
class UserRun:
    """One customer over the test period, in one run."""
    user_id: str
    persona: str
    wanted: np.ndarray  # taka the customer wanted to spend each day, before any advice
    spent: np.ndarray  # taka actually spent
    short_of_plan: np.ndarray  # True on days the money did not cover what they planned
    borrowed: np.ndarray  # taka borrowed from a contact
    overdue: np.ndarray  # True on days a regular payment was waiting unpaid
    missed: np.ndarray  # payments given up on that day
    days_warned: int = 0
    days_followed: int = 0


def simulate(policy: str = WITHOUT, cfg: Settings = settings, every: int = 1, adoption: float = 1.0) -> list[UserRun]:
    """All customers (or one in `every`) over the whole year; returns their test-period days.

    `adoption` is the share of customers who act on Agam's advice in this run; the rest are
    simulated exactly as in the `without` run. It decides who follows with a draw that is
    independent of `master`, so the same `adoption` always picks the same customers and the
    underlying synthetic data for every customer stays exactly what `generate()` produced.
    """
    forecaster = QuantileForecaster(cfg.model_dir, cfg) if policy != WITHOUT else None
    window = eid_window(cfg)
    first, last = (cfg.test_start - cfg.start_date).days, (cfg.test_end - cfg.start_date).days
    master = np.random.default_rng(cfg.seed)
    runs, number = [], 0
    for persona in PERSONAS.values():
        for _ in range(cfg.users_per_persona):
            number += 1
            seed = int(master.integers(1 << 32))  # the same draw, in the same order, as generate()
            if (number - 1) % every:
                continue
            follows = np.random.default_rng(seed ^ 0x5EED).random() < adoption
            follower = Follower(forecaster, cfg, policy) if forecaster and follows else None
            trace: list = []
            simulate_user(f"U{number:04d}", persona, np.random.default_rng(seed), cfg, window, advisor=follower, trace=trace)
            days = [row for row in trace if first <= row[0] <= last]
            column = lambda index, kind: np.array([row[index] for row in days], dtype=kind)  # noqa: E731
            runs.append(UserRun(
                user_id=f"U{number:04d}", persona=persona.key,
                wanted=column(1, float), spent=column(3, float), short_of_plan=column(4, bool),
                borrowed=column(5, float), overdue=column(6, float) > 0, missed=column(7, float),
                days_warned=follower.days_warned if follower else 0,
                days_followed=follower.days_followed if follower else 0,
            ))
    return runs


def hard_days(run: UserRun) -> np.ndarray:
    """Days on which less than half of what the customer needed was paid for, by choice or not."""
    return run.spent < HARD_DAY * run.wanted


def very_hard_days(run: UserRun) -> np.ndarray:
    """Days on which less than a quarter of what the customer needed could be paid for."""
    return run.spent < VERY_HARD_DAY * run.wanted


def summarize(runs: list[UserRun]) -> dict:
    """One run in a few figures. Shares are of all customer-days in the test period."""
    days = sum(len(run.wanted) for run in runs)
    return {
        "very_hard_days": round(sum(very_hard_days(run).sum() for run in runs) / days, 4),
        "hard_days": round(sum(hard_days(run).sum() for run in runs) / days, 4),
        "days_short_of_plan": round(sum(run.short_of_plan.sum() for run in runs) / days, 4),
        "spending_met": round(sum(run.spent.sum() for run in runs) / sum(run.wanted.sum() for run in runs), 4),
        "customers_who_borrowed": round(float(np.mean([run.borrowed.sum() > 0 for run in runs])), 4),
        "borrowed_per_customer": round(float(np.mean([run.borrowed.sum() for run in runs]))),
        "days_with_a_payment_overdue": round(sum(run.overdue.sum() for run in runs) / days, 4),
        "payments_given_up_per_100_customers": round(100 * sum(run.missed.sum() for run in runs) / len(runs), 1),
        "days_warned": round(sum(run.days_warned for run in runs) / days, 4),
        "days_advice_changed_spending": round(sum(run.days_followed for run in runs) / days, 4),
    }


def difference(before: list[UserRun], after: list[UserRun], of, seed: int = 0) -> dict:
    """The average change per customer in `of(run)`, with the range it lies in 95 times out of 100.

    The range comes from drawing the customers again and again with replacement.
    """
    changes = np.array([of(b) - of(a) for a, b in zip(before, after)], dtype=float)
    rng = np.random.default_rng(seed)
    means = changes[rng.integers(0, len(changes), (RESAMPLES, len(changes)))].mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return {"change": round(float(changes.mean()), 4), "low": round(float(low), 4), "high": round(float(high), 4)}


MEASURES = {
    "very_hard_days": lambda run: very_hard_days(run).mean(),
    "hard_days": lambda run: hard_days(run).mean(),
    "spending_met": lambda run: run.spent.sum() / run.wanted.sum(),
    "borrowed_per_customer": lambda run: run.borrowed.sum(),
    "days_with_a_payment_overdue": lambda run: run.overdue.mean(),
}


def compare(without: list[UserRun], followed: dict[str, list[UserRun]], cfg: Settings = settings) -> dict:
    """The whole result: each run in figures, the changes with their ranges, and the runs per persona."""
    runs = {WITHOUT: without, **followed}
    return {
        "about": {
            "data": "synthetic; see docs/SYNTHETIC_DATA.md",
            "period": {"from": str(cfg.test_start), "to": str(cfg.test_end)},
            "customers": len(without),
            "days_each": len(without[0].wanted),
            "least_share_of_need": LEAST_SHARE,
            "hard_day": "a day on which less than half of what the customer needed was paid for, by choice or not",
            "very_hard_day": "a day on which less than a quarter of what the customer needed could be paid for",
        },
        "runs": {name: summarize(users) for name, users in runs.items()},
        "changes": {
            policy: {name: difference(without, users, of) for name, of in MEASURES.items()}
            for policy, users in followed.items()
        },
        "by_persona": [
            {
                "persona": persona.key,
                "label": persona.label,
                **{name: summarize([run for run in users if run.persona == persona.key]) for name, users in runs.items()},
            }
            for persona in PERSONAS.values()
        ],
    }


def run_impact_test(cfg: Settings = settings, every: int = 1) -> dict:
    """Simulate without Agam and with each way of following it. The two followed runs go side by side."""
    without = simulate(WITHOUT, cfg, every)
    with ProcessPoolExecutor(max_workers=len(POLICIES)) as pool:
        jobs = {policy: pool.submit(simulate, policy, cfg, every) for policy in POLICIES}
        followed = {policy: job.result() for policy, job in jobs.items()}
    return compare(without, followed, cfg)


ADOPTION_LEVELS = (0.25, 0.5, 0.75, 1.0)
ADOPTION_FILE = "impact_sensitivity.json"


def run_adoption_sensitivity(cfg: Settings = settings, every: int = 1, levels=ADOPTION_LEVELS) -> dict:
    """How the impact changes if only a share of customers act on a warning.

    The 65% cut in borrowing (see run_impact_test) assumes every warned customer follows the
    advice. This answers the obvious objection: what if only a quarter, or half, do?
    """
    without = simulate(WITHOUT, cfg, every)
    with ProcessPoolExecutor(max_workers=len(levels)) as pool:
        jobs = {f"{round(level * 100)}% adoption": pool.submit(simulate, WHEN_WARNED, cfg, every, level)
                for level in levels}
        followed = {name: job.result() for name, job in jobs.items()}
    return compare(without, followed, cfg)


def format_adoption_sensitivity(results: dict) -> str:
    """The sensitivity results as a plain text table: borrowed per customer at each adoption level."""
    about, runs = results["about"], results["runs"]
    levels = [name for name in runs if name != WITHOUT]
    lines = [f"{about['customers']} customers, {about['period']['from']} to {about['period']['to']}. "
             "All data is synthetic.", "",
             f"{'':28}{'without':>12}" + "".join(f"{level:>16}" for level in levels)]
    names = {
        "borrowed_per_customer": "taka borrowed per customer",
        "very_hard_days": "days with under a quarter of the need met",
        "hard_days": "days with under half the need met",
        "spending_met": "share of wanted spending spent",
    }
    shares = {"very_hard_days", "hard_days", "spending_met"}
    for key, name in names.items():
        without_cell = f"{runs[WITHOUT][key]:.1%}" if key in shares else f"{runs[WITHOUT][key]:,.0f}"
        cells = [f"{runs[level][key]:.1%}" if key in shares else f"{runs[level][key]:,.0f}" for level in levels]
        lines.append(f"{name:28}{without_cell:>12}" + "".join(f"{cell:>16}" for cell in cells))
    lines.append("")
    for level in levels:
        change = results["changes"][level]["borrowed_per_customer"]
        lines.append(f"borrowed per customer, {level}: {change['change']:+,.0f} "
                     f"(between {change['low']:+,.0f} and {change['high']:+,.0f})")
    return "\n".join(lines)


def save_impact(results: dict, report_dir: Path, file_name: str = IMPACT_FILE) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / file_name
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return path


def format_impact(results: dict) -> str:
    """The results as a plain text table."""
    about, runs = results["about"], results["runs"]
    names = {
        "very_hard_days": "days with under a quarter of the need met",
        "hard_days": "days with under half the need met",
        "days_short_of_plan": "days the plan could not be paid for",
        "spending_met": "share of wanted spending spent",
        "customers_who_borrowed": "customers who borrowed",
        "borrowed_per_customer": "taka borrowed per customer",
        "days_with_a_payment_overdue": "days with a payment overdue",
        "payments_given_up_per_100_customers": "payments given up per 100 customers",
        "days_warned": "days with a warning",
        "days_advice_changed_spending": "days the advice changed spending",
    }
    shares = {"very_hard_days", "hard_days", "days_short_of_plan", "spending_met", "customers_who_borrowed",
              "days_with_a_payment_overdue", "days_warned", "days_advice_changed_spending"}
    lines = [f"{about['customers']} customers, {about['period']['from']} to {about['period']['to']}. All data is synthetic.",
             "", f"{'':40}{'without':>12}{'when warned':>14}{'every day':>12}"]
    for key, name in names.items():
        cells = [f"{runs[run][key]:.1%}" if key in shares else f"{runs[run][key]:,.0f}" for run in (WITHOUT, *POLICIES)]
        lines.append(f"{name:40}{cells[0]:>12}{cells[1]:>14}{cells[2]:>12}")
    lines.append("")
    for policy in POLICIES:
        for measure in ("very_hard_days", "hard_days"):
            change = results["changes"][policy][measure]
            lines.append(f"{measure.replace('_', ' ')}, {policy.replace('_', ' ')}: {change['change']:+.1%} "
                         f"(between {change['low']:+.1%} and {change['high']:+.1%})")
    return "\n".join(lines)
