import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import pl from "../i18n/pl.json";
import ModuleTag from "../components/ModuleTag";
import Ruler from "../components/Ruler";
import { api } from "../lib/api";
import { HIGH_RISK, MODULES, formatDate } from "../lib/modules";

function headline(total: number, high: number): string {
  if (total === 0) return "Nic nie czeka na przegląd.";
  const few = total % 10 >= 2 && total % 10 <= 4 && (total % 100 < 12 || total % 100 > 14);
  const form = total === 1 ? "nowy finding czeka" : few ? "nowe findingi czekają" : "nowych findingów czeka";
  const base = `${total} ${form} na przegląd`;
  return high > 0 ? `${base}, ${high} ${pl["overview.highRisk"]}.` : `${base}.`;
}

export default function Overview() {
  const queue = useQuery({ queryKey: ["findings", "queue"], queryFn: () => api.listFindings({ status: "new", limit: 500 }) });
  const trend = useQuery({ queryKey: ["trend"], queryFn: api.findingsTrend });
  const counters = useQuery({ queryKey: ["counters"], queryFn: api.findingsCounters });

  const waiting = queue.data ?? [];
  const highWaiting = waiting.filter((f) => f.score >= HIGH_RISK).length;

  const byDay = new Map<string, Record<string, number | string>>();
  (trend.data ?? []).forEach((row) => {
    const day = row.day.slice(5, 10).split("-").reverse().join(".");
    const entry = byDay.get(day) ?? { day };
    entry[row.module] = row.count;
    byDay.set(day, entry);
  });
  const chartData = [...byDay.values()];

  return (
    <>
      <h1 className="page__title">{queue.isSuccess ? headline(waiting.length, highWaiting) : pl["overview.title"]}</h1>
      {queue.isError && <p className="notice">{pl["common.error"]}</p>}

      <div className="split">
        <section>
          <div className="section__head">
            <h2 className="section__title">{pl["overview.queue"]}</h2>
            <Link to="/findings" className="link">
              {pl["overview.queueAll"]}
            </Link>
          </div>
          {queue.isSuccess && waiting.length === 0 ? (
            <p className="empty">
              {pl["overview.queueEmpty"]} <Link to="/scan">{pl["nav.scan"]}</Link>
            </p>
          ) : (
            <ul className="rows">
              {waiting.slice(0, 8).map((f) => (
                <li key={f.id}>
                  <Link to={`/findings/${f.id}`} className="row row--finding">
                    <ModuleTag module={f.module} />
                    <Ruler score={f.score} module={f.module} />
                    <span className={`score${f.score >= HIGH_RISK ? " score--high" : ""}`}>{f.score.toFixed(2)}</span>
                    <span className="row__meta">{formatDate(f.created_at)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h2 className="section__title">{pl["overview.trend"]}</h2>
          {chartData.length === 0 ? (
            <p className="empty">{pl["overview.trendEmpty"]}</p>
          ) : (
            <div className="chart">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData}>
                  <CartesianGrid vertical={false} stroke="#c3ced2" />
                  <XAxis dataKey="day" tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={28} />
                  <Tooltip cursor={{ fill: "rgba(18,37,45,0.06)" }} />
                  {MODULES.map((m) => (
                    <Bar key={m.id} dataKey={m.id} name={m.short} stackId="d" fill={m.color} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <h2 className="section__title section__title--spaced">{pl["overview.modules"]}</h2>
          <ul className="modules">
            {MODULES.map((m) => (
              <li key={m.id} className="modules__item" style={{ borderColor: m.color }}>
                <span className="modules__count">{counters.data?.by_module[m.id] ?? 0}</span>
                <span className="modules__name">{m.name}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
