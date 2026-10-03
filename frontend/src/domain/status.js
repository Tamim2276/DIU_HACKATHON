// Where a customer stands, read off one forecast. The API has already decided whether
// there is a warning; this only names the four situations a screen can show.

export const SHORTFALL = "shortfall"; // a warning, and the balance is still above the cushion today
export const LOW_NOW = "low_now"; // a warning, and the balance is already under the cushion
export const RECOVERING = "recovering"; // under the cushion today, but no warning: it is expected to rise
export const CLEAR = "clear"; // no warning, and above the cushion

export function statusOf(forecast) {
  if (forecast.alert) return forecast.under_cushion_now ? LOW_NOW : SHORTFALL;
  return forecast.under_cushion_now ? RECOVERING : CLEAR;
}
