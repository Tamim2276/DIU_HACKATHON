import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { FAILED, useMetrics } from "../../application/useMetrics.js";
import { ASSUMPTIONS, DATA_NOTES_URL, INCOME, LIMITS } from "../../domain/assumptions.js";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";
import { useText } from "../language.jsx";

const ALL = "all users";
const UNSEEN = "users it never saw";
const WEAK_RANKING = 0.75; // a warning ranking under this is called a weak spot
const NARROW_RANGE = 0.72; // so is a range that holds the real balance less often than this

// The simple methods the model is compared with, drawn as differently dashed grey lines.
const DASHES = ["6 4", "2 3", "10 3 2 3"];

function ErrorChart({ byDay }) {
  const { t, f } = useText();
  const text = t.model;
  const names = Object.keys(byDay).filter((name) => name !== "days_ahead" && name !== "model");
  const named = (key) => (key === "model" ? text.modelName : (text.baselines[key] ?? key));
  const rows = byDay.days_ahead.map((day, index) => ({
    day,
    model: byDay.model[index],
    ...Object.fromEntries(names.map((name) => [name, byDay[name][index]])),
  }));

  return (
    <>
      <p className="chart-caption">{text.errorCaption}</p>
      <div className="chart short">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--rule)" strokeDasharray="3 4" />
            <XAxis
              dataKey="day"
              ticks={[1, 7, 14, 21, 30]}
              tickFormatter={(day) => f.number(day)}
              tick={{ fill: "var(--muted)", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "var(--rule)" }}
              tickMargin={8}
            />
            <YAxis
              width={32}
              tickFormatter={(value) => f.number(value)}
              tick={{ fill: "var(--muted)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              isAnimationActive={false}
              cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <div className="chart-tip">
                    <p className="chart-tip-day">{text.daysAhead(f.number(label), label)}</p>
                    <dl>
                      {payload.map((entry) => (
                        <div key={entry.dataKey}>
                          <dt>{named(entry.dataKey)}</dt>
                          <dd>{f.decimal(entry.value)}</dd>
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
          {text.modelName}
        </li>
        {names.map((name, index) => (
          <li key={name}>
            <svg className="key-dash" width="26" height="6" aria-hidden="true">
              <line x1="0" y1="3" x2="26" y2="3" stroke="var(--muted)" strokeWidth="1.6" strokeDasharray={DASHES[index % DASHES.length]} />
            </svg>
            {named(name)}
          </li>
        ))}
      </ul>
    </>
  );
}

// A bar that shows a share against the share it should be.
function Meter({ name, share, target }) {
  const { t, f } = useText();
  const [figure, rest] = t.model.meter(f.percent(share), f.percent(target));
  return (
    <div className="meter">
      <p>
        <strong>{figure}</strong>
        {rest}
        <small>{name}</small>
      </p>
      <div className="meter-track" role="img" aria-label={`${f.percent(share)} / ${f.percent(target)}`}>
        <span className="meter-fill" style={{ width: `${share * 100}%` }} />
        <span className="meter-target" style={{ left: `${target * 100}%` }} />
      </div>
    </div>
  );
}

// The impact test: the same customers with and without the app's advice.
function Impact({ impact }) {
  const { t, f } = useText();
  const text = t.model;
  const { about, runs, changes } = impact;
  const takas = new Set(["borrowed_per_customer"]);
  // shares differ by a point or two here, so they are written with one decimal: 6.3%, not 6%
  const write = (name, value) => (takas.has(name) ? f.taka(value) : `${f.decimal(value * 100, 1)}%`);
  const signed = (name, value) => {
    const sign = value > 0 ? "+" : value < 0 ? "−" : "";
    return takas.has(name) ? `${sign}${f.taka(Math.abs(value))}` : text.impactPoints(`${sign}${f.decimal(Math.abs(value) * 100, 1)}`);
  };
  const rows = Object.keys(text.impactRows).filter((name) => name in runs.without);
  const measured = rows.filter((name) => name in changes.when_warned);

  // What happened to a measure: it clearly fell, clearly rose, or the range still includes "no change".
  const takeaway = (name) => {
    const { low, high } = changes.when_warned[name];
    const say = high < 0 ? text.impactFell : low > 0 ? text.impactRose : text.impactSame;
    return say(text.impactRows[name], write(name, runs.without[name]), write(name, runs.when_warned[name]));
  };

  return (
    <section className="card" aria-labelledby="impact-title">
      <h2 id="impact-title" className="section-title">
        {text.impactTitle}
      </h2>
      <p className="card-text wide">
        {text.impactText(f.number(about.customers), f.fullDay(about.period.from), f.fullDay(about.period.to))}
      </p>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <td />
              <th scope="col">{text.impactWithout}</th>
              <th scope="col">{text.impactWarned}</th>
              <th scope="col">{text.impactEvery}</th>
              <th scope="col">{text.impactChange}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((name) => {
              const change = changes.when_warned[name];
              return (
                <tr key={name}>
                  <th scope="row">{text.impactRows[name]}</th>
                  <td>{name === "days_warned" ? "–" : write(name, runs.without[name])}</td>
                  <td>{write(name, runs.when_warned[name])}</td>
                  <td>{write(name, runs.every_day[name])}</td>
                  <td>
                    {change ? (
                      <>
                        {signed(name, change.change)}
                        <small>{text.impactRange(signed(name, change.low), signed(name, change.high))}</small>
                      </>
                    ) : (
                      "–"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="prose-heading spaced">{text.impactTakeaways}</p>
      <ul className="plain-list">
        {measured.map((name) => (
          <li key={name}>{takeaway(name)}</li>
        ))}
      </ul>
      <p className="footnote spaced">
        {text.impactMoral} {text.impactHalfNote} {text.impactNote}
      </p>
    </section>
  );
}

export default function ModelReport({ meta }) {
  const { t, f, language } = useText();
  const text = t.model;
  const { status, metrics, impact, error, reload } = useMetrics();

  if (status === FAILED) return <Failed title={t.state.resultsFailed} error={error} onRetry={reload} />;
  if (!metrics) return <Loading heights={[220, 420, 260]} />;

  const { about, checks, early_warning: warning, by_persona: personas } = metrics;
  const horizons = metrics.error[ALL].filter((row) => typeof row.days_ahead === "number");
  const unseen = metrics.error[UNSEEN].filter((row) => typeof row.days_ahead === "number").map((row) => row.better_than_best_baseline_by);
  const overall = metrics.range[ALL].find((row) => typeof row.days_ahead !== "number") ?? metrics.range[ALL].at(-1);
  const bestBaseline = (row) =>
    Math.min(...Object.entries(row.in_days_of_spending).filter(([name]) => name !== "model").map(([, value]) => value));
  const label = (persona) => text.personaLabels[persona.persona] ?? persona.label;
  const listed = (group) => group.map((persona) => text.plural(label(persona))).join(text.and);
  const weakWarnings = personas.filter((persona) => persona.warning_ranking < WEAK_RANKING);
  const narrowRanges = personas.filter((persona) => persona.inside_p10_p90 < NARROW_RANGE);

  // "model, chance of going under the cushion at least 40% (used in the app)" -> "Model, warning at 40%"
  const ruleName = (rule) => {
    if (rule.startsWith("simple rule")) return text.ruleSimple;
    const level = rule.match(/at least (\d+)%/);
    return level ? text.ruleLevel(f.number(Number(level[1]))) : text.ruleSame;
  };

  const passed = [
    checks.beats_every_baseline_at_7_14_30_days,
    checks.range_is_honest_70_to_90_percent,
    checks.warnings_beat_the_simple_rule,
  ];

  return (
    <div className="stack">
      <section className="card" aria-labelledby="report-title">
        <h1 id="report-title">{text.title}</h1>
        <p className="card-text wide">
          {text.intro(
            f.fullDay(about.trained_up_to),
            f.fullDay(about.test_period.from),
            f.fullDay(about.test_period.to),
            f.number(about.forecasts_tested),
            f.number(about.users.all),
            f.number(about.users.never_seen),
          )}
        </p>
        <p className="callout">
          <Icon name="info" size={18} />
          <span>{text.synthetic}</span>
        </p>
        <ul className="checks">
          {passed.map((ok, index) => (
            <li key={text.checks[index]} className={ok ? "ok" : "bad"}>
              <Icon name={ok ? "check" : "warning"} size={18} />
              {text.checks[index]}
            </li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="error-title">
        <h2 id="error-title" className="section-title">
          {text.errorTitle}
        </h2>
        <p className="card-text wide">{text.errorText}</p>
        <ErrorChart byDay={metrics.error_by_days_ahead} />
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{text.colDays}</th>
                <th scope="col">{text.colModel}</th>
                <th scope="col">{text.colBest}</th>
                <th scope="col">{text.colBetter}</th>
              </tr>
            </thead>
            <tbody>
              {horizons.map((row) => (
                <tr key={row.days_ahead}>
                  <th scope="row">{f.number(row.days_ahead)}</th>
                  <td>{f.decimal(row.in_days_of_spending.model)}</td>
                  <td>{f.decimal(bestBaseline(row))}</td>
                  <td className="good">{f.percent(row.better_than_best_baseline_by)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          {text.unseen(f.number(about.users.never_seen), f.percent(Math.min(...unseen)), f.percent(Math.max(...unseen)), about.model)}
        </p>
      </section>

      <section className="card" aria-labelledby="range-title">
        <h2 id="range-title" className="section-title">
          {text.rangeTitle}
        </h2>
        <p className="card-text wide">{text.rangeText}</p>
        <Meter name={text.meterWide} share={overall.inside_p10_p90} target={0.8} />
        <Meter name={text.meterNarrow} share={overall.inside_p25_p75} target={0.5} />
        <p className="footnote">{text.meterNote}</p>
      </section>

      <section className="card" aria-labelledby="warning-title">
        <h2 id="warning-title" className="section-title">
          {text.warningTitle}
        </h2>
        <p className="card-text wide">
          {text.warningText(t.days(f.number(meta.warning_days)), f.number(warning.days_asked), f.percent(warning.share_followed_by_a_shortfall))}
        </p>
        <dl className="figures tight">
          <div>
            <dt>{text.rankModel}</dt>
            <dd>{f.decimal(warning.ranking_quality.model)}</dd>
          </div>
          <div>
            <dt>{text.rankRule}</dt>
            <dd>{f.decimal(warning.ranking_quality["simple rule"])}</dd>
          </div>
        </dl>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{text.colRule}</th>
                <th scope="col">{text.colCaught}</th>
                <th scope="col">{text.colRight}</th>
                <th scope="col">{text.colFalse}</th>
              </tr>
            </thead>
            <tbody>
              {warning.warnings.map((row) => {
                const inApp = row.warning.includes("used in the app");
                return (
                  <tr key={row.warning} className={inApp ? "chosen" : undefined}>
                    <th scope="row">
                      {ruleName(row.warning)}
                      {inApp && <small>{text.inApp}</small>}
                    </th>
                    <td>{f.percent(row.caught)}</td>
                    <td>{f.percent(row.right)}</td>
                    <td>{f.percent(row.false_alarms)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="footnote">{text.warningNote(f.percent(warning.alert_level_used_in_the_app))}</p>
      </section>

      <section className="card" aria-labelledby="persona-title">
        <h2 id="persona-title" className="section-title">
          {text.personaTitle}
        </h2>
        <p className="card-text wide">{text.personaText}</p>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{text.colCustomer}</th>
                <th scope="col">{text.colModel}</th>
                <th scope="col">{text.colBest}</th>
                <th scope="col">{text.colBetterBy}</th>
                <th scope="col">{text.colInside}</th>
                <th scope="col">{text.colRanking}</th>
              </tr>
            </thead>
            <tbody>
              {personas.map((persona) => (
                <tr key={persona.persona}>
                  <th scope="row">{label(persona)}</th>
                  <td>{f.decimal(persona.error_14_days)}</td>
                  <td>{f.decimal(persona.best_baseline_14_days)}</td>
                  <td className="good">{f.percent(persona.better_by)}</td>
                  <td className={persona.inside_p10_p90 < NARROW_RANGE ? "weak" : undefined}>{f.percent(persona.inside_p10_p90)}</td>
                  <td className={persona.warning_ranking < WEAK_RANKING ? "weak" : undefined}>{f.decimal(persona.warning_ranking)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(weakWarnings.length > 0 || narrowRanges.length > 0) && (
          <p className="footnote">
            {text.weak}
            {weakWarnings.length > 0 && text.weakWarnings(listed(weakWarnings))}
            {narrowRanges.length > 0 && text.weakRange(listed(narrowRanges))}
          </p>
        )}
      </section>

      {impact && <Impact impact={impact} />}

      <section className="card" aria-labelledby="data-title">
        <h2 id="data-title" className="section-title">
          {text.dataTitle}
        </h2>
        <ul className="plain-list">
          {ASSUMPTIONS[language].map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
        <div className="table-scroll">
          <table className="table text">
            <thead>
              <tr>
                <th scope="col">{text.colCustomer}</th>
                <th scope="col">{text.colIncome}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(INCOME[language]).map(([persona, income]) => (
                <tr key={persona}>
                  <th scope="row">{text.personaLabels[persona]}</th>
                  <td>{income}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="footnote">
          <a href={DATA_NOTES_URL} target="_blank" rel="noreferrer">
            {text.allAssumptions}
          </a>
        </p>
      </section>

      <section className="card" aria-labelledby="limits-title">
        <h2 id="limits-title" className="section-title">
          {text.limitsTitle}
        </h2>
        <ul className="plain-list">
          {LIMITS[language].map((limit) => (
            <li key={limit}>{limit}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
