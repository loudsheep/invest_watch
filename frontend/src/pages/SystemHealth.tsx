import { useQuery } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import QueryError from "../components/QueryError";
import SoonTag from "../components/SoonTag";
import { api } from "../lib/api";

const labels = pl as Record<string, string>;
const REFRESH_MS = 5000;

function formatSchedule(seconds: number | null) {
  return seconds === null ? pl["system.once"] : pl["system.schedule"].replace("{minutes}", String(Math.round(seconds / 60)));
}

function parseUtc(value: string): Date {
  return new Date(value.endsWith("Z") ? value : `${value}Z`);
}

function clockTime(date: Date): string {
  return date.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
}

function minutesAgo(date: Date): string {
  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
  return `${minutes} min temu`;
}

export default function SystemHealth() {
  const { data, isError, isPending, refetch, dataUpdatedAt, isFetching } = useQuery({
    queryKey: ["system-health"],
    queryFn: api.systemHealth,
    refetchInterval: REFRESH_MS,
  });

  const lastCrawl = data?.collectors
    .map((c) => (c.last_crawl_at ? parseUtc(c.last_crawl_at) : null))
    .filter((d): d is Date => d !== null)
    .sort((a, b) => b.getTime() - a.getTime())[0];
  const totalDocuments = data?.collectors.reduce((sum, c) => sum + c.documents, 0) ?? 0;
  const proxyFailures = data?.proxies.reduce((sum, p) => sum + p.failures, 0) ?? 0;
  const openProxy = data?.proxies.find((p) => p.circuit_open);
  const maxQueue = Math.max(1, ...Object.values(data?.queues ?? {}));

  return (
    <>
      <div className="page__header">
        <div>
          <h1 className="page__title">{pl["system.title"]}</h1>
          <p className="page__sub">
            Kolejki, kolektory i proxy. Odświeżanie co {REFRESH_MS / 1000} s
            {dataUpdatedAt ? ` · ostatnia aktualizacja ${new Date(dataUpdatedAt).toLocaleTimeString("pl-PL")}` : ""}
          </p>
        </div>
        <button className="btn btn--secondary" onClick={() => refetch()} disabled={isFetching}>
          Odśwież
        </button>
      </div>

      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}

      {data && (
        <>
          <div className="kpi">
            <div className="kpi__stat">
              <span className="kpi__label">Kolejka scrapera</span>
              <span className="kpi__value">{data.queues.scraping ?? 0}</span>
              <span className="kpi__note">zadań</span>
            </div>
            <div className="kpi__stat">
              <span className="kpi__label">Kolejka AI</span>
              <span className="kpi__value">{data.queues.ai ?? 0}</span>
              <span className="kpi__note">{(data.queues.ai ?? 0) === 0 ? "wolna" : "zadań"}</span>
            </div>
            <div className="kpi__stat">
              <span className="kpi__label">Błędy proxy</span>
              <span className={`kpi__value${proxyFailures > 0 ? " kpi__value--high" : ""}`}>{proxyFailures}</span>
              <span className={`kpi__note${openProxy ? " text-high" : ""}`}>
                {openProxy ? `${openProxy.url}: obwód otwarty` : "wszystkie proxy działają"}
              </span>
            </div>
            <div className="kpi__stat">
              <span className="kpi__label">{pl["system.lastCrawl"]}</span>
              <span className="kpi__value">{lastCrawl ? clockTime(lastCrawl) : "-"}</span>
              <span className="kpi__note">{lastCrawl ? `${minutesAgo(lastCrawl)} · ${totalDocuments} dokumentów` : pl["system.never"]}</span>
            </div>
            <div className="kpi__stat is-soon">
              <span className="kpi__label">Opóźnienie API (p95)</span>
              <span className="kpi__value">-</span>
              <span className="kpi__note">
                <SoonTag />
              </span>
            </div>
          </div>

          <div className="row-split">
            <section className="panel row-split__main">
              <div className="panel__head">
                <h2>{pl["system.queues"]}</h2>
                <span className="muted">Redis</span>
              </div>
              <div className="panel__body queue-bars">
                {Object.entries(data.queues).map(([name, length]) => (
                  <div key={name}>
                    <p className="queue-bars__head">
                      <span className="mono">kolejka {labels[`system.queue.${name}`]?.toLowerCase() ?? name}</span>
                      <span className="muted mono">{length} zadań</span>
                    </p>
                    <span className="queue-bars__track">
                      <span
                        className={`queue-bars__fill${name === "ai" ? " queue-bars__fill--dark" : ""}`}
                        style={{ width: `${(length / maxQueue) * 100}%` }}
                      />
                    </span>
                  </div>
                ))}
                <p className="muted is-soon">
                  Historia długości kolejek z ostatnich 30 min <SoonTag />
                </p>
              </div>
            </section>

            <section className="panel row-split__side is-soon">
              <div className="panel__head">
                <h2>Usługi</h2>
                <SoonTag />
              </div>
              <p className="empty">Brak endpointu ze statusem usług (api, workery, postgres, redis, garage, searxng).</p>
            </section>
          </div>

          <div className="row-split">
            <section className="panel row-split__main">
              <div className="panel__head">
                <h2>Kolektory i ostatni crawl per źródło</h2>
              </div>
              <div className="table-head micro">
                <span className="col-collector">Kolektor</span>
                <span className="col-health">Status</span>
                <span className="col-sched">Harmonogram</span>
                <span className="col-crawl">Ostatni crawl</span>
                <span className="col-docs">Dok.</span>
                <span className="col-errors is-soon">Błędy 24h</span>
              </div>
              {data.collectors.map((c) => (
                <div className="table-row" key={c.name}>
                  <span className="col-collector cell-id">{c.name}</span>
                  <span className="col-health">
                    <span className={`dot-label${c.enabled ? " dot-label--ok" : " dot-label--off"}`}>
                      {c.enabled ? "Działa" : pl["system.disabled"]}
                    </span>
                  </span>
                  <span className="col-sched mono muted">{c.enabled ? formatSchedule(c.schedule_seconds) : "-"}</span>
                  <span className="col-crawl mono muted">
                    {c.last_crawl_at ? parseUtc(c.last_crawl_at).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : pl["system.never"]}
                  </span>
                  <span className="col-docs mono">{c.documents}</span>
                  <span className="col-errors mono muted is-soon">-</span>
                </div>
              ))}
            </section>

            <section className="panel row-split__side">
              <div className="panel__head">
                <h2>ProxyPool</h2>
              </div>
              {data.proxies.length === 0 ? (
                <p className="empty">{pl["system.proxies.none"]}</p>
              ) : (
                <>
                  <div className="table-head micro">
                    <span className="col-grow">Proxy</span>
                    <span className="col-health">Status</span>
                    <span className="col-docs">Błędy</span>
                  </div>
                  {data.proxies.map((p) => (
                    <div className="table-row" key={p.url}>
                      <span className="col-grow cell-id">{p.url}</span>
                      <span className="col-health">
                        <span className={`dot-label${p.circuit_open ? " dot-label--critical" : " dot-label--ok"}`}>
                          {p.circuit_open ? "Obwód otwarty" : "Działa"}
                        </span>
                      </span>
                      <span className="col-docs mono muted">{p.failures}</span>
                    </div>
                  ))}
                  {openProxy && <p className="proxy-note">{pl["system.proxy.open"]}: {openProxy.url}</p>}
                </>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}
