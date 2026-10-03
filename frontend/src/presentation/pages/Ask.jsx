import { useState } from "react";

import { FAILED, LOADING, useExplanation, useQuestions } from "../../application/useExplanation.js";
import { dayCount, fullDay, percent, taka } from "../../domain/format.js";
import ContextBar from "../components/ContextBar.jsx";
import Icon from "../components/Icon.jsx";
import { Failed, Loading } from "../components/ScreenState.jsx";

const LANGUAGES = [
  { id: "bn", name: "বাংলা" },
  { id: "en", name: "English" },
];

// Questions offered as one tap, in the language of the explanation.
const SUGGESTED = {
  en: {
    warning: ["Why do I run short?", "What should I do now?", "How much can I spend each day?"],
    clear: ["Am I safe this month?", "How much can I spend each day?", "When is my next income?"],
  },
  bn: {
    warning: ["আমার টাকা কেন কম পড়বে?", "এখন আমার কী করা উচিত?", "আমি প্রতিদিন কত টাকা খরচ করতে পারব?"],
    clear: ["আমার কি কোনো সমস্যা আছে?", "আমি প্রতিদিন কত টাকা খরচ করতে পারব?", "আমার পরের আয় কবে আসবে?"],
  },
};

const PLACEHOLDER = { en: "Type your question", bn: "আপনার প্রশ্ন লিখুন" };
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
  const rows = [
    ["Balance today", taka(facts.balance)],
    ["Safety cushion", taka(facts.cushion)],
    facts.alert_day && ["First day at risk", fullDay(facts.alert_day)],
    facts.alert_chance !== null && ["Chance of a shortfall", percent(facts.alert_chance)],
    facts.alert_gap !== null && ["Below the cushion, in a cautious estimate", taka(facts.alert_gap)],
    ["Safe to spend a day", taka(facts.safe_to_spend)],
    ["That amount has to last until", fullDay(facts.window_until)],
    facts.next_income_day && ["Next income expected", `${fullDay(facts.next_income_day)}, in ${dayCount(facts.days_to_income)}`],
    ["Regular payments due before then", taka(facts.payments_due)],
    ["Usual everyday spending a day", taka(facts.usual_spending)],
    facts.chance_after !== null && ["Chance with the suggested action", percent(facts.chance_after)],
  ].filter(Boolean);

  return (
    <details className="how">
      <summary>The figures this text was built from</summary>
      <dl className="sum">
        {rows.map(([name, value]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <p className="footnote">
        Each figure comes from the forecasting model or a fixed rule. The text contains no number that is not here.
      </p>
    </details>
  );
}

// The box for follow-up questions and the answers given so far.
function Questions({ selection, language, hasAlert }) {
  const { exchanges, ask, waiting } = useQuestions(selection.userId, selection.asOf, language);
  const [draft, setDraft] = useState("");
  const suggested = SUGGESTED[language][hasAlert ? "warning" : "clear"];

  function send(question) {
    const text = question.trim();
    if (!text || waiting) return;
    ask(text);
    setDraft("");
  }

  return (
    <section className="card" aria-labelledby="ask-title">
      <h2 id="ask-title" className="card-title">
        Ask a follow-up question
      </h2>
      <p className="card-text">
        A language model answers from this customer's figures only. An answer is shown only if every number in it matches
        those figures.
      </p>

      {exchanges.length > 0 && (
        <ol className="exchanges" aria-live="polite">
          {exchanges.map((exchange) => (
            <li key={exchange.id}>
              <p className="asked" lang={language}>
                {exchange.question}
              </p>
              {exchange.status === LOADING && (
                <p className="answer waiting">
                  <span className="spinner small" aria-hidden="true" />
                  Writing an answer. This can take a few seconds.
                </p>
              )}
              {exchange.status === FAILED && <p className="answer unavailable">No answer: {exchange.error}</p>}
              {exchange.source === "llm" && (
                <div className="answer">
                  <p lang={language}>{exchange.text}</p>
                  <p className="answer-source">
                    <Icon name="check" size={14} />
                    Written by AI from the figures above. Every number was checked.
                  </p>
                </div>
              )}
              {exchange.source === "template" && (
                <p className="answer unavailable">
                  The assistant could not give a checked answer just now. The explanation above still holds. Try again in
                  a minute.
                </p>
              )}
            </li>
          ))}
        </ol>
      )}

      <div className="chips">
        {suggested.map((question) => (
          <button key={question} type="button" className="chip" lang={language} disabled={waiting} onClick={() => send(question)}>
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
          Your question
        </label>
        <input
          id="question"
          type="text"
          lang={language}
          value={draft}
          maxLength={MAX_LENGTH}
          placeholder={PLACEHOLDER[language]}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" className="button" disabled={waiting || !draft.trim()}>
          Ask
        </button>
      </form>
    </section>
  );
}

// The explanation in Bangla or English, and follow-up questions.
export default function Ask({ users, selection, language, onLanguage, goTo }) {
  const { status, explanation, error, reload } = useExplanation(selection.userId, selection.asOf, language);
  // While another customer, day or language loads, the text on screen is the previous one.
  const current =
    explanation &&
    explanation.user_id === selection.userId &&
    explanation.as_of === selection.asOf &&
    explanation.language === language;

  return (
    <div className="stack">
      <ContextBar users={users} selection={selection} goTo={goTo} />

      {status === FAILED && <Failed title="The explanation could not be loaded" error={error} onRetry={reload} />}
      {status !== FAILED && !explanation && <Loading heights={[340, 220]} label="Loading the explanation" />}
      {status !== FAILED && explanation && (
        <>
          <section className={current ? "card" : "card outdated"} aria-labelledby="explain-title" aria-busy={!current}>
            <div className="card-head">
              <h1 id="explain-title">{explanation.has_alert ? "Why this warning" : "Where you stand"}</h1>
              <div className="segmented" role="group" aria-label="Language">
                {LANGUAGES.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    lang={option.id}
                    aria-pressed={language === option.id}
                    onClick={() => onLanguage(option.id)}
                  >
                    {option.name}
                  </button>
                ))}
              </div>
            </div>
            <Explanation text={explanation.text} language={explanation.language} />
            <Figures facts={explanation.facts} />
          </section>

          {current && (
            <Questions
              key={`${selection.userId}|${selection.asOf}|${language}`}
              selection={selection}
              language={language}
              hasAlert={explanation.has_alert}
            />
          )}
        </>
      )}
    </div>
  );
}
