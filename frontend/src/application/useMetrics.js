import { useCallback, useEffect, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// The model's test results, for the Model report screen. They do not depend on the chosen customer.
export function useMetrics() {
  const [state, setState] = useState({ status: LOADING, metrics: null, error: null });
  const [run, setRun] = useState(0);

  useEffect(() => {
    let outdated = false;
    setState({ status: LOADING, metrics: null, error: null });
    api
      .metrics()
      .then((metrics) => {
        if (!outdated) setState({ status: READY, metrics, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, metrics: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [run]);

  const reload = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, reload };
}
