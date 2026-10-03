import { useText } from "../language.jsx";

// How much the customer can spend each day and still pay everything on time until the end of the period.
// The API works the number out with a fixed formula for every day of the period. The day that leaves
// the least decides, and the parts for that day are shown so the number can be checked.
export default function SafeToSpend({ forecast }) {
  const { t, f } = useText();
  const text = t.safe;
  const { safe_to_spend: amount, safe_to_spend_parts: parts, window_days: days, window_until: until, income } = forecast;
  const usual = forecast.usual_everyday_spending;
  const period = t.days(f.number(days));
  const tightDay = f.weekDay(parts.date);
  const tightPeriod = t.days(f.number(parts.days));
  const early = parts.days < days; // a day before the end of the period decides
  const nothingLeft = amount < 1;

  let summary;
  if (!nothingLeft) {
    summary = income.next_day === until ? text.untilIncome(f.weekDay(until), period) : text.until(f.weekDay(until), period);
  } else if (!early) {
    summary = text.nothing;
  } else {
    summary = parts.payments_due >= 1 ? text.nothingBy(tightDay) : text.nothingYet(tightDay);
  }

  return (
    <section className="card" aria-labelledby="safe-title">
      <h2 id="safe-title" className="card-title">
        {text.title}
      </h2>

      <p className={nothingLeft ? "big warn-text" : "big"}>
        <span className="sign">৳</span>
        {f.number(amount)} <span className="unit">{text.aDay}</span>
      </p>
      <p className="card-text">{summary}</p>
      {usual >= 1 && <p className="card-text">{text.usual(f.taka(usual))}</p>}

      <details className="how">
        <summary>{text.how}</summary>
        <p className="footnote">{early ? text.tightest(tightDay, tightPeriod) : text.lastDay(tightDay)}</p>
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
          {!early && (
            <div>
              <dt>{text.cushion}</dt>
              <dd>− {f.taka(parts.cushion)}</dd>
            </div>
          )}
          {parts.savings > 0 && (
            <div>
              <dt>{text.savings}</dt>
              <dd>− {f.taka(parts.savings)}</dd>
            </div>
          )}
          <div className="total">
            <dt>{text.left(tightPeriod)}</dt>
            <dd>{f.taka(parts.left_over)}</dd>
          </div>
        </dl>
        <p className="footnote">
          {parts.left_over > 0 ? text.sum(f.taka(parts.left_over), tightPeriod, f.taka(amount)) : text.sumNothing}{" "}
          {early && `${text.cushionLater} `}
          {text.fixed}
        </p>
      </details>
    </section>
  );
}
