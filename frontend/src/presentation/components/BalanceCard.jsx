import { useText } from "../language.jsx";

// The balance today, and the level the warning rule compares it with.
export default function BalanceCard({ forecast }) {
  const { t, f } = useText();
  const { balance, cushion, typical_daily_spending: usual, as_of: today } = forecast;
  const cushionDays = usual > 0 ? cushion / usual : 0;
  const oneDay = Math.abs(cushionDays - 1) < 0.05;

  return (
    <section className="card" aria-labelledby="balance-title">
      <h2 id="balance-title" className="card-title">
        {t.balance.title}
      </h2>
      <p className="big">
        <span className="sign">৳</span>
        {f.number(balance)}
      </p>
      <p className="card-text">{t.balance.asOf(f.fullDay(today))}</p>

      <dl className="rows">
        <div>
          <dt>
            {t.balance.cushion}
            <small>{oneDay ? t.balance.cushionOneDay : t.balance.cushionDays(f.decimal(cushionDays, 1))}</small>
          </dt>
          <dd>{f.taka(cushion)}</dd>
        </div>
      </dl>
    </section>
  );
}
