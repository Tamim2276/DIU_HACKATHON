import { FAILED } from "../../application/useServer.js";
import { useText } from "../language.jsx";

// A sentence with the server's address inside it, set in its own typeface.
function WithAddress({ parts }) {
  const [before, address, after] = parts;
  return (
    <p>
      {before}
      <code>{address}</code>
      {after}
    </p>
  );
}

// Shown in place of a screen while the API has not answered: never a blank page.
export default function ConnectionNotice({ server }) {
  const { t, f } = useText();
  const text = t.connection;

  if (server.status === FAILED) {
    return (
      <section className="card notice" role="alert">
        <h1>{text.failed}</h1>
        <WithAddress parts={text.failedText(server.address)} />
        <p className="reason">{server.error}</p>
        <button type="button" className="button" onClick={server.retry}>
          {text.tryAgain}
        </button>
      </section>
    );
  }

  const noAnswerYet = server.error !== null; // at least one try has failed
  return (
    <section className="card notice" aria-busy="true">
      <span className="spinner" aria-hidden="true" />
      <h1>{noAnswerYet ? text.starting : text.connecting}</h1>
      {noAnswerYet && (
        <>
          <WithAddress parts={text.noAnswer(server.address)} />
          <p className="reason">
            {text.trying}
            {server.waitedSeconds >= 3 && text.waited(f.number(server.waitedSeconds))}
          </p>
        </>
      )}
    </section>
  );
}
