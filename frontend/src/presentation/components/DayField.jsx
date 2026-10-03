import { useText } from "../language.jsx";
import Icon from "./Icon.jsx";

// A day the reader can change. The day is written out by the app ("Wed, 12 Aug 2026"), because a
// browser's own date box shows 08/12 or 12/08 depending on the device. The real date box lies on
// top, unseen: it takes the click, opens the calendar and works with the keyboard.
export default function DayField({ id, value, min, max, onChange, rounded = false }) {
  const { f } = useText();

  function openCalendar(event) {
    try {
      event.currentTarget.showPicker?.();
    } catch {
      // the browser opens its calendar in its own way
    }
  }

  return (
    <span className={rounded ? "day rounded" : "day"}>
      <Icon name="calendar" size={16} />
      <span aria-hidden="true">
        <span className="wide-only">{f.weekdayOnly(value)}, </span>
        {f.shortDay(value)} {f.year(value)}
      </span>
      <input
        id={id}
        type="date"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(event.target.value)}
        onClick={openCalendar}
      />
    </span>
  );
}
