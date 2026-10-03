// The forecast in the shape a chart draws: one row per day, starting with today.

// `before` is the forecast without any action, when the chart compares the two.
export function chartRows(forecast, before = null) {
  const { balance } = forecast;
  const today = {
    date: forecast.as_of,
    likely: balance,
    wide: [balance, balance],
    narrow: [balance, balance],
    actual: balance,
    before: before ? balance : undefined,
  };
  const days = forecast.points.map((point, index) => ({
    date: point.date,
    likely: point.p50, // the most likely balance
    wide: [point.p10, point.p90], // the balance is in here about 8 times in 10
    narrow: [point.p25, point.p75], // and in here about 5 times in 10
    actual: point.actual ?? undefined, // what really happened, when the data has it
    before: before ? before.points[index].p50 : undefined,
  }));
  return [today, ...days];
}

// The day on which a level of the forecast is lowest. `level` is "p50" (most likely) or "p25" (cautious).
export function lowestPoint(points, level = "p50") {
  return points.reduce((lowest, point) => (point[level] < lowest[level] ? point : lowest), points[0]);
}

// Round marks for the side of a chart, from zero to just above the highest value: 0, 5k, 10k, 15k.
export function roundMarks(highest, wanted = 4) {
  const rough = Math.max(highest, 1) / wanted;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((factor) => factor * power).find((candidate) => candidate >= rough);
  const count = Math.ceil(highest / step);
  return Array.from({ length: count + 1 }, (_, index) => index * step);
}

// 2400 -> "৳2.4k", 16000 -> "৳16k", 800 -> "৳800": short enough for the side of a chart
export function shortTaka(value) {
  if (Math.abs(value) < 1000) return `৳${Math.round(value)}`;
  const thousands = value / 1000;
  return `৳${Number.isInteger(thousands) ? thousands : thousands.toFixed(1)}k`;
}
