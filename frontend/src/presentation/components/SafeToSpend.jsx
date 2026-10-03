import { useText } from "../language.jsx";

// How much the customer can spend each day and still reach the end of the period.
// The API works the number out with a fixed formula; the parts are shown so it can be checked.
export default function SafeToSpend({ forecast }) {
  const { t, f } = useText();
  const text = t.safe;
  const { safe_to_spend: amount, safe_to_spend_parts: parts, window_days: days, window_until: until, income } = forecast;
  const usual = forecast.usual_everyday_spending;
  const period = t.days(f.number(days));
  const nothingLeft = amount < 1;

  return (
    <section className="card" aria-labelledby="safe-title">
      <h2 id="safe-title" className="card-title">
        {text.title}
      </h2>

      <p className={nothingLeft ? "big warn-text" : "big"}>
        <span className="sign">৳</span>
        {f.number(amount)} <span className="unit">{text.aDay}</span>
      </p>
      <p className="card-text">
        {nothingLeft
          ? text.nothing
          : income.next_day === until
            ? text.untilIncome(f.weekDay(until), period)
            : text.until(f.weekDay(until), period)}
      </p>
      {usual >= 1 && <p className="card-text">{text.usual(f.taka(usual))}</p>}

      <details className="how">
        <summary>{text.how}</summary>
        <dl className="sum">
          <div>
            <dt>{text.balance}</dt>
            <dd>{f.taka(parts.balance)}</dd>
          </div>
          <div>
            <dt>{text.income}</dt>
            <dd>+ {f.taka(parts.cautious_income)}</dd>
          </div>
          <div>
            <dt>{text.payments}</dt>
            <dd>− {f.taka(parts.payments_due)}</dd>
          </div>
          <div>
            <dt>{text.cushion}</dt>
            <dd>− {f.taka(parts.cushion)}</dd>
          </div>
          {parts.savings > 0 && (
            <div>
              <dt>{text.savings}</dt>
              <dd>− {f.taka(parts.savings)}</dd>
            </div>
          )}
          <div className="total">
            <dt>{text.left(period)}</dt>
            <dd>{f.taka(parts.left_over)}</dd>
          </div>
        </dl>
        <p className="footnote">
          {parts.left_over > 0 ? text.sum(f.taka(parts.left_over), period, f.taka(amount)) : text.sumNothing} {text.fixed}
        </p>
      </details>
    </section>
  );
}
