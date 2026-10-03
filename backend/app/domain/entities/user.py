"""A wallet customer."""
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: str
    persona: str  # key of the simulated persona, for example "rider"
    persona_label: str  # readable name, for example "Ride-share rider"
