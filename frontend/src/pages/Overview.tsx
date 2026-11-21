import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import RiskCell from "../components/RiskCell";
import { api } from "../lib/api";
import { HIGH_RISK, MODULES, formatShortDate, riskBand } from "../lib/modules";

const LEVELS = [
  { band: "critical", label: "Krytyczne (od 0,9)", color: "var(--risk-critical)" },
  { band: "high", label: "Wysokie (0,8-0,9)", color: "var(--risk-high)" },
  { band: "medium", label: "Średnie (0,5-0,8)", color: "var(--risk-med)" },
  { band: "low", label: "Niskie (poniżej 0,5)", color: "var(--risk-low)" },
] as const;

function todayLabel(): string {
  const text = new Date().toLocaleDateString("pl-PL", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export default function Overview() {
  const queue = useQuery({ queryKey: ["findings", "queue"], queryFn: () => api.listFindings({ status: "new", limit: 500 }) });
  const trend = useQuery({ queryKey: ["trend"], queryFn: api.findingsTrend });
  const counters = useQuery({ queryKey: ["counters"], queryFn: api.findingsCounters });

  const waiting = queue.data ?? [];
  const highWaiting = waiting.filter((f) => f.score >= HIGH_RISK).length;
  const levelCounts = LEVELS.map((level) => ({
    ...level,
    count: waiting.filter((f) => riskBand(f.score) === level.band).length,
  }));
  const maxLevel = Math.max(1, ...levelCounts.map((l) => l.count));

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
      <div className="page__header">
        <div>
          <h1 className="page__title">{pl["overview.title"]}</h1>
          <p className="page__sub">{todayLabel()}</p>
        </div>
        <Link to="/scan" className="btn btn--primary">
          {pl["nav.scan"]}
        </Link>
      </div>

      <div className="kpi">
        <div className="kpi__stat">
          <span className="kpi__label">{pl["overview.queue"]}</span>
          <span className="kpi__value">{waiting.length}</span>
          <span className="kpi__note">&nbsp;</span>
        </div>
        <div className="kpi__stat">
          <span className="kpi__label">Wysokie ryzyko (od 0,8)</span>
          <span className="kpi__value kpi__value--critical">{highWaiting}</span>
          <span className="kpi__note">&nbsp;</span>
        </div>
        {MODULES.map((m) => (
          <div className="kpi__stat" key={m.id}>
            <ModuleBadge module={m.id} />
            <span className="kpi__value">{counters.data?.by_module[m.id] ?? 0}</span>
            <span className="kpi__note">{m.name}</span>
          </div>
        ))}
      </div>

      <div className="row-split">
        <section className="panel row-split__main">
          <div className="panel__head">
            <h2>{pl["overview.queue.title"]}</h2>
            <Link to="/findings" className="panel__aside">
              {pl["overview.queueAll"]} →
            </Link>
          </div>
          <div className="table-head micro">
            <span className="col-mod">Mod</span>
            <span className="col-grow">Treść</span>
            <span className="col-entity">Podmiot</span>
            <span className="col-risk">Ryzyko</span>
            <span className="col-date">Data</span>
          </div>
          {queue.isPending ? (
            <Loading />
          ) : queue.isError ? (
            <QueryError onRetry={() => queue.refetch()} />
          ) : waiting.length === 0 ? (
            <p className="empty">
              {pl["overview.queueEmpty"]} <Link to="/scan">{pl["nav.scan"]}</Link>
            </p>
          ) : (
            waiting.slice(0, 8).map((f) => (
              <Link key={f.id} to={`/findings/${f.id}`} className="table-row">
                <span className="col-mod">
                  <ModuleBadge module={f.module} />
                </span>
                <span className="col-grow">
                  <p className="cell-title">{f.title ?? `Finding #${f.id}`}</p>
                  <p className="cell-sub">{f.domain ?? "-"}</p>
                </span>
                <span className="col-entity">{f.entity_name ?? "-"}</span>
                <span className="col-risk">
                  <RiskCell score={f.score} />
                </span>
                <span className="col-date">{formatShortDate(f.created_at)}</span>
              </Link>
            ))
          )}
        </section>

        <div className="row-split__side">
          <section className="panel">
            <div className="panel__head">
              <h2>{pl["overview.trend"]}</h2>
              <span className="panel__aside">14 dni</span>
            </div>
            <div className="panel__body">
              {trend.isPending ? (
                <Loading />
              ) : trend.isError ? (
                <QueryError onRetry={() => trend.refetch()} />
              ) : chartData.length === 0 ? (
                <p className="muted">{pl["overview.trendEmpty"]}</p>
              ) : (
                <>
                  <div className="legend">
                    {MODULES.map((m) => (
                      <ModuleBadge key={m.id} module={m.id} />
                    ))}
                  </div>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={chartData}>
                      <CartesianGrid vertical={false} stroke="#d8dce4" />
                      <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={20} tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                      <Tooltip />
                      {MODULES.map((m) => (
                        <Line
                          key={m.id}
                          type="linear"
                          dataKey={m.id}
                          name={m.short}
                          stroke={m.color}
                          strokeWidth={1.5}
                          strokeDasharray={m.id === "m3" ? "4 3" : undefined}
                          dot={false}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <h2>Poziom ryzyka</h2>
            </div>
            <div className="panel__body levels">
              {levelCounts.map((level) => (
                <div className="levels__row" key={level.band}>
                  <span className="levels__label">{level.label}</span>
                  <span className="levels__track">
                    <span className="levels__bar" style={{ width: `${(level.count / maxLevel) * 100}%`, background: level.color, display: "block" }} />
                  </span>
                  <span className="levels__count">{level.count}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
