import { useCallback, useEffect, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// Loads the forecast for the chosen customer and day, with their savings goal if they set one.
// While a new one loads, the previous one stays available so the screen does not go empty.
export function useForecast(userId, asOf, goal) {
  const [state, setState] = useState({ status: LOADING, forecast: null, error: null });
  const [run, setRun] = useState(0);
  const amount = goal?.amount ?? null;
  const date = goal?.date ?? null;

  useEffect(() => {
    let outdated = false; // set when the customer, day or goal changes before the answer arrives
    setState((before) => ({ ...before, status: LOADING, error: null }));
    api
      .forecast(userId, asOf, amount === null ? null : { amount, date })
      .then((forecast) => {
        if (!outdated) setState({ status: READY, forecast, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, forecast: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [userId, asOf, amount, date, run]);

  const reload = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, reload };
}
