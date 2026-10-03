import { FAILED } from "../../application/useForecast.js";
import AlertCard from "../components/AlertCard.jsx";
import BalanceCard from "../components/BalanceCard.jsx";
import ComingUp from "../components/ComingUp.jsx";
import SafeToSpend from "../components/SafeToSpend.jsx";
import UserSwitcher from "../components/UserSwitcher.jsx";

// Grey blocks in the shape of the screen, shown while the first forecast loads.
function Loading() {
  return (
    <div className="home-grid" aria-busy="true" aria-label="Loading the forecast">
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

function Failed({ error, onRetry }) {
  return (
    <section className="card notice" role="alert">
      <h1>The forecast could not be loaded</h1>
      <p className="card-text">{error}</p>
      <button type="button" className="button" onClick={onRetry}>
        Try again
      </button>
    </section>
  );
}

export default function Home({ users, meta, selection, onChoose, forecastState, goTo }) {
  const { status, forecast, error, reload } = forecastState;
  // While another customer or day is loading, the previous forecast stays on screen, dimmed.
  const outdated = forecast && (forecast.user_id !== selection.userId || forecast.as_of !== selection.asOf);

  return (
    <div className="stack">
      <UserSwitcher users={users} meta={meta} selection={selection} onChoose={onChoose} />

      {status === FAILED && <Failed error={error} onRetry={reload} />}
      {status !== FAILED && !forecast && <Loading />}
      {status !== FAILED && forecast && (
        <div className={outdated ? "home-grid outdated" : "home-grid"} aria-busy={outdated}>
          <div className="stack">
            <AlertCard forecast={forecast} meta={meta} goTo={goTo} />
            <SafeToSpend forecast={forecast} />
          </div>
          <div className="stack">
            <BalanceCard forecast={forecast} />
            <ComingUp forecast={forecast} goTo={goTo} />
          </div>
        </div>
      )}
    </div>
  );
}
