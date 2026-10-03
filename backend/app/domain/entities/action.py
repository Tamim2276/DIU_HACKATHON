"""Something the user could do to avoid or shrink a shortfall."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Action:
    id: str  # which kind of action, for example "keep_to_safe_spend"
    title: str  # one plain sentence with the numbers filled in
    effect: float  # taka: how much it raises the most likely balance on the forecast's lowest day
    changes: tuple[float, ...]  # taka added to the balance on each forecast day
    details: dict = field(default_factory=dict)  # the numbers behind the title, for explanations

    def __post_init__(self):
        if any(change < 0 for change in self.changes):
            raise ValueError("an action can only raise the balance or leave it unchanged")
