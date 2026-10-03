import { daysBetween, whole } from "../../domain/format.js";
import { CLEAR, LOW_NOW, RECOVERING, SHORTFALL, statusOf } from "../../domain/status.js";
import { useText } from "../language.jsx";
import Icon from "./Icon.jsx";

// The first thing a customer reads: is a shortfall likely, or not?
// What to say comes from the forecast. Only the words are chosen here.
function describe(forecast, meta, t, f) {
  const { alert, as_of: today } = forecast;
  const text = t.status;
  const balance = f.taka(forecast.balance);
  const cushion = f.taka(forecast.cushion);
  const period = t.days(f.number(meta.warning_days));
  // the cushion is one day of the customer's usual spending unless the rule was changed
  const oneDay = Math.abs(forecast.cushion / (forecast.typical_daily_spending || 1) - 1) < 0.05;

  switch (statusOf(forecast)) {
    case SHORTFALL: {
      const away = daysBetween(today, alert.date);
      const empty = whole(alert.gap) >= whole(alert.cushion); // the cautious forecast reaches zero
      return {
        tone: "warn",
        icon: "warning",
        eyebrow: text.warning,
        title: text.shortfallTitle(f.weekDay(alert.date)),
        text: text.shortfallText(t.fromNow(f.number(away), away), cushion, oneDay),
        figures: [
          { value: f.percent(alert.probability), label: text.chance },
          empty ? { value: f.taka(0), label: text.left } : { value: f.taka(alert.gap), label: text.short },
        ],
      };
    }
    case LOW_NOW:
      return {
        tone: "warn",
        icon: "warning",
        eyebrow: text.warning,
        title: text.lowNowTitle,
        text: text.lowNowText(balance, cushion, period),
        figures: [{ value: f.percent(alert.probability), label: text.chance }],
      };
    case RECOVERING:
      return {
        tone: "note",
        icon: "info",
        eyebrow: text.noWarning,
        title: text.recoveringTitle,
        text: text.recoveringText(balance, cushion, period),
        // no warning, yet the payments due are more than the money expected: say so, or the two cards disagree
        extra: forecast.safe_to_spend_parts.left_over < 0 ? text.recoveringButPayments : null,
        figures: [],
      };
    case CLEAR:
    default:
      return {
        tone: "ok",
        icon: "check",
        eyebrow: text.allClear,
        title: text.clearTitle(period),
        text: text.clearText(balance, cushion),
        figures: [],
      };
  }
}

export default function AlertCard({ forecast, meta, goTo }) {
  const { t, f } = useText();
  const view = describe(forecast, meta, t, f);
  const warned = view.tone === "warn";

  return (
    <section className={`status ${view.tone}`} aria-labelledby="status-title">
      <p className="status-eyebrow">
        <Icon name={view.icon} size={18} />
        {view.eyebrow}
      </p>
      <h1 id="status-title">{view.title}</h1>
      <p className="status-text">{view.text}</p>
      {view.extra && <p className="status-text">{view.extra}</p>}

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
              {t.status.seeActions}
              <Icon name="arrow" size={18} />
            </button>
            <button type="button" className="button quiet" onClick={() => goTo("ask")}>
              {t.status.why}
            </button>
          </>
        ) : (
          <button type="button" className="button quiet" onClick={() => goTo("forecast")}>
            {t.status.seeForecast}
            <Icon name="arrow" size={18} />
          </button>
        )}
      </div>

      {warned && <p className="footnote">{t.status.rule(f.percent(meta.alert_level))}</p>}
    </section>
  );
}
