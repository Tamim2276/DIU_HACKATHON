import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { FAILED, useMetrics } from "../../application/useMetrics.js";
import { ASSUMPTIONS, DATA_NOTES_URL, LIMITS, PERSONAS } from "../../domain/assumptions.js";
import { fullDay, number, percent } from "../../domain/format.js";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";

const ALL = "all users";
const UNSEEN = "users it never saw";
const WEAK_RANKING = 0.75; // a warning ranking under this is called a weak spot
const NARROW_RANGE = 0.72; // so is a range that holds the real balance less often than this

const two = (value) => value.toFixed(2);
const sentence = (text) => text.charAt(0).toUpperCase() + text.slice(1);

// The simple methods the model is compared with, drawn as differently dashed grey lines.
const DASHES = ["6 4", "2 3", "10 3 2 3"];

function ErrorChart({ byDay }) {
  const names = Object.keys(byDay).filter((name) => name !== "days_ahead" && name !== "model");
  const rows = byDay.days_ahead.map((day, index) => ({
    day,
    model: byDay.model[index],
    ...Object.fromEntries(names.map((name) => [name, byDay[name][index]])),
  }));

  return (
    <>
      <div className="chart short">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--rule)" strokeDasharray="3 4" />
            <XAxis
              dataKey="day"
              ticks={[1, 7, 14, 21, 30]}
              tick={{ fill: "var(--muted)", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "var(--rule)" }}
              tickMargin={8}
            />
            <YAxis width={32} tick={{ fill: "var(--muted)", fontSize: 12 }} tickLine={false} axisLine={false} />
            <Tooltip
              isAnimationActive={false}
              cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <div className="chart-tip">
                    <p className="chart-tip-day">{label === 1 ? "1 day ahead" : `${label} days ahead`}</p>
                    <dl>
                      {payload.map((entry) => (
                        <div key={entry.dataKey}>
                          <dt>{entry.dataKey === "model" ? "Model" : sentence(entry.dataKey)}</dt>
                          <dd>{two(entry.value)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ) : null
              }
            />
            {names.map((name, index) => (
              <Line
                key={name}
                dataKey={name}
                stroke="var(--muted)"
                strokeWidth={1.6}
                strokeDasharray={DASHES[index % DASHES.length]}
                dot={false}
                activeDot={false}
                isAnimationActive={false}
              />
            ))}
            <Line dataKey="model" stroke="var(--accent)" strokeWidth={2.8} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ul className="chart-key">
        <li>
          <span className="key-line" />
          Model
        </li>
        {names.map((name, index) => (
          <li key={name}>
            <svg className="key-dash" width="26" height="6" aria-hidden="true">
              <line x1="0" y1="3" x2="26" y2="3" stroke="var(--muted)" strokeWidth="1.6" strokeDasharray={DASHES[index % DASHES.length]} />
            </svg>
            {sentence(name)}
          </li>
        ))}
      </ul>
    </>
  );
}

// A bar that shows a share against the share it should be.
function Meter({ name, share, target }) {
  return (
    <div className="meter">
      <p>
        <strong>{percent(share)}</strong> of real balances fell inside the range meant to hold {percent(target)}
        <small>{name}</small>
      </p>
      <div className="meter-track" role="img" aria-label={`${percent(share)} against a target of ${percent(target)}`}>
        <span className="meter-fill" style={{ width: `${share * 100}%` }} />
        <span className="meter-target" style={{ left: `${target * 100}%` }} />
      </div>
    </div>
  );
}

// "model, chance of going under the cushion at least 40% (used in the app)" -> "Model, warning at 40%"
function warningName(text) {
  if (text.startsWith("simple rule")) return "Simple rule: the 3-month average";
  const level = text.match(/at least (\d+)%/);
  if (level) return `Model, warning at ${level[1]}%`;
  return "Model, set to the same false alarms as the simple rule";
}

export default function ModelReport({ meta }) {
  const { status, metrics, error, reload } = useMetrics();

  if (status === FAILED) return <Failed title="The test results could not be loaded" error={error} onRetry={reload} />;
  if (!metrics) return <Loading heights={[220, 420, 260]} label="Loading the test results" />;

  const { about, checks, early_warning: warning, by_persona: personas } = metrics;
  const horizons = metrics.error[ALL].filter((row) => typeof row.days_ahead === "number");
  const unseen = metrics.error[UNSEEN].filter((row) => typeof row.days_ahead === "number");
  const overall = metrics.range[ALL].find((row) => typeof row.days_ahead !== "number") ?? metrics.range[ALL].at(-1);
  const bestBaseline = (row) =>
    Math.min(...Object.entries(row.in_days_of_spending).filter(([name]) => name !== "model").map(([, value]) => value));
  const share = (rows) => `${percent(Math.min(...rows.map((row) => row.better_than_best_baseline_by)))} to ${percent(Math.max(...rows.map((row) => row.better_than_best_baseline_by)))}`;
  const weakWarnings = personas.filter((persona) => persona.warning_ranking < WEAK_RANKING);
  const narrowRanges = personas.filter((persona) => persona.inside_p10_p90 < NARROW_RANGE);

  const passed = [
    [checks.beats_every_baseline_at_7_14_30_days, "Beats every simple method at 7, 14 and 30 days"],
    [checks.range_is_honest_70_to_90_percent, "The range holds the real balance about as often as it says"],
    [checks.warnings_beat_the_simple_rule, "Warnings are better than the simple rule"],
  ];

  return (
    <div className="stack">
      <section className="card" aria-labelledby="report-title">
        <h1 id="report-title">How good is the forecast?</h1>
        <p className="card-text wide">
          The model learned from data up to {fullDay(about.trained_up_to)}. It was then tested on forecasts made from{" "}
          {fullDay(about.test_period.from)} to {fullDay(about.test_period.to)}, days it had never seen:{" "}
          {number(about.forecasts_tested)} forecasts for {about.users.all} customers, {about.users.never_seen} of whom it
          had never seen at all.
        </p>
        <p className="callout">
          <Icon name="info" size={18} />
          <span>
            All results on this screen come from synthetic data. They show that the method finds the patterns put into
            that data. They do not show how it would do with real customers.
          </span>
        </p>
        <ul className="checks">
          {passed.map(([ok, text]) => (
            <li key={text} className={ok ? "ok" : "bad"}>
              <Icon name={ok ? "check" : "warning"} size={18} />
              {text}
            </li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="error-title">
        <h2 id="error-title" className="section-title">
          Against simple methods
        </h2>
        <p className="card-text wide">
          The error is measured in days of the customer's usual spending: 3.4 means the forecast balance was off by about
          three and a half days of spending. Lower is better. The further ahead, the harder the forecast.
        </p>
        <p className="chart-caption">Error for each number of days ahead, from 1 to 30</p>
        <ErrorChart byDay={metrics.error_by_days_ahead} />
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Days ahead</th>
                <th scope="col">Model</th>
                <th scope="col">Best simple method</th>
                <th scope="col">Model is better by</th>
              </tr>
            </thead>
            <tbody>
              {horizons.map((row) => (
                <tr key={row.days_ahead}>
                  <th scope="row">{row.days_ahead}</th>
                  <td>{two(row.in_days_of_spending.model)}</td>
                  <td>{two(bestBaseline(row))}</td>
                  <td className="good">{percent(row.better_than_best_baseline_by)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          For the {about.users.never_seen} customers the model never saw, it is still better by {share(unseen)}. The
          model: {about.model}.
        </p>
      </section>

      <section className="card" aria-labelledby="range-title">
        <h2 id="range-title" className="section-title">
          Is the range honest?
        </h2>
        <p className="card-text wide">
          A forecast gives a range, not one number. The range is honest if the real balance falls inside it as often as
          it claims.
        </p>
        <Meter name="The wider range on the chart, over all 30 days" share={overall.inside_p10_p90} target={0.8} />
        <Meter name="The narrower range on the chart, over all 30 days" share={overall.inside_p25_p75} target={0.5} />
        <p className="footnote">
          The bar is the share the range really held. The dark mark is the share it is meant to hold.
        </p>
      </section>

      <section className="card" aria-labelledby="warning-title">
        <h2 id="warning-title" className="section-title">
          Early warnings
        </h2>
        <p className="card-text wide">
          The question: on a day when the customer is not short, will they run short in the next {meta.warning_days} days?
          Out of {number(warning.days_asked)} such days in the test, {percent(warning.share_followed_by_a_shortfall)}{" "}
          were followed by a shortfall.
        </p>
        <dl className="figures tight">
          <div>
            <dt>ranking quality of the model (1 is perfect, 0.5 is a coin toss)</dt>
            <dd>{two(warning.ranking_quality.model)}</dd>
          </div>
          <div>
            <dt>ranking quality of the simple rule</dt>
            <dd>{two(warning.ranking_quality["simple rule"])}</dd>
          </div>
        </dl>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Warning rule</th>
                <th scope="col">Shortfalls caught</th>
                <th scope="col">Warnings that were right</th>
                <th scope="col">False alarms</th>
              </tr>
            </thead>
            <tbody>
              {warning.warnings.map((row) => {
                const inApp = row.warning.includes("used in the app");
                return (
                  <tr key={row.warning} className={inApp ? "chosen" : undefined}>
                    <th scope="row">
                      {warningName(row.warning)}
                      {inApp && <small>used in the app</small>}
                    </th>
                    <td>{percent(row.caught)}</td>
                    <td>{percent(row.right)}</td>
                    <td>{percent(row.false_alarms)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          Caught: the share of real shortfalls that had a warning. Right: the share of warnings that were followed by a
          shortfall. False alarms: the share of safe periods that got a warning anyway. A lower warning level catches
          more and cries wolf more; {percent(warning.alert_level_used_in_the_app)} was chosen as the balance.
        </p>
      </section>

      <section className="card" aria-labelledby="persona-title">
        <h2 id="persona-title" className="section-title">
          By kind of customer
        </h2>
        <p className="card-text wide">Error 14 days ahead, in days of usual spending, and how the range and the warnings hold up.</p>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Customer</th>
                <th scope="col">Model</th>
                <th scope="col">Best simple method</th>
                <th scope="col">Better by</th>
                <th scope="col">Inside the wider range</th>
                <th scope="col">Warning ranking</th>
              </tr>
            </thead>
            <tbody>
              {personas.map((persona) => (
                <tr key={persona.persona}>
                  <th scope="row">{persona.label}</th>
                  <td>{two(persona.error_14_days)}</td>
                  <td>{two(persona.best_baseline_14_days)}</td>
                  <td className="good">{percent(persona.better_by)}</td>
                  <td className={persona.inside_p10_p90 < NARROW_RANGE ? "weak" : undefined}>{percent(persona.inside_p10_p90)}</td>
                  <td className={persona.warning_ranking < WEAK_RANKING ? "weak" : undefined}>{two(persona.warning_ranking)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(weakWarnings.length > 0 || narrowRanges.length > 0) && (
          <p className="footnote">
            Weak spots, marked in the table:
            {weakWarnings.length > 0 &&
              ` warnings are least reliable for ${weakWarnings.map((persona) => `${persona.label.toLowerCase()}s`).join(" and ")}, whose income arrives day by day.`}
            {narrowRanges.length > 0 &&
              ` The range is too narrow for ${narrowRanges.map((persona) => `${persona.label.toLowerCase()}s`).join(" and ")}, whose income is the hardest to predict.`}
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="data-title">
        <h2 id="data-title" className="section-title">
          What the data assumes
        </h2>
        <ul className="plain-list">
          {ASSUMPTIONS.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
        <div className="table-scroll">
          <table className="table text">
            <thead>
              <tr>
                <th scope="col">Customer</th>
                <th scope="col">How income arrives in the data</th>
              </tr>
            </thead>
            <tbody>
              {PERSONAS.map((persona) => (
                <tr key={persona.name}>
                  <th scope="row">{persona.name}</th>
                  <td>{persona.income}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          <a href={DATA_NOTES_URL} target="_blank" rel="noreferrer">
            Every assumption, in full
          </a>
        </p>
      </section>

      <section className="card" aria-labelledby="limits-title">
        <h2 id="limits-title" className="section-title">
          Limits
        </h2>
        <ul className="plain-list">
          {LIMITS.map((limit) => (
            <li key={limit}>{limit}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
