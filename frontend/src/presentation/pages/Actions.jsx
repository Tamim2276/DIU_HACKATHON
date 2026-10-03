import { FAILED as FORECAST_FAILED } from "../../application/useForecast.js";
import { FAILED, LOADING, useWhatIf } from "../../application/useWhatIf.js";
import { lowestPoint } from "../../domain/forecastSeries.js";
import ContextBar from "../components/ContextBar.jsx";
import ForecastChart, { ChartKey } from "../components/ForecastChart.jsx";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";
import { useText } from "../language.jsx";
import { isOutdated } from "./Home.jsx";

// The sentence for one action, written from the figures the API sends with it.
// An action the app does not know yet falls back to the API's own English sentence.
function sentence(action, t, f) {
  const { details } = action;
  switch (action.id) {
    case "keep_to_safe_spend":
      return t.actions.keep(f.taka(details.safe_per_day), f.shortDay(details.until), f.taka(details.usual_per_day));
    case "move_payment":
      return t.actions.move(
        f.taka(details.amount),
        t.payments[details.label] ?? t.payments.other,
        f.shortDay(details.to),
        f.shortDay(details.from),
      );
    case "pay_directly":
      return t.actions.pay(f.taka(details.fees_last_30_days));
    default:
      return action.title;
  }
}

// What the chosen actions change: the warning and the lowest balance we expect, now and with them.
function Outcome({ forecast, changed, count, available, meta }) {
  const { t, f } = useText();
  const text = t.actions;
  const level = f.percent(meta.alert_level);
  const before = forecast.alert;
  const after = changed ? changed.alert : before;
  const several = count > 1;

  let view;
  if (available === 0) {
    view = before
      ? { tone: "warn", icon: "warning", eyebrow: text.standing, title: text.stands, text: text.standsText(f.weekDay(before.date)) }
      : { tone: "note", icon: "info", eyebrow: text.standing, title: text.nothingNeeded, text: text.nothingNeededText };
  } else if (count === 0) {
    view = {
      tone: "note",
      icon: "info",
      eyebrow: text.eyebrow,
      title: text.switchOn,
      text: before ? text.switchOnWarned(f.weekDay(before.date)) : text.switchOnClear,
    };
  } else if (!changed) {
    view = { tone: "note", icon: "info", eyebrow: text.eyebrow, title: text.working, text: "" };
  } else if (before && !after) {
    view = { tone: "ok", icon: "check", eyebrow: text.eyebrow, title: text.gone(several), text: text.goneText(level) };
  } else if (before && after) {
    const lower = before.probability - after.probability >= 0.01;
    view = {
      tone: "warn",
      icon: "warning",
      eyebrow: text.eyebrow,
      title: lower ? text.lower : text.stays,
      text: lower
        ? text.lowerText(several, f.percent(before.probability), f.percent(after.probability))
        : text.staysText(several),
    };
  } else {
    view = { tone: "ok", icon: "check", eyebrow: text.eyebrow, title: text.more, text: text.moreText(several) };
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
            <th scope="col">{text.now}</th>
            <th scope="col">{text.withIt(several)}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">{text.chance}</th>
            <td>{before ? f.percent(before.probability) : text.under(level)}</td>
            <td>{!changed ? "–" : after ? f.percent(after.probability) : text.under(level)}</td>
          </tr>
          <tr>
            <th scope="row">{text.lowest}</th>
            <td>{f.taka(lowBefore.p50)}</td>
            <td>{lowAfter ? f.taka(lowAfter.p50) : "–"}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

// The suggested actions, each with a switch. Switching one asks the API for the forecast with it.
export default function Actions({ users, meta, selection, forecastState, actionIds, onToggle, goTo }) {
  const { t, f } = useText();
  const text = t.actions;
  const { status, forecast, error, reload } = forecastState;
  const whatIf = useWhatIf(selection.userId, selection.asOf, actionIds, selection.goal);

  if (status === FORECAST_FAILED) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Failed title={t.state.forecastFailed} error={error} onRetry={reload} />
      </div>
    );
  }
  if (!forecast || isOutdated(forecast, selection)) {
    return (
      <div className="stack">
        <ContextBar users={users} selection={selection} goTo={goTo} />
        <Loading heights={[280, 420]} />
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
          <h1 id="actions-title">{text.title}</h1>
          {forecast.actions.length === 0 ? (
            <p className="card-text">{text.none}</p>
          ) : (
            <>
              <p className="card-text">{text.intro}</p>
              <ul className="action-list">
                {forecast.actions.map((action) => (
                  <li key={action.id}>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={actionIds.includes(action.id)}
                      className="action"
                      onClick={() => onToggle(action.id)}
                    >
                      <span className="action-words">
                        <strong>{text.names[action.id] ?? text.other}</strong>
                        <span>{sentence(action, t, f)}</span>
                        <small>{text.adds(f.taka(action.effect))}</small>
                      </span>
                      <span className="switch" aria-hidden="true" />
                    </button>
                  </li>
                ))}
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
              {count > 0 ? text.chartWith : text.chartPlain}
            </h2>
            {whatIf.status === FAILED && (
              <p className="card-text warn-text" role="alert">
                {text.failed(whatIf.error)}
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
