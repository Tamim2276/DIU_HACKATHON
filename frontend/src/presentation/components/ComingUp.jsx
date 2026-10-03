import { daysBetween, fromNow, taka, weekDay } from "../../domain/format.js";
import { paymentName } from "../../domain/labels.js";
import Icon from "./Icon.jsx";

const SHOWN = 4; // the rest are on the Forecast screen

const INCOME_WITHOUT_A_DAY = {
  daily: "Your income arrives day by day, so there is no single income day to show.",
  irregular: "Your income has no usual day, so none is shown here.",
};

// The next income and the next regular payments, in the order they fall.
export default function ComingUp({ forecast, goTo }) {
  const { income, regular_payments: payments, as_of: today } = forecast;

  const items = payments.map((payment) => ({
    key: `${payment.recipient}-${payment.date}`,
    day: payment.date,
    name: paymentName(payment.label),
    amount: `− ${taka(payment.amount)}`,
    incoming: false,
  }));
  if (income.next_day) {
    items.push({
      key: "income",
      day: income.next_day,
      name: "Income expected",
      amount: `+ ${taka(income.usual_amount)}`,
      incoming: true,
    });
  }
  items.sort((a, b) => a.day.localeCompare(b.day) || Number(b.incoming) - Number(a.incoming));
  const more = items.length - SHOWN;

  return (
    <section className="card" aria-labelledby="coming-title">
      <h2 id="coming-title" className="card-title">
        Coming up
      </h2>

      {items.length === 0 ? (
        <p className="card-text">No regular payments are due in the next 30 days.</p>
      ) : (
        <ul className="events">
          {items.slice(0, SHOWN).map((item) => (
            <li key={item.key}>
              <span className={item.incoming ? "badge in" : "badge"}>
                <Icon name={item.incoming ? "moneyIn" : "moneyOut"} size={16} />
              </span>
              <span className="event-name">
                {item.name}
                <small>
                  {weekDay(item.day)} · {fromNow(daysBetween(today, item.day))}
                </small>
              </span>
              <span className={item.incoming ? "event-amount in" : "event-amount"}>{item.amount}</span>
            </li>
          ))}
        </ul>
      )}

      {INCOME_WITHOUT_A_DAY[income.kind] && <p className="footnote">{INCOME_WITHOUT_A_DAY[income.kind]}</p>}

      {more > 0 && (
        <button type="button" className="text-button" onClick={() => goTo("forecast")}>
          {more} more on the Forecast screen
        </button>
      )}
    </section>
  );
}
