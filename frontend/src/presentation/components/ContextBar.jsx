import { fullDay } from "../../domain/format.js";
import { personaName } from "../../domain/labels.js";

// Says whose figures a screen shows, and offers the way back to change that.
export default function ContextBar({ users, selection, goTo }) {
  const user = users.find((candidate) => candidate.user_id === selection.userId);

  return (
    <div className="context">
      <p>
        <strong>{personaName(user)}</strong> {user.user_id}
        <span className="context-day">Today is {fullDay(selection.asOf)}</span>
      </p>
      <button type="button" className="text-button" onClick={() => goTo("home")}>
        Change
      </button>
    </div>
  );
}
