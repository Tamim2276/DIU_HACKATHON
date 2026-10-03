import { daysBetween } from "../../domain/format.js";
import { useText } from "../language.jsx";
import Icon from "./Icon.jsx";

// The next income and the regular payments in the forecast period, in the order they fall, as rows of a list.
// Used on Home (the first few) and on the Forecast screen (all of them).
export function upcoming(forecast, t, f) {
  const { income, regular_payments: payments } = forecast;
  const items = payments.map((payment) => ({
    key: `${payment.recipient}-${payment.date}`,
    day: payment.date,
    name: t.payments[payment.label] ?? t.payments.other,
    amount: `− ${f.taka(payment.amount)}`,
    incoming: false,
  }));
  if (income.next_day) {
    items.push({
      key: "income",
      day: income.next_day,
      name: t.coming.income,
      amount: `+ ${f.taka(income.usual_amount)}`,
      incoming: true,
    });
  }
  return items.sort((a, b) => a.day.localeCompare(b.day) || Number(b.incoming) - Number(a.incoming));
}

export function Events({ items, today }) {
  const { t, f } = useText();
  return (
    <ul className="events">
      {items.map((item) => {
        const away = daysBetween(today, item.day);
        return (
          <li key={item.key}>
            <span className={item.incoming ? "badge in" : "badge"}>
              <Icon name={item.incoming ? "moneyIn" : "moneyOut"} size={16} />
            </span>
            <span className="event-name">
              {item.name}
              <small>
                {f.weekDay(item.day)} · {t.fromNow(f.number(away), away)}
              </small>
            </span>
            <span className={item.incoming ? "event-amount in" : "event-amount"}>{item.amount}</span>
          </li>
        );
      })}
    </ul>
  );
}

const SHOWN = 4; // the rest are on the Forecast screen

export default function ComingUp({ forecast, meta, goTo }) {
  const { t, f } = useText();
  const items = upcoming(forecast, t, f);
  const more = items.length - SHOWN;
  const note = { daily: t.coming.daily, irregular: t.coming.irregular }[forecast.income.kind];

  return (
    <section className="card" aria-labelledby="coming-title">
      <h2 id="coming-title" className="card-title">
        {t.coming.title}
      </h2>

      {items.length === 0 ? (
        <p className="card-text">{t.coming.none(f.number(meta.horizon_days))}</p>
      ) : (
        <Events items={items.slice(0, SHOWN)} today={forecast.as_of} />
      )}

      {note && <p className="footnote">{note}</p>}

      {more > 0 && (
        <button type="button" className="text-button" onClick={() => goTo("forecast")}>
          {t.coming.more(f.number(more))}
        </button>
      )}
    </section>
  );
}
