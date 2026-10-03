import { useText } from "../language.jsx";

// Says whose figures a screen shows, and offers the way back to change that.
export default function ContextBar({ users, selection, goTo }) {
  const { t, f } = useText();
  const user = users.find((candidate) => candidate.user_id === selection.userId);

  return (
    <div className="context">
      <p>
        <strong>{t.personas[user.persona] ?? user.persona_label}</strong> {user.user_id}
        <span className="context-day">{t.context.today(f.fullDay(selection.asOf))}</span>
      </p>
      <button type="button" className="text-button" onClick={() => goTo("home")}>
        {t.context.change}
      </button>
    </div>
  );
}
