"""What the forecast would look like if the user took some of the suggested actions."""
from dataclasses import dataclass, replace
from datetime import date

from app.application.use_cases.get_forecast import ForecastResult, GetForecast
from app.domain.entities.action import Action
from app.domain.entities.alert import Alert
from app.domain.services.actions import apply_actions
from app.domain.services.shortfall import find_shortfall


class UnknownActionError(ValueError):
    """An action was asked for that is not among the ones suggested to this user."""


@dataclass(frozen=True)
class WhatIfResult:
    result: ForecastResult  # as the forecast use case returns it, but with the forecast and alert changed
    applied: list[Action]  # the actions that were switched on
    alert_before: Alert | None  # the alert without any action, to compare with


class RunWhatIf:
    def __init__(self, get_forecast: GetForecast):
        self._get_forecast = get_forecast

    def execute(self, user_id: str, as_of: date, action_ids: list[str]) -> WhatIfResult:
        base = self._get_forecast.execute(user_id, as_of)
        available = {action.id: action for action in base.assessment.actions}
        unknown = [action_id for action_id in action_ids if action_id not in available]
        if unknown:
            raise UnknownActionError(f"not suggested for this user: {', '.join(unknown)}. "
                                     f"Suggested: {', '.join(available) or 'none'}")

        chosen = [available[action_id] for action_id in dict.fromkeys(action_ids)]  # each one once, in the order asked
        changed = apply_actions(base.assessment.forecast, chosen)
        # only the forecast and the alert change; the rules run again on the changed forecast
        assessment = replace(base.assessment, forecast=changed, alert=find_shortfall(changed, base.assessment.cushion))
        return WhatIfResult(ForecastResult(base.user, assessment, base.actual), chosen, base.assessment.alert)
