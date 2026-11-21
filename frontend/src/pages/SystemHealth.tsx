import { useQuery } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import QueryError from "../components/QueryError";
import { api } from "../lib/api";

const labels = pl as Record<string, string>;
const REFRESH_MS = 5000;

function formatSchedule(seconds: number | null) {
  return seconds === null ? pl["system.once"] : pl["system.schedule"].replace("{minutes}", String(Math.round(seconds / 60)));
}

export default function SystemHealth() {
  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ["system-health"],
    queryFn: api.systemHealth,
    refetchInterval: REFRESH_MS,
  });

  return (
    <>
      <h1 className="page__title">{pl["system.title"]}</h1>
      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
      {data && (
        <div className="split">
          <section>
            <h2 className="section__title">{pl["system.queues"]}</h2>
            <ul className="modules">
              {Object.entries(data.queues).map(([name, length]) => (
                <li key={name} className="modules__item" style={{ borderColor: length > 0 ? "#b06f12" : "#1d6e7a" }}>
                  <span className="modules__count">{length}</span>
                  <span className="modules__name">{labels[`system.queue.${name}`] ?? name}</span>
                </li>
              ))}
            </ul>

            <h2 className="section__title section__title--spaced">{pl["system.proxies"]}</h2>
            {data.proxies.length === 0 ? (
              <p className="empty">{pl["system.proxies.none"]}</p>
            ) : (
              <ul className="facts">
                {data.proxies.map((p) => (
                  <li key={p.url}>
                    <strong>{p.url}</strong>
                    <span className={`facts__meta${p.circuit_open ? " facts__bad" : ""}`}>
                      {p.circuit_open ? pl["system.proxy.open"] : pl["system.proxy.ok"]}, {p.failures} {pl["system.proxy.failures"]}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 className="section__title">{pl["system.collectors"]}</h2>
            <ul className="facts">
              {data.collectors.map((c) => (
                <li key={c.name}>
                  <strong>{c.name}</strong>
                  <span className="facts__meta">
                    {c.enabled ? formatSchedule(c.schedule_seconds) : pl["system.disabled"]}, {c.documents} {pl["system.documents"]}
                    <br />
                    {pl["system.lastCrawl"]}: {c.last_crawl_at ? new Date(c.last_crawl_at + "Z").toLocaleString("pl-PL") : pl["system.never"]}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </>
  );
}
