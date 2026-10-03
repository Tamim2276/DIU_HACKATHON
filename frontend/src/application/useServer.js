import { useCallback, useEffect, useState } from "react";

import { api, apiUrl } from "../infrastructure/apiClient.js";

const RETRY_EVERY_MS = 3000;
// A free host puts the API to sleep when nobody visits. Waking it takes about a minute,
// so the app keeps trying for longer than that before it calls it a failure.
const GIVE_UP_AFTER_MS = 150000;

export const CONNECTING = "connecting";
export const READY = "ready";
export const FAILED = "failed";

// Reaches the API when the app opens and loads what every screen needs: the list of users
// and the days a forecast can be asked for.
export function useServer() {
  const [state, setState] = useState({ status: CONNECTING, meta: null, users: [], waitedSeconds: 0, error: null });
  const [run, setRun] = useState(0);

  useEffect(() => {
    let stopped = false;
    let timer;
    const started = Date.now();
    setState((before) => ({ ...before, status: CONNECTING, waitedSeconds: 0, error: null }));

    async function attempt() {
      try {
        const [meta, users] = await Promise.all([api.meta(), api.users()]);
        if (!stopped) setState({ status: READY, meta, users, waitedSeconds: 0, error: null });
      } catch (error) {
        if (stopped) return;
        const waited = Date.now() - started;
        if (waited >= GIVE_UP_AFTER_MS) {
          setState((before) => ({ ...before, status: FAILED, error: error.message }));
        } else {
          setState((before) => ({ ...before, waitedSeconds: Math.round(waited / 1000), error: error.message }));
          timer = setTimeout(attempt, RETRY_EVERY_MS);
        }
      }
    }

    attempt();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [run]);

  const retry = useCallback(() => setRun((count) => count + 1), []);
  return { ...state, address: apiUrl, retry };
}
