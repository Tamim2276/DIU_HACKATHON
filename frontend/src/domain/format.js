// How numbers and dates are written on screen. Plain functions: no React, no API.
// A day is always a "YYYY-MM-DD" string, exactly as the API sends it.

// Rounds a half to the even neighbour, as the API does when it writes its explanation.
// A figure on a screen then never differs by one taka from the same figure in a sentence.
export function whole(value) {
  const floor = Math.floor(value);
  if (value - floor === 0.5) return floor % 2 === 0 ? floor : floor + 1;
  return Math.round(value);
}

const grouped = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

// 1771.4 -> "1,771" (the sign is left to the caller)
export const number = (value) => grouped.format(Math.abs(whole(value)));

// 1771.4 -> "৳1,771", and -5934.3 -> "−৳5,934"
export const taka = (value) => `${whole(value) < 0 ? "−" : ""}৳${number(value)}`;

// 0.4454 -> "45%"
export const percent = (chance) => `${whole(chance * 100)}%`;

const asDate = (day) => new Date(`${day}T00:00:00Z`);

// Written out here, not left to the browser, so every device shows a date the same way.
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// "23 Aug"
export function shortDay(day) {
  const date = asDate(day);
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;
}

// "Sun, 23 Aug"
export const weekDay = (day) => `${WEEKDAYS[asDate(day).getUTCDay()]}, ${shortDay(day)}`;

// "Wed, 12 Aug 2026"
export const fullDay = (day) => `${weekDay(day)} ${asDate(day).getUTCFullYear()}`;

const DAY_MS = 24 * 60 * 60 * 1000;

export const daysBetween = (from, to) => Math.round((asDate(to) - asDate(from)) / DAY_MS);

export const addDays = (day, count) => new Date(asDate(day).getTime() + count * DAY_MS).toISOString().slice(0, 10);

export const isDay = (text) => /^\d{4}-\d{2}-\d{2}$/.test(text) && !Number.isNaN(asDate(text).getTime());

// 0 -> "today", 1 -> "tomorrow", 11 -> "in 11 days"
export function fromNow(days) {
  if (days <= 0) return "today";
  return days === 1 ? "tomorrow" : `in ${days} days`;
}

// 1 -> "1 day", 27 -> "27 days"
export const dayCount = (days) => (days === 1 ? "1 day" : `${days} days`);
