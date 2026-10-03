import { FAILED } from "../../application/useServer.js";

// Shown in place of a screen while the API has not answered: never a blank page.
export default function ConnectionNotice({ server }) {
  if (server.status === FAILED) {
    return (
      <section className="card notice" role="alert">
        <h1>The server did not answer</h1>
        <p>
          Nothing answered at <code>{server.address}</code>. Check that the API is running there, then try again.
        </p>
        <p className="reason">{server.error}</p>
        <button type="button" className="button" onClick={server.retry}>
          Try again
        </button>
      </section>
    );
  }

  const noAnswerYet = server.error !== null; // at least one try has failed
  return (
    <section className="card notice" aria-busy="true">
      <span className="spinner" aria-hidden="true" />
      <h1>{noAnswerYet ? "Starting the server" : "Connecting"}</h1>
      {noAnswerYet && (
        <>
          <p>
            No answer yet from <code>{server.address}</code>. On a free host the server sleeps when nobody visits and
            needs about a minute to wake up.
          </p>
          <p className="reason">
            Trying again every few seconds.
            {server.waitedSeconds >= 3 && ` Waited ${server.waitedSeconds} seconds so far.`}
          </p>
        </>
      )}
    </section>
  );
}
