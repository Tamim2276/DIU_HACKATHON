import { useCallback, useEffect, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// Loads the forecast for the chosen customer and day.
// While a new one loads, the previous one stays available so the screen does not go empty.
export function useForecast(userId, asOf) {
  const [state, setState] = useState({ status: LOADING, forecast: null, error: null });
  const [run, setRun] = useState(0);

  useEffect(() => {
    let outdated = false; // set when the customer or day changes before the answer arrives
    setState((before) => ({ ...before, status: LOADING, error: null }));
    api
      .forecast(userId, asOf)
      .then((forecast) => {
        if (!outdated) setState({ status: READY, forecast, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, forecast: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [userId, asOf, run]);

  const reload = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, reload };
}
