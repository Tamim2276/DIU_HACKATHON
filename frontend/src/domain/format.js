// How numbers and dates are written on screen, in English or in Bangla. Plain functions: no React, no API.
// A day is always a "YYYY-MM-DD" string, exactly as the API sends it.

export const ENGLISH = "en";
export const BANGLA = "bn";

// Rounds a half to the even neighbour, as the API does when it writes its explanation.
// A figure on a screen then never differs by one taka from the same figure in a sentence.
export function whole(value) {
  const floor = Math.floor(value);
  if (value - floor === 0.5) return floor % 2 === 0 ? floor : floor + 1;
  return Math.round(value);
}

const asDate = (day) => new Date(`${day}T00:00:00Z`);
const DAY_MS = 24 * 60 * 60 * 1000;

export const daysBetween = (from, to) => Math.round((asDate(to) - asDate(from)) / DAY_MS);

export const addDays = (day, count) => new Date(asDate(day).getTime() + count * DAY_MS).toISOString().slice(0, 10);

export const isDay = (text) => /^\d{4}-\d{2}-\d{2}$/.test(text) && !Number.isNaN(asDate(text).getTime());

// Written out here, not left to the browser, so every device shows a date the same way.
const WORDS = {
  [ENGLISH]: {
    weekdays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  },
  [BANGLA]: {
    weekdays: ["রবি", "সোম", "মঙ্গল", "বুধ", "বৃহস্পতি", "শুক্র", "শনি"],
    months: ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"],
  },
};

const BANGLA_DIGITS = "০১২৩৪৫৬৭৮৯";
const grouped = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

// Every way of writing a figure, for one language.
function makeFormatter(language) {
  const { weekdays, months } = WORDS[language];
  // In Bangla every digit is written as a Bangla digit: 1,771 becomes ১,৭৭১.
  const digits = (text) =>
    language === BANGLA ? String(text).replace(/\d/g, (digit) => BANGLA_DIGITS[digit]) : String(text);

  const number = (value) => digits(grouped.format(Math.abs(whole(value)))); // the sign is left to the caller
  const shortDay = (day) => `${digits(asDate(day).getUTCDate())} ${months[asDate(day).getUTCMonth()]}`;
  const weekDay = (day) => `${weekdays[asDate(day).getUTCDay()]}, ${shortDay(day)}`;

  return {
    digits,
    number, // 1771.4 -> "1,771"
    taka: (value) => `${whole(value) < 0 ? "−" : ""}৳${number(value)}`, // "৳1,771", "−৳5,934"
    percent: (chance) => `${digits(whole(chance * 100))}%`, // 0.4454 -> "45%"
    decimal: (value, places = 2) => digits(value.toFixed(places)), // 3.367 -> "3.37"
    shortDay, // "23 Aug"
    weekDay, // "Sun, 23 Aug"
    weekdayOnly: (day) => weekdays[asDate(day).getUTCDay()],
    year: (day) => digits(asDate(day).getUTCFullYear()),
    fullDay: (day) => `${weekDay(day)} ${digits(asDate(day).getUTCFullYear())}`, // "Wed, 12 Aug 2026"
  };
}

const FORMATTERS = { [ENGLISH]: makeFormatter(ENGLISH), [BANGLA]: makeFormatter(BANGLA) };

export const formatter = (language) => FORMATTERS[language] ?? FORMATTERS[ENGLISH];
