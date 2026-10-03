import { useText } from "../language.jsx";
import { Events, upcoming } from "./ComingUp.jsx";

// Every regular payment and the next income in the forecast period, in the order they fall.
export default function RegularPayments({ forecast, meta }) {
  const { t, f } = useText();
  const text = t.forecast;
  const { regular_payments: payments } = forecast;
  const items = upcoming(forecast, t, f);
  const total = payments.reduce((sum, payment) => sum + payment.amount, 0);
  const note = { daily: text.incomeDaily, irregular: text.incomeIrregular }[forecast.income.kind];

  return (
    <section className="card" aria-labelledby="payments-title">
      <h2 id="payments-title" className="card-title">
        {text.paymentsTitle(f.number(meta.horizon_days))}
      </h2>

      <p className="card-text wide">
        {payments.length === 0 ? text.noPayments : text.paymentsText(f.number(payments.length), f.taka(total))}
      </p>

      {items.length > 0 && <Events items={items} today={forecast.as_of} />}
      {note && <p className="footnote">{note}</p>}
    </section>
  );
}
