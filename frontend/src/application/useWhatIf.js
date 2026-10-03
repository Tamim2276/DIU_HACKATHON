import { useEffect, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const IDLE = "idle"; // no action is switched on, so there is nothing to ask
export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// Asks the API how the forecast would look with the chosen actions switched on.
// While a new answer loads, the previous one stays available so the chart does not blink.
export function useWhatIf(userId, asOf, actionIds, goal) {
  const [state, setState] = useState({ status: IDLE, result: null, error: null });
  const chosen = actionIds.join(",");
  const amount = goal?.amount ?? null;
  const date = goal?.date ?? null;

  useEffect(() => {
    if (!chosen) {
      setState({ status: IDLE, result: null, error: null });
      return undefined;
    }
    let outdated = false;
    setState((before) => ({ ...before, status: LOADING, error: null }));
    api
      .whatIf(userId, asOf, chosen.split(","), amount === null ? null : { amount, date })
      .then((result) => {
        if (!outdated) setState({ status: READY, result, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, result: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [userId, asOf, chosen, amount, date]);

  return state;
}
