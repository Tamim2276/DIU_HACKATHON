import { useState } from "react";

import { addDays, isDay } from "../../domain/format.js";
import { validGoal } from "../../domain/selection.js";
import { useText } from "../language.jsx";
import DayField from "./DayField.jsx";

// The customer can put money aside for a goal. The API takes it out of the safe-to-spend amount,
// so setting a goal lowers that number, here and on every other screen.
export default function SavingsGoal({ forecast, selection, onChoose }) {
  const { t, f } = useText();
  const text = t.goal;
  const plan = forecast.savings_goal;
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(forecast.window_until);
  const [refused, setRefused] = useState(false);

  function set(event) {
    event.preventDefault();
    const goal = validGoal({ amount, date }, selection.asOf);
    setRefused(!goal);
    if (goal) onChoose({ goal });
  }

  return (
    <section className="card" aria-labelledby="goal-title">
      <h2 id="goal-title" className="card-title">
        {text.title}
      </h2>

      {plan ? (
        <>
          <p className="goal-plan">{text.plan(f.taka(plan.amount), f.weekDay(plan.date), f.taka(plan.per_day))}</p>
          <p className="card-text">
            {forecast.safe_to_spend < 1 && plan.safe_to_spend_before >= 1
              ? text.noRoom
              : text.effect(f.taka(plan.safe_to_spend_before), f.taka(forecast.safe_to_spend))}
          </p>
          <button type="button" className="text-button" onClick={() => onChoose({ goal: null })}>
            {text.remove}
          </button>
        </>
      ) : (
        <>
          <p className="card-text">{text.intro}</p>
          <form className="goal-form" onSubmit={set}>
            <label className="field">
              <span>{text.amount}</span>
              <input
                type="number"
                inputMode="numeric"
                min="1"
                step="1"
                value={amount}
                placeholder="2000"
                onChange={(event) => setAmount(event.target.value)}
              />
            </label>
            <div className="field">
              <label htmlFor="goal-day">{text.by}</label>
              <DayField
                id="goal-day"
                value={date}
                min={addDays(selection.asOf, 1)}
                max={addDays(selection.asOf, 365)}
                onChange={(day) => isDay(day) && setDate(day)}
                rounded
              />
            </div>
            <button type="submit" className="button">
              {text.set}
            </button>
          </form>
          {refused && (
            <p className="footnote warn-text" role="alert">
              {text.invalid}
            </p>
          )}
        </>
      )}
    </section>
  );
}
