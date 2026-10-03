import { useState } from "react";

import { FAILED } from "../../application/useForecast.js";
import { lowestPoint } from "../../domain/forecastSeries.js";
import ContextBar from "../components/ContextBar.jsx";
import ForecastChart, { ChartKey } from "../components/ForecastChart.jsx";
import RegularPayments from "../components/RegularPayments.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";
import { useText } from "../language.jsx";
import { isOutdated } from "./Home.jsx";

// The 30-day forecast as a chart, with the regular payments it has to carry.
export default function Forecast({ users, meta, selection, forecastState, goTo }) {
  const { t, f } = useText();
  const text = t.forecast;
  const { status, forecast, error, reload } = forecastState;
  const [showActual, setShowActual] = useState(false);

  if (status === FAILED) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Failed title={t.state.forecastFailed} error={error} onRetry={reload} />
      </div>
    );
  }
  if (!forecast) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Loading heights={[460, 260]} />
      </div>
    );
  }

  const outdated = isOutdated(forecast, selection);
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
          <h1 id="chart-title">{text.title(f.number(points.length))}</h1>
          {hasActual && (
            <label className="check">
              <input type="checkbox" checked={showActual} onChange={(event) => setShowActual(event.target.checked)} />
              {text.showActual}
            </label>
          )}
        </div>
        <p className="card-text wide">{text.read}</p>

        <ForecastChart forecast={forecast} showActual={showActual} />
        <ChartKey showActual={showActual} />

        <dl className="figures tight">
          <div>
            <dt>{text.lowest(f.weekDay(lowest.date))}</dt>
            <dd>{f.taka(lowest.p50)}</dd>
          </div>
          <div>
            <dt>{text.cautious(f.weekDay(cautious.date))}</dt>
            <dd>{f.taka(cautious.p25)}</dd>
          </div>
          <div>
            <dt>{text.last(f.weekDay(last.date))}</dt>
            <dd>{f.taka(last.p50)}</dd>
          </div>
        </dl>

        {showActual && <p className="footnote spaced">{text.demo}</p>}
      </section>

      <RegularPayments forecast={forecast} meta={meta} />
    </div>
  );
}
