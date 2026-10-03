import { useState } from "react";

import { FAILED } from "../../application/useForecast.js";
import { taka, weekDay } from "../../domain/format.js";
import { lowestPoint } from "../../domain/forecastSeries.js";
import ContextBar from "../components/ContextBar.jsx";
import ForecastChart, { ChartKey } from "../components/ForecastChart.jsx";
import RegularPayments from "../components/RegularPayments.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";

// The 30-day forecast as a chart, with the regular payments it has to carry.
export default function Forecast({ users, selection, forecastState, goTo }) {
  const { status, forecast, error, reload } = forecastState;
  const [showActual, setShowActual] = useState(false);

  if (status === FAILED) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Failed title="The forecast could not be loaded" error={error} onRetry={reload} />
      </div>
    );
  }
  if (!forecast) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Loading heights={[460, 260]} label="Loading the forecast" />
      </div>
    );
  }

  const outdated = forecast.user_id !== selection.userId || forecast.as_of !== selection.asOf;
  const { points } = forecast;
  const lowest = lowestPoint(points, "p50");
  const cautious = lowestPoint(points, "p25");
  const last = points[points.length - 1];
  const hasActual = points.some((point) => point.actual !== null);

  return (
    <div className={outdated ? "stack outdated" : "stack"} aria-busy={outdated}>
      <ContextBar users={users} selection={selection} goTo={goTo} />

      <section className="card" aria-labelledby="chart-title">
        <div className="card-head">
          <h1 id="chart-title">Your balance over the next 30 days</h1>
          {hasActual && (
            <label className="check">
              <input type="checkbox" checked={showActual} onChange={(event) => setShowActual(event.target.checked)} />
              Show what really happened
            </label>
          )}
        </div>
        <p className="card-text">
          The line is the most likely balance. The shaded areas show how far it could reasonably be above or below.
        </p>

        <ForecastChart forecast={forecast} showActual={showActual} />
        <ChartKey showActual={showActual} />

        <dl className="figures tight">
          <div>
            <dt>lowest point, most likely, on {weekDay(lowest.date)}</dt>
            <dd>{taka(lowest.p50)}</dd>
          </div>
          <div>
            <dt>lowest point in a cautious estimate, on {weekDay(cautious.date)}</dt>
            <dd>{taka(cautious.p25)}</dd>
          </div>
          <div>
            <dt>most likely on {weekDay(last.date)}, the last day</dt>
            <dd>{taka(last.p50)}</dd>
          </div>
        </dl>

        {showActual && (
          <p className="footnote spaced">
            Demo only: the days after "today" already exist in the synthetic data, so the forecast can be compared with
            what happened. The forecast itself never sees them.
          </p>
        )}
      </section>

      <RegularPayments forecast={forecast} />
    </div>
  );
}
