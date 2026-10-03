import { addDays, isDay, shortDay, weekDay } from "../../domain/format.js";
import { personaName } from "../../domain/labels.js";
import { byPersona } from "../../domain/selection.js";
import Icon from "./Icon.jsx";

// The demo's controls: which customer is shown, and which day counts as today.
// In a real wallet there is no such choice: it is the signed-in customer, today.
export default function UserSwitcher({ users, meta, selection, onChoose }) {
  const groups = byPersona(users);
  const current = groups.find((group) => group.users.some((user) => user.user_id === selection.userId));
  const { asOf } = selection;

  function chooseDay(day) {
    if (isDay(day) && day >= meta.first_day && day <= meta.last_day) onChoose({ asOf: day });
  }

  function openCalendar(event) {
    try {
      event.currentTarget.showPicker?.();
    } catch {
      // the browser opens its calendar in its own way
    }
  }

  return (
    <section className="switcher" aria-labelledby="switcher-title">
      <div className="switcher-head">
        <h2 id="switcher-title" className="label">
          Demo customer
        </h2>
        <p className="hint">In a real wallet this is the signed-in customer, today.</p>
      </div>

      <div className="chips" role="group" aria-label="Kind of customer">
        {groups.map((group) => (
          <button
            key={group.persona}
            type="button"
            className="chip"
            aria-pressed={group === current}
            onClick={() => group !== current && onChoose({ userId: group.first.user_id })}
          >
            {personaName(group.first)}
          </button>
        ))}
      </div>

      <div className="fields">
        <label className="field">
          <span>Customer</span>
          <select value={selection.userId} onChange={(event) => onChoose({ userId: event.target.value })}>
            {current.users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.user_id}
              </option>
            ))}
          </select>
        </label>

        <div className="field">
          <label htmlFor="today">Today is</label>
          <div className="stepper">
            <button
              type="button"
              aria-label="One day earlier"
              disabled={asOf <= meta.first_day}
              onClick={() => chooseDay(addDays(asOf, -1))}
            >
              <Icon name="left" size={18} />
            </button>
            {/* The day is written out by the app, because a browser's own date box shows 08/12 or 12/08
                depending on the device. The real date box lies on top, unseen, and opens the calendar. */}
            <span className="day">
              <Icon name="calendar" size={16} />
              <span aria-hidden="true">
                <span className="wide-only">{weekDay(asOf).split(" ")[0]} </span>
                {shortDay(asOf)} {asOf.slice(0, 4)}
              </span>
              <input
                id="today"
                type="date"
                value={asOf}
                min={meta.first_day}
                max={meta.last_day}
                onChange={(event) => chooseDay(event.target.value)}
                onClick={openCalendar}
              />
            </span>
            <button
              type="button"
              aria-label="One day later"
              disabled={asOf >= meta.last_day}
              onClick={() => chooseDay(addDays(asOf, 1))}
            >
              <Icon name="right" size={18} />
            </button>
          </div>
        </div>

        {asOf !== meta.default_day && (
          <button type="button" className="text-button" onClick={() => chooseDay(meta.default_day)}>
            Back to the demo day
          </button>
        )}
      </div>
    </section>
  );
}
