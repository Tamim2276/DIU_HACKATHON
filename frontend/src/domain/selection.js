// Which customer the app is showing, which day it treats as today, and the customer's savings goal.
import { daysBetween, isDay } from "./format.js";

const LONGEST_GOAL_DAYS = 365; // the API refuses a goal further away than a year

// The customer the app opens on: a student with a shortfall ahead that one action removes.
const FIRST_CUSTOMER = "U0121";

// A savings goal the API will accept for this day: an amount above zero and a later date within a year.
// Otherwise none.
export function validGoal(goal, asOf) {
  const amount = Number(goal?.amount);
  const date = goal?.date ?? "";
  const usable = Number.isFinite(amount) && amount > 0 && isDay(date) && date > asOf && daysBetween(asOf, date) <= LONGEST_GOAL_DAYS;
  return usable ? { amount, date } : null;
}

// A selection the API will accept. Anything missing or out of range is replaced by the default.
export function validSelection(wanted, users, meta) {
  const known = (id) => users.some((user) => user.user_id === id);
  const fallback = known(FIRST_CUSTOMER) ? FIRST_CUSTOMER : users[0].user_id;
  const day = wanted?.asOf ?? "";
  const inRange = isDay(day) && day >= meta.first_day && day <= meta.last_day;
  const asOf = inRange ? day : meta.default_day;
  return { userId: known(wanted?.userId) ? wanted.userId : fallback, asOf, goal: validGoal(wanted?.goal, asOf) };
}

export const sameGoal = (a, b) => (a?.amount ?? null) === (b?.amount ?? null) && (a?.date ?? null) === (b?.date ?? null);

// The customers grouped by kind, in the order the API lists them.
export function byPersona(users) {
  const groups = [];
  for (const user of users) {
    let group = groups.find((candidate) => candidate.persona === user.persona);
    if (!group) {
      group = { persona: user.persona, first: user, users: [] };
      groups.push(group);
    }
    group.users.push(user);
  }
  return groups;
}
