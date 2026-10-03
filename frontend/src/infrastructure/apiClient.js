// Every call the web app makes to the API, in one file.
// Nothing else in the app knows an address or builds a request.

const DEFAULT_URL = "http://127.0.0.1:8000";
const TIMEOUT_MS = 15000;
const EXPLAIN_TIMEOUT_MS = 30000; // a follow-up question waits for a language model

export const apiUrl = (import.meta.env.VITE_API_URL || DEFAULT_URL).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status; // the HTTP status, or null when the server could not be reached at all
  }
}

// The API explains an error in "detail": a sentence, or a list of problems with the request.
function reasonFrom(body, status) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return detail.map((problem) => problem.msg).join("; ");
  return `The server answered with an error (${status}).`;
}

async function request(path, { method = "GET", body, timeoutMs = TIMEOUT_MS } = {}) {
  const stop = new AbortController();
  const timer = setTimeout(() => stop.abort(), timeoutMs);
  let response;
  try {
    response = await fetch(apiUrl + path, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: stop.signal,
    });
  } catch (error) {
    const reason = error.name === "AbortError" ? "The server took too long to answer." : "The server could not be reached.";
    throw new ApiError(reason, null);
  } finally {
    clearTimeout(timer);
  }

  const answer = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(reasonFrom(answer, response.status), response.status);
  return answer;
}

const user = (userId) => `/users/${encodeURIComponent(userId)}`;

export const api = {
  health: () => request("/health"),

  // The days a forecast can be asked for, and the day the app opens on.
  meta: () => request("/meta"),

  users: () => request("/users"),

  // `asOf` is the day to treat as today, as YYYY-MM-DD.
  forecast: (userId, asOf) => request(`${user(userId)}/forecast?as_of=${encodeURIComponent(asOf)}`),

  // The forecast as it would look with the chosen actions switched on. Nothing is stored.
  whatIf: (userId, asOf, actions) =>
    request(`${user(userId)}/what-if`, { method: "POST", body: { as_of: asOf, actions } }),

  // The explanation in "bn" or "en". With a question, a language model answers it from the same facts.
  explain: (userId, asOf, language, question) =>
    request(`${user(userId)}/explain`, {
      method: "POST",
      body: { as_of: asOf, language, question: question || null },
      timeoutMs: EXPLAIN_TIMEOUT_MS,
    }),

  // How the forecasting model did on months it never trained on.
  metrics: () => request("/metrics"),
};
