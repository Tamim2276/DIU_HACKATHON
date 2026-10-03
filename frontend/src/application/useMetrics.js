import { useCallback, useEffect, useState } from "react";

import { api } from "../infrastructure/apiClient.js";

export const LOADING = "loading";
export const READY = "ready";
export const FAILED = "failed";

// The model's test results and the impact test's, for the Model report screen.
// They do not depend on the chosen customer. The impact results are an extra:
// when they are missing, `impact` is null and the rest of the screen still shows.
export function useMetrics() {
  const [state, setState] = useState({ status: LOADING, metrics: null, impact: null, error: null });
  const [run, setRun] = useState(0);

  useEffect(() => {
    let outdated = false;
    setState({ status: LOADING, metrics: null, impact: null, error: null });
    Promise.all([api.metrics(), api.impact().catch(() => null)])
      .then(([metrics, impact]) => {
        if (!outdated) setState({ status: READY, metrics, impact, error: null });
      })
      .catch((error) => {
        if (!outdated) setState({ status: FAILED, metrics: null, impact: null, error: error.message });
      });
    return () => {
      outdated = true;
    };
  }, [run]);

  const reload = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, reload };
}
