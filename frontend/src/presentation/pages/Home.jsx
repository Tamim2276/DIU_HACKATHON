import { FAILED } from "../../application/useForecast.js";
import { sameGoal } from "../../domain/selection.js";
import AlertCard from "../components/AlertCard.jsx";
import BalanceCard from "../components/BalanceCard.jsx";
import ComingUp from "../components/ComingUp.jsx";
import SafeToSpend from "../components/SafeToSpend.jsx";
import SavingsGoal from "../components/SavingsGoal.jsx";
import { Failed } from "../components/ScreenState.jsx";
import UserSwitcher from "../components/UserSwitcher.jsx";
import { useText } from "../language.jsx";

// The forecast on screen belongs to another customer, day or goal while the right one loads.
export function isOutdated(forecast, selection) {
  const goal = forecast.savings_goal && { amount: forecast.savings_goal.amount, date: forecast.savings_goal.date };
  return forecast.user_id !== selection.userId || forecast.as_of !== selection.asOf || !sameGoal(goal, selection.goal);
}

// Grey blocks in the shape of the screen, shown while the first forecast loads.
function Loading({ label }) {
  return (
    <div className="home-grid" aria-busy="true" aria-label={label}>
      <div className="stack">
        <div className="skeleton" style={{ height: 232 }} />
        <div className="skeleton" style={{ height: 168 }} />
      </div>
      <div className="stack">
        <div className="skeleton" style={{ height: 212 }} />
        <div className="skeleton" style={{ height: 188 }} />
      </div>
    </div>
  );
}

export default function Home({ users, meta, selection, onChoose, forecastState, goTo }) {
  const { t } = useText();
  const { status, forecast, error, reload } = forecastState;
  // While another customer, day or goal is loading, the previous forecast stays on screen, dimmed.
  const outdated = forecast && isOutdated(forecast, selection);

  return (
    <div className="stack">
      <UserSwitcher users={users} meta={meta} selection={selection} onChoose={onChoose} />

      {status === FAILED && <Failed title={t.state.forecastFailed} error={error} onRetry={reload} />}
      {status !== FAILED && !forecast && <Loading label={t.state.loading} />}
      {status !== FAILED && forecast && (
        <div className={outdated ? "home-grid outdated" : "home-grid"} aria-busy={outdated}>
          <div className="stack">
            <AlertCard forecast={forecast} meta={meta} goTo={goTo} />
            <SafeToSpend forecast={forecast} />
            <SavingsGoal
              key={`${selection.userId}|${selection.asOf}`}
              forecast={forecast}
              selection={selection}
              onChoose={onChoose}
            />
          </div>
          <div className="stack">
            <BalanceCard forecast={forecast} />
            <ComingUp forecast={forecast} meta={meta} goTo={goTo} />
          </div>
        </div>
      )}
    </div>
  );
}
