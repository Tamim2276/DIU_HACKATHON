import { daysBetween, fromNow, taka, weekDay } from "../../domain/format.js";
import { paymentName } from "../../domain/labels.js";
import Icon from "./Icon.jsx";

const INCOME_WITHOUT_A_DAY = {
  daily: "Income arrives day by day, so there is no single income day to show.",
  irregular: "Income has no usual day, so none is shown here.",
};

// Every regular payment and the next income in the forecast period, in the order they fall.
export default function RegularPayments({ forecast }) {
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
  const total = payments.reduce((sum, payment) => sum + payment.amount, 0);

  return (
    <section className="card" aria-labelledby="payments-title">
      <h2 id="payments-title" className="card-title">
        Regular payments in the next 30 days
      </h2>

      {payments.length === 0 ? (
        <p className="card-text">No regular payments were found in this customer's history.</p>
      ) : (
        <p className="card-text">
          {payments.length === 1 ? "1 payment" : `${payments.length} payments`}, {taka(total)} in all. They are found
          from the customer's own history: the same recipient, a similar amount, around the same day each month.
        </p>
      )}

      {items.length > 0 && (
        <ul className="events">
          {items.map((item) => (
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
    </section>
  );
}
