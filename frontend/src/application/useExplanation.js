import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// The standard explanation for the chosen customer and day, in Bangla ("bn") or English ("en").
export function useExplanation(userId, asOf, language, goal) {
  const [state, setState] = useState({ status: LOADING, explanation: null, error: null });
  const [run, setRun] = useState(0);
  const amount = goal?.amount ?? null;
  const date = goal?.date ?? null;

  useEffect(() => {
    let outdated = false;
    setState((before) => ({ ...before, status: LOADING, error: null }));
    api
      .explain(userId, asOf, language, null, amount === null ? null : { amount, date })
      .then((explanation) => {
        if (!outdated) setState({ status: READY, explanation, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, explanation: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [userId, asOf, language, amount, date, run]);

  const reload = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, reload };
}

// Follow-up questions and their answers, newest last.
// An answer has `source`: "llm" when the language model answered, "template" when it could not.
export function useQuestions(userId, asOf, language, goal) {
  const [exchanges, setExchanges] = useState([]);
  const nextId = useRef(1);

  const ask = useCallback(
    (question) => {
      const id = nextId.current++;
      const settle = (change) =>
        setExchanges((before) => before.map((exchange) => (exchange.id === id ? { ...exchange, ...change } : exchange)));
      setExchanges((before) => [...before, { id, question, status: LOADING }]);
      api
        .explain(userId, asOf, language, question, goal)
        .then((answer) => settle({ status: READY, text: answer.text, source: answer.source }))
        .catch((error) => settle({ status: FAILED, error: error.message }));
    },
    [userId, asOf, language, goal],
  );

  const waiting = exchanges.some((exchange) => exchange.status === LOADING);
  return { exchanges, ask, waiting };
}
