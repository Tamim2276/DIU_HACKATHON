"""What the use cases need from whatever puts the app's findings into sentences."""
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import date

BANGLA, ENGLISH = "bn", "en"
LANGUAGES = (BANGLA, ENGLISH)
BANGLA_DIGITS = "০১২৩৪৫৬৭৮৯"

# Reasons a shortfall is likely. The use case decides which apply; an explainer only words them.
INCOME_LATER = "income_later"  # the next income is expected after the day the shortfall is likely
INCOME_DAILY = "income_daily"  # income comes in day by day, so there is no payday to wait for
INCOME_IRREGULAR = "income_irregular"  # income has no usual day
PAYMENTS_DUE = "payments_due"  # regular payments fall due before the safe-to-spend period ends
SPENDING_ABOVE_SAFE = "spending_above_safe"  # usual everyday spending is more than the money covers
REASONS = (INCOME_LATER, INCOME_DAILY, INCOME_IRREGULAR, PAYMENTS_DUE, SPENDING_ABOVE_SAFE)

# What the best action does to the warning.
REMOVES_ALERT = "removes_alert"
LOWERS_CHANCE = "lowers_chance"
LITTLE_CHANGE = "little_change"
OUTCOMES = (REMOVES_ALERT, LOWERS_CHANCE, LITTLE_CHANGE)

CHANCES = ("alert_chance", "chance_after")  # facts between 0 and 1, written as a percentage


@dataclass(frozen=True)
class Facts:
    """Everything an explanation may say about one user on one day.

    Every value was produced by the model or by a fixed rule before an explainer
    sees it. An explainer chooses the words. It adds no number of its own.
    """
    as_of: date
    balance: float
    cushion: float
    under_cushion_now: bool
    warning_days: int  # how many days ahead a warning looks
    safe_to_spend: float  # taka per day
    window_until: date  # the day the safe-to-spend amount has to last until

    # what is likely to happen: all None when there is no warning
    alert_day: date | None = None
    alert_chance: float | None = None  # 0 to 1
    alert_gap: float | None = None  # taka the cautious forecast falls under the cushion

    # why: the reasons that apply, in a fixed order, and the figures they are about
    reasons: tuple[str, ...] = ()
    next_income_day: date | None = None
    days_to_income: int | None = None
    payments_due: float = 0.0  # regular payments the safe-to-spend amount sets money aside for
    payment_label: str | None = None  # the largest single payment among them
    payment_day: date | None = None
    payment_amount: float | None = None
    usual_spending: float = 0.0  # taka a day on everyday things over the last 30 days

    # what to do: the suggested action that lowers the chance most, and what it does to the warning
    action_id: str | None = None
    action: dict = field(default_factory=dict)  # the figures behind that action
    outcome: str | None = None  # one of OUTCOMES
    chance_after: float | None = None  # the chance that remains, when the action lowers it

    def as_dict(self) -> dict:
        return asdict(self)

    def numbers(self) -> set[int]:
        """Every whole number a text about these facts may contain.

        Taka are written rounded to a whole taka, chances as a whole percentage,
        and dates as a day of the month (or a year).
        """
        allowed = set()

        def add(value):
            if isinstance(value, date):
                allowed.update((value.day, value.year))
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                allowed.add(round(value))
            elif isinstance(value, dict):
                for inner in value.values():
                    add(inner)

        for name, value in self.as_dict().items():
            add(value * 100 if name in CHANCES and value is not None else value)
        return allowed


def numbers_in(text: str) -> list[float]:
    """The numbers written in a text, in Bangla or English digits. "৳4,510" and "৳৪,৫১০" both give 4510."""
    plain = text.translate(str.maketrans(BANGLA_DIGITS, "0123456789"))
    return [float(found.replace(",", "")) for found in re.findall(r"\d[\d,]*(?:\.\d+)?", plain)]


def unknown_numbers(text: str, facts: Facts) -> list[float]:
    """Numbers in the text that are not among the facts. An honest explanation has none."""
    allowed = facts.numbers()
    return [number for number in numbers_in(text) if number not in allowed]


class Explainer(ABC):
    @abstractmethod
    def explain(self, facts: Facts, language: str) -> str:
        """The explanation as plain text in the language asked for, one of LANGUAGES.

        Lines are separated by a line break and paragraphs by an empty line.
        """
