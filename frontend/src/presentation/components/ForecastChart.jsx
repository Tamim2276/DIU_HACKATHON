import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { BANGLA } from "../../domain/format.js";
import { chartRows, roundMarks, shortTaka } from "../../domain/forecastSeries.js";
import { useText } from "../language.jsx";

// What the reader sees when pointing at a day.
function DayDetails({ active, payload, today }) {
  const { t, f } = useText();
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  const isToday = row.date === today;

  return (
    <div className="chart-tip">
      <p className="chart-tip-day">{isToday ? t.chart.today(f.shortDay(row.date)) : f.weekDay(row.date)}</p>
      <dl>
        <div>
          <dt>{isToday ? t.chart.balance : t.chart.expect}</dt>
          <dd>{f.taka(row.likely)}</dd>
        </div>
        {!isToday && (
          <div>
            <dt>{t.chart.range}</dt>
            <dd>{t.chart.to(f.taka(row.wide[0]), f.taka(row.wide[1]))}</dd>
          </div>
        )}
        {!isToday && row.before !== undefined && (
          <div>
            <dt>{t.chart.without}</dt>
            <dd>{f.taka(row.before)}</dd>
          </div>
        )}
        {!isToday && row.shownActual !== undefined && (
          <div>
            <dt>{t.chart.actual}</dt>
            <dd>{f.taka(row.shownActual)}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}

// The balance for the next 30 days: the line we expect, the range around it, and the cushion.
// `before` is the forecast without any action, drawn as a dashed line to compare with.
export default function ForecastChart({ forecast, before = null, showActual = false }) {
  const { t, f, language } = useText();
  const rows = chartRows(forecast, before).map((row) => ({ ...row, shownActual: showActual ? row.actual : undefined }));
  const weekly = rows.filter((_, index) => index % 7 === 0).map((row) => row.date);
  const { alert, cushion } = forecast;
  const highest = Math.max(cushion, ...rows.flatMap((row) => [row.wide[1], row.before ?? 0, row.shownActual ?? 0]));
  const marks = roundMarks(highest);
  // "৳5k" is short enough in English; in Bangla the whole number reads better: ৫,০০০
  const mark = language === BANGLA ? (value) => f.number(value) : shortTaka;

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 22, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--rule)" strokeDasharray="3 4" />
          <XAxis
            dataKey="date"
            ticks={weekly}
            tickFormatter={f.shortDay}
            tick={{ fill: "var(--muted)", fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: "var(--rule)" }}
            tickMargin={8}
          />
          <YAxis
            width={language === BANGLA ? 56 : 48}
            domain={[0, marks[marks.length - 1]]}
            ticks={marks}
            tickFormatter={mark}
            tick={{ fill: "var(--muted)", fontSize: 12 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            content={<DayDetails today={forecast.as_of} />}
            cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
            isAnimationActive={false}
          />

          <Area dataKey="wide" stroke="none" fill="var(--accent)" fillOpacity={0.13} isAnimationActive={false} />
          <Area dataKey="narrow" stroke="none" fill="var(--accent)" fillOpacity={0.2} isAnimationActive={false} />

          <ReferenceLine
            y={cushion}
            stroke="var(--warn)"
            strokeDasharray="6 4"
            label={{ value: t.chart.cushion(f.taka(cushion)), position: "insideTopRight", fill: "var(--warn)", fontSize: 11 }}
          />
          {alert && (
            <ReferenceLine
              x={alert.date}
              stroke="var(--warn)"
              strokeOpacity={0.7}
              label={{ value: t.chart.warning(f.shortDay(alert.date)), position: "top", fill: "var(--warn)", fontSize: 11 }}
            />
          )}

          {before && (
            <Line
              dataKey="before"
              stroke="var(--muted)"
              strokeWidth={1.6}
              strokeDasharray="5 4"
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
          )}
          <Line
            dataKey="likely"
            stroke="var(--accent)"
            strokeWidth={2.6}
            dot={false}
            activeDot={{ r: 4, fill: "var(--accent)", stroke: "var(--surface)", strokeWidth: 2 }}
            isAnimationActive={false}
          />
          {showActual && (
            <Line
              dataKey="shownActual"
              stroke="var(--ink)"
              strokeWidth={1.6}
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// The key to the chart, as words beside small samples of each line and shade.
export function ChartKey({ before = false, showActual = false }) {
  const { t } = useText();
  return (
    <ul className="chart-key">
      <li>
        <span className="key-line" />
        {t.chart.keyExpect}
      </li>
      <li>
        <span className="key-shade narrow" />
        {t.chart.keyNarrow}
      </li>
      <li>
        <span className="key-shade" />
        {t.chart.keyWide}
      </li>
      <li>
        <span className="key-line cushion" />
        {t.chart.keyCushion}
      </li>
      {before && (
        <li>
          <span className="key-line before" />
          {t.chart.keyWithout}
        </li>
      )}
      {showActual && (
        <li>
          <span className="key-line actual" />
          {t.chart.keyActual}
        </li>
      )}
    </ul>
  );
}
