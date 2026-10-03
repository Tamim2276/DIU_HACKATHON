import { addDays, isDay } from "../../domain/format.js";
import { byPersona } from "../../domain/selection.js";
import { useText } from "../language.jsx";
import DayField from "./DayField.jsx";
import Icon from "./Icon.jsx";

// The demo's controls: which customer is shown, and which day counts as today.
// In a real wallet there is no such choice: it is the signed-in customer, today.
export default function UserSwitcher({ users, meta, selection, onChoose }) {
  const { t } = useText();
  const text = t.switcher;
  const groups = byPersona(users);
  const current = groups.find((group) => group.users.some((user) => user.user_id === selection.userId));
  const { asOf } = selection;

  function chooseDay(day) {
    if (isDay(day) && day >= meta.first_day && day <= meta.last_day) onChoose({ asOf: day });
  }

  return (
    <section className="switcher" aria-labelledby="switcher-title">
      <div className="switcher-head">
        <h2 id="switcher-title" className="label">
          {text.title}
        </h2>
        <p className="hint">{text.hint}</p>
      </div>

      <div className="chips" role="group" aria-label={text.kind}>
        {groups.map((group) => (
          <button
            key={group.persona}
            type="button"
            className="chip"
            aria-pressed={group === current}
            onClick={() => group !== current && onChoose({ userId: group.first.user_id })}
          >
            {t.personas[group.persona] ?? group.first.persona_label}
          </button>
        ))}
      </div>

      <div className="fields">
        <label className="field">
          <span>{text.customer}</span>
          <select value={selection.userId} onChange={(event) => onChoose({ userId: event.target.value })}>
            {current.users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.user_id}
              </option>
            ))}
          </select>
        </label>

        <div className="field">
          <label htmlFor="today">{text.today}</label>
          <div className="stepper">
            <button
              type="button"
              aria-label={text.earlier}
              disabled={asOf <= meta.first_day}
              onClick={() => chooseDay(addDays(asOf, -1))}
            >
              <Icon name="left" size={18} />
            </button>
            <DayField id="today" value={asOf} min={meta.first_day} max={meta.last_day} onChange={chooseDay} />
            <button
              type="button"
              aria-label={text.later}
              disabled={asOf >= meta.last_day}
              onClick={() => chooseDay(addDays(asOf, 1))}
            >
              <Icon name="right" size={18} />
            </button>
          </div>
        </div>

        {asOf !== meta.default_day && (
          <button type="button" className="text-button" onClick={() => chooseDay(meta.default_day)}>
            {text.back}
          </button>
        )}
      </div>
    </section>
  );
}
