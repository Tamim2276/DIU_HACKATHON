import { FAILED as FORECAST_FAILED } from "../../application/useForecast.js";
import { FAILED, LOADING, useWhatIf } from "../../application/useWhatIf.js";
import { percent, taka, weekDay } from "../../domain/format.js";
import { lowestPoint } from "../../domain/forecastSeries.js";
import { actionName } from "../../domain/labels.js";
import ContextBar from "../components/ContextBar.jsx";
import ForecastChart, { ChartKey } from "../components/ForecastChart.jsx";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";

// What the chosen actions change: the warning and the lowest likely balance, now and with them.
function Outcome({ forecast, changed, count, available, meta }) {
  const under = `under ${percent(meta.alert_level)}`;
  const before = forecast.alert;
  const after = changed ? changed.alert : before;
  const these = count === 1 ? "this action" : "these actions";

  let view;
  if (available === 0) {
    view = {
      tone: before ? "warn" : "note",
      icon: before ? "warning" : "info",
      eyebrow: "Where things stand",
      title: before ? "The warning stands" : "Nothing needs to change",
      text: before
        ? `The forecast shows a shortfall warning for ${weekDay(before.date)}, and there is no suggested action to try against it.`
        : "There is no shortfall warning, and no action is suggested.",
    };
  } else if (count === 0) {
    view = {
      tone: "note",
      icon: "info",
      eyebrow: "What would change",
      title: "Switch an action on to see what it changes",
      text: before
        ? `The forecast shows a shortfall warning for ${weekDay(before.date)}.`
        : "There is no shortfall warning at the moment. An action would still leave more in the wallet.",
    };
  } else if (!changed) {
    view = { tone: "note", icon: "info", eyebrow: "What would change", title: "Working it out", text: "" };
  } else if (before && !after) {
    view = {
      tone: "ok",
      icon: "check",
      eyebrow: "What would change",
      title: `With ${these}, the warning goes away`,
      text: `The chance of a shortfall falls below ${percent(meta.alert_level)}, the level at which a warning is shown.`,
    };
  } else if (before && after) {
    const lower = before.probability - after.probability >= 0.01;
    view = {
      tone: "warn",
      icon: "warning",
      eyebrow: "What would change",
      title: lower ? "The warning stays, but the risk is lower" : "The warning stays",
      text: lower
        ? `With ${these}, the chance of a shortfall falls from ${percent(before.probability)} to ${percent(after.probability)}.`
        : `${count === 1 ? "This action helps" : "These actions help"} a little, but not enough to remove the warning.`,
    };
  } else {
    view = {
      tone: "ok",
      icon: "check",
      eyebrow: "What would change",
      title: "More is left in the wallet",
      text: `There was no shortfall warning, and with ${these} there is still none.`,
    };
  }

  const lowBefore = lowestPoint(forecast.points);
  const lowAfter = changed ? lowestPoint(changed.points) : null;

  return (
    <section className={`status ${view.tone}`} aria-live="polite" aria-labelledby="outcome-title">
      <p className="status-eyebrow">
        <Icon name={view.icon} size={18} />
        {view.eyebrow}
      </p>
      <h2 id="outcome-title" className="status-title">
        {view.title}
      </h2>
      {view.text && <p className="status-text">{view.text}</p>}

      <table className="compare" hidden={available === 0}>
        <thead>
          <tr>
            <td />
            <th scope="col">Now</th>
            <th scope="col">With {count > 1 ? "the actions" : "the action"}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Chance of a shortfall</th>
            <td>{before ? percent(before.probability) : under}</td>
            <td>{!changed ? "–" : after ? percent(after.probability) : under}</td>
          </tr>
          <tr>
            <th scope="row">Lowest likely balance</th>
            <td>{taka(lowBefore.p50)}</td>
            <td>{lowAfter ? taka(lowAfter.p50) : "–"}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

// The suggested actions, each with a switch. Switching one asks the API for the forecast with it.
export default function Actions({ users, meta, selection, forecastState, actionIds, onToggle, goTo }) {
  const { status, forecast, error, reload } = forecastState;
  const whatIf = useWhatIf(selection.userId, selection.asOf, actionIds);

  if (status === FORECAST_FAILED) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Failed title="The forecast could not be loaded" error={error} onRetry={reload} />
      </div>
    );
  }
  if (!forecast || forecast.user_id !== selection.userId || forecast.as_of !== selection.asOf) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Loading heights={[280, 420]} label="Loading the forecast" />
      </div>
    );
  }

  const count = actionIds.length;
  const changed = count > 0 ? whatIf.result : null;
  const shown = changed ?? forecast;

  return (
    <div className="stack">
      <ContextBar users={users} selection={selection} goTo={goTo} />

      <div className="actions-grid">
        <section className="card" aria-labelledby="actions-title">
          <h1 id="actions-title">What you can do</h1>
          {forecast.actions.length === 0 ? (
            <p className="card-text">
              Nothing in this customer's history points to a step that would help. The best that can be done is to keep
              spending as low as possible until more money comes in.
            </p>
          ) : (
            <>
              <p className="card-text">
                Each of these either saves money or shifts the date of a payment. None is a loan or a paid product.
                Switch one on to see the forecast with it.
              </p>
              <ul className="action-list">
                {forecast.actions.map((action) => {
                  const on = actionIds.includes(action.id);
                  return (
                    <li key={action.id}>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={on}
                        className="action"
                        onClick={() => onToggle(action.id)}
                      >
                        <span className="action-words">
                          <strong>{actionName(action.id)}</strong>
                          <span>{action.title}</span>
                          <small>Adds about {taka(action.effect)} on the forecast's tightest day.</small>
                        </span>
                        <span className="switch" aria-hidden="true" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>

        <div className="stack">
          <Outcome forecast={forecast} changed={changed} count={count} available={forecast.actions.length} meta={meta} />

          <section
            className={whatIf.status === LOADING ? "card outdated" : "card"}
            aria-labelledby="whatif-chart-title"
            aria-busy={whatIf.status === LOADING}
          >
            <h2 id="whatif-chart-title" className="card-title">
              {count > 0 ? "The forecast with the action" : "The forecast as it is"}
            </h2>
            {whatIf.status === FAILED && (
              <p className="card-text warn-text" role="alert">
                This could not be worked out: {whatIf.error} Switch the action off and on to try again.
              </p>
            )}
            <ForecastChart forecast={shown} before={changed ? forecast : null} />
            <ChartKey before={Boolean(changed)} />
          </section>
        </div>
      </div>
    </div>
  );
}
