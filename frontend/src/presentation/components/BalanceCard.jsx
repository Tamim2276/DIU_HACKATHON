import { fullDay, number, taka } from "../../domain/format.js";

// The balance today, and the level the warning rule compares it with.
export default function BalanceCard({ forecast }) {
  const { balance, cushion, typical_daily_spending: usual, as_of: today } = forecast;
  const cushionDays = usual > 0 ? cushion / usual : 0;
  const cushionIs = Math.abs(cushionDays - 1) < 0.05 ? "One day" : `${cushionDays.toFixed(1)} days`;

  return (
    <section className="card" aria-labelledby="balance-title">
      <h2 id="balance-title" className="card-title">
        Balance
      </h2>
      <p className="big">
        <span className="sign">৳</span>
        {number(balance)}
      </p>
      <p className="card-text">At the end of {fullDay(today)}.</p>

      <dl className="rows">
        <div>
          <dt>
            Safety cushion
            <small>{cushionIs} of your usual spending. A warning means the balance may fall below it.</small>
          </dt>
          <dd>{taka(cushion)}</dd>
        </div>
      </dl>
    </section>
  );
}
