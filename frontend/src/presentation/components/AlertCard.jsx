import { dayCount, daysBetween, fromNow, percent, taka, weekDay, whole } from "../../domain/format.js";
import { CLEAR, LOW_NOW, RECOVERING, SHORTFALL, statusOf } from "../../domain/status.js";
import Icon from "./Icon.jsx";

// The first thing a customer reads: is a shortfall likely, or not?
// What to say comes from the forecast. Only the words are chosen here.
function describe(forecast, meta) {
  const { alert, balance, cushion, as_of: today } = forecast;
  const ahead = dayCount(meta.warning_days);

  switch (statusOf(forecast)) {
    case SHORTFALL: {
      const empty = whole(alert.gap) >= whole(alert.cushion); // the cautious forecast reaches zero
      return {
        tone: "warn",
        icon: "warning",
        eyebrow: "Shortfall warning",
        title: `You may run short around ${weekDay(alert.date)}`,
        text: `That is ${fromNow(daysBetween(today, alert.date))}. Your balance may fall below your safety cushion of ${taka(cushion)}.`,
        figures: [
          { value: percent(alert.probability), label: "chance of a shortfall" },
          empty
            ? { value: taka(0), label: "left in a cautious estimate" }
            : { value: taka(alert.gap), label: "below the cushion, in a cautious estimate" },
        ],
      };
    }
    case LOW_NOW:
      return {
        tone: "warn",
        icon: "warning",
        eyebrow: "Shortfall warning",
        title: "Your balance is already low",
        text: `${taka(balance)} today is under your safety cushion of ${taka(cushion)}. It may be short again in the next ${ahead}.`,
        figures: [{ value: percent(alert.probability), label: "chance of a shortfall" }],
      };
    case RECOVERING:
      return {
        tone: "note",
        icon: "info",
        eyebrow: "No warning",
        title: "Low today, but expected to recover",
        text: `${taka(balance)} today is under your safety cushion of ${taka(cushion)}. The forecast expects it to rise above that level again, so there is no shortfall warning for the next ${ahead}.`,
        figures: [],
      };
    case CLEAR:
    default:
      return {
        tone: "ok",
        icon: "check",
        eyebrow: "All clear",
        title: `No shortfall warning for the next ${ahead}`,
        text: `Your balance is ${taka(balance)}, above your safety cushion of ${taka(cushion)}.`,
        figures: [],
      };
  }
}

export default function AlertCard({ forecast, meta, goTo }) {
  const view = describe(forecast, meta);
  const warned = view.tone === "warn";

  return (
    <section className={`status ${view.tone}`} aria-labelledby="status-title">
      <p className="status-eyebrow">
        <Icon name={view.icon} size={18} />
        {view.eyebrow}
      </p>
      <h1 id="status-title">{view.title}</h1>
      <p className="status-text">{view.text}</p>

      {view.figures.length > 0 && (
        <dl className="figures">
          {view.figures.map((figure) => (
            <div key={figure.label}>
              <dt>{figure.label}</dt>
              <dd>{figure.value}</dd>
            </div>
          ))}
        </dl>
      )}

      <div className="status-actions">
        {warned ? (
          <>
            <button type="button" className="button" onClick={() => goTo("actions")}>
              See what you can do
              <Icon name="arrow" size={18} />
            </button>
            <button type="button" className="button quiet" onClick={() => goTo("ask")}>
              Why?
            </button>
          </>
        ) : (
          <button type="button" className="button quiet" onClick={() => goTo("forecast")}>
            See the forecast
            <Icon name="arrow" size={18} />
          </button>
        )}
      </div>

      {warned && <p className="footnote">A warning is shown when the chance reaches {percent(meta.alert_level)}.</p>}
    </section>
  );
}
