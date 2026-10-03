import { useState } from "react";

import { FAILED, LOADING, useExplanation, useQuestions } from "../../application/useExplanation.js";
import ContextBar from "../components/ContextBar.jsx";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";
import { useText } from "../language.jsx";

const MAX_LENGTH = 300; // the API refuses a longer question

// The explanation as paragraphs. A paragraph with "•" lines becomes a heading and a list.
function Explanation({ text, language }) {
  return (
    <div className="prose" lang={language}>
      {text.split("\n\n").map((paragraph, index) => {
        const lines = paragraph.split("\n");
        const points = lines.filter((line) => line.startsWith("• ")).map((line) => line.slice(2));
        if (points.length === 0) return <p key={index}>{paragraph}</p>;
        const heading = lines.filter((line) => !line.startsWith("• ")).join(" ");
        return (
          <div key={index}>
            {heading && <p className="prose-heading">{heading}</p>}
            <ul>
              {points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

// The figures the text was built from, so a reader can check that nothing was made up.
function Figures({ facts }) {
  const { t, f } = useText();
  const names = t.ask.facts;
  const rows = [
    [names.balance, f.taka(facts.balance)],
    [names.cushion, f.taka(facts.cushion)],
    facts.alert_day && [names.alertDay, f.fullDay(facts.alert_day)],
    facts.alert_chance !== null && [names.chance, f.percent(facts.alert_chance)],
    facts.alert_gap !== null && [names.gap, f.taka(facts.alert_gap)],
    [names.safe, f.taka(facts.safe_to_spend)],
    [names.until, f.fullDay(facts.window_until)],
    facts.next_income_day && [
      names.income,
      names.incomeIn(f.fullDay(facts.next_income_day), t.days(f.number(facts.days_to_income))),
      "wraps", // a day and a count of days: too long for one line on a narrow phone
    ],
    [names.payments, f.taka(facts.payments_due)],
    [names.usual, f.taka(facts.usual_spending)],
    facts.chance_after !== null && [names.chanceAfter, f.percent(facts.chance_after)],
  ].filter(Boolean);

  return (
    <details className="how">
      <summary>{t.ask.figures}</summary>
      <dl className="sum">
        {rows.map(([name, value, look]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd className={look}>{value}</dd>
          </div>
        ))}
      </dl>
      <p className="footnote">{t.ask.figuresNote}</p>
    </details>
  );
}

// The box for follow-up questions and the answers given so far.
function Questions({ selection, hasAlert }) {
  const { t, language } = useText();
  const text = t.ask;
  const { exchanges, ask, waiting } = useQuestions(selection.userId, selection.asOf, language, selection.goal);
  const [draft, setDraft] = useState("");
  const suggested = text.suggested[hasAlert ? "warning" : "clear"];

  function send(question) {
    const words = question.trim();
    if (!words || waiting) return;
    ask(words);
    setDraft("");
  }

  return (
    <section className="card" aria-labelledby="ask-title">
      <h2 id="ask-title" className="card-title">
        {text.questionsTitle}
      </h2>
      <p className="card-text">{text.questionsText}</p>

      {exchanges.length > 0 && (
        <ol className="exchanges" aria-live="polite">
          {exchanges.map((exchange) => (
            <li key={exchange.id}>
              <p className="asked">{exchange.question}</p>
              {exchange.status === LOADING && (
                <p className="answer waiting">
                  <span className="spinner small" aria-hidden="true" />
                  {text.waiting}
                </p>
              )}
              {exchange.status === FAILED && <p className="answer unavailable">{text.noAnswer(exchange.error)}</p>}
              {exchange.source === "llm" && (
                <div className="answer">
                  <p>{exchange.text}</p>
                  <p className="answer-source">
                    <Icon name="check" size={14} />
                    {text.byAi}
                  </p>
                </div>
              )}
              {exchange.source === "template" && <p className="answer unavailable">{text.unavailable}</p>}
            </li>
          ))}
        </ol>
      )}

      <div className="chips">
        {suggested.map((question) => (
          <button key={question} type="button" className="chip" disabled={waiting} onClick={() => send(question)}>
            {question}
          </button>
        ))}
      </div>

      <form
        className="ask-form"
        onSubmit={(event) => {
          event.preventDefault();
          send(draft);
        }}
      >
        <label className="visually-hidden" htmlFor="question">
          {text.yourQuestion}
        </label>
        <input
          id="question"
          type="text"
          value={draft}
          maxLength={MAX_LENGTH}
          placeholder={text.placeholder}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" className="button" disabled={waiting || !draft.trim()}>
          {text.send}
        </button>
      </form>
    </section>
  );
}

// The explanation in the app's language, and follow-up questions.
export default function Ask({ users, selection, goTo }) {
  const { t, language } = useText();
  const { status, explanation, error, reload } = useExplanation(selection.userId, selection.asOf, language, selection.goal);
  // While another customer, day or language loads, the text on screen is the previous one.
  const current =
    explanation &&
    explanation.user_id === selection.userId &&
    explanation.as_of === selection.asOf &&
    explanation.language === language;

  return (
    <div className="stack">
      <ContextBar users={users} selection={selection} goTo={goTo} />

      {status === FAILED && <Failed title={t.state.explanationFailed} error={error} onRetry={reload} />}
      {status !== FAILED && !explanation && <Loading heights={[340, 220]} />}
      {status !== FAILED && explanation && (
        <>
          <section className={current ? "card" : "card outdated"} aria-labelledby="explain-title" aria-busy={!current}>
            <h1 id="explain-title">{explanation.has_alert ? t.ask.whyWarning : t.ask.whereYouStand}</h1>
            <Explanation text={explanation.text} language={explanation.language} />
            <Figures facts={explanation.facts} />
          </section>

          {current && (
            <Questions
              key={`${selection.userId}|${selection.asOf}|${language}`}
              selection={selection}
              hasAlert={explanation.has_alert}
            />
          )}
        </>
      )}
    </div>
  );
}
