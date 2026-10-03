// Which customer the app is showing, and which day it treats as today.
import { isDay } from "./format.js";

// The customer the app opens on: a student with a shortfall ahead that one action removes.
const FIRST_CUSTOMER = "U0121";

// A selection the API will accept. Anything missing or out of range is replaced by the default.
export function validSelection(wanted, users, meta) {
  const known = (id) => users.some((user) => user.user_id === id);
  const fallback = known(FIRST_CUSTOMER) ? FIRST_CUSTOMER : users[0].user_id;
  const asOf = wanted?.asOf ?? "";
  const inRange = isDay(asOf) && asOf >= meta.first_day && asOf <= meta.last_day;
  return { userId: known(wanted?.userId) ? wanted.userId : fallback, asOf: inRange ? asOf : meta.default_day };
}

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
