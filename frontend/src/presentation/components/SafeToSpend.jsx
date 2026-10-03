import { dayCount, number, taka, weekDay } from "../../domain/format.js";

// How much the customer can spend each day and still reach the end of the period.
// The API works the number out with a fixed formula; the parts are shown so it can be checked.
export default function SafeToSpend({ forecast }) {
  const { safe_to_spend: amount, safe_to_spend_parts: parts, window_days: days, window_until: until, income } = forecast;
  const untilIncome = income.next_day === until;
  const nothingLeft = amount < 1;

  return (
    <section className="card" aria-labelledby="safe-title">
      <h2 id="safe-title" className="card-title">
        Safe to spend
      </h2>

      <p className={nothingLeft ? "big warn-text" : "big"}>
        <span className="sign">৳</span>
        {number(amount)} <span className="unit">a day</span>
      </p>
      <p className="card-text">
        {untilIncome ? `Until your next income on ${weekDay(until)}` : `Until ${weekDay(until)}`}, {dayCount(days)} from
        now.
        {nothingLeft && " Your regular payments and safety cushion take all the money expected before then."}
      </p>

      <details className="how">
        <summary>How this is worked out</summary>
        <dl className="sum">
          <div>
            <dt>Balance today</dt>
            <dd>{taka(parts.balance)}</dd>
          </div>
          <div>
            <dt>Income expected, counted cautiously</dt>
            <dd>+ {taka(parts.cautious_income)}</dd>
          </div>
          <div>
            <dt>Regular payments due</dt>
            <dd>− {taka(parts.payments_due)}</dd>
          </div>
          <div>
            <dt>Safety cushion kept aside</dt>
            <dd>− {taka(parts.cushion)}</dd>
          </div>
          {parts.savings > 0 && (
            <div>
              <dt>Savings set aside</dt>
              <dd>− {taka(parts.savings)}</dd>
            </div>
          )}
          <div className="total">
            <dt>Left for {dayCount(days)}</dt>
            <dd>{taka(parts.left_over)}</dd>
          </div>
        </dl>
        <p className="footnote">
          {parts.left_over > 0
            ? `${taka(parts.left_over)} over ${dayCount(days)} is ${taka(amount)} a day, rounded down.`
            : "Nothing is left over, so the safe amount is ৳0."}{" "}
          This is a fixed formula, not a guess by the model.
        </p>
      </details>
    </section>
  );
}
