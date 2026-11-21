import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import { api } from "../lib/api";
import { socket } from "../lib/socket";

interface StageEvent {
  scan_id: string;
  stage: string;
  status: string;
  message?: string | null;
  data?: {
    modules?: Record<string, { relevance: number; score: number | null; finding_id: number | null }>;
    finding_ids?: number[];
  };
}

type ModuleResults = NonNullable<StageEvent["data"]>["modules"];

interface TimedEvent extends StageEvent {
  at: number;
}

const STAGES = ["fetch", "preprocess", "embed", "classify", "llm", "done"] as const;
const NO_RESPONSE_MS = 20000;
const labels = pl as Record<string, string>;

function stageState(event: StageEvent | undefined): "waiting" | "running" | "done" | "error" {
  if (!event) return "waiting";
  if (event.status === "error") return "error";
  if (event.status === "done") return "done";
  return "running";
}

function clock(at: number): string {
  const d = new Date(at);
  return `${d.toLocaleTimeString("pl-PL", { hour12: false })}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

export default function ScanNow() {
  const [url, setUrl] = useState("");
  const [scanId, setScanId] = useState<string | null>(null);
  const [events, setEvents] = useState<TimedEvent[]>([]);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [requestFailed, setRequestFailed] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const connected = socket.connected;

  useEffect(() => {
    function onStage(event: StageEvent) {
      if (event.scan_id !== scanId) return;
      setTimedOut(false);
      setEvents((prev) => [...prev, { ...event, at: Date.now() }]);
    }
    socket.on("scan_stage", onStage);
    return () => {
      socket.off("scan_stage", onStage);
    };
  }, [scanId]);

  const started = events.length > 0;

  useEffect(() => {
    if (!scanId || started) return;
    const timer = window.setTimeout(() => setTimedOut(true), NO_RESPONSE_MS);
    return () => window.clearTimeout(timer);
  }, [scanId, started]);

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    setEvents([]);
    setScanId(null);
    setTimedOut(false);
    setRequestFailed(false);
    setSubmitting(true);
    try {
      const { scan_id } = await api.scanUrl(url);
      setScanId(scan_id);
      setStartedAt(Date.now());
      socket.emit("subscribe_scan", { scan_id });
    } catch {
      setRequestFailed(true);
    } finally {
      setSubmitting(false);
    }
  }

  const latest = new Map(events.map((ev) => [ev.stage, ev]));
  const failedEvent = events.find((ev) => ev.status === "error");
  const finished = latest.get("done")?.status === "done" || !!failedEvent;
  const inFlight = submitting || (!!scanId && !finished && !timedOut);
  const doneEvent = latest.get("done");
  const moduleResults: ModuleResults = (doneEvent?.data?.modules ?? latest.get("classify")?.data?.modules);
  const findingIds = doneEvent?.data?.finding_ids ?? Object.values(moduleResults ?? {}).flatMap((r) => (r.finding_id ? [r.finding_id] : []));
  const total = finished && startedAt ? ((events[events.length - 1].at - startedAt) / 1000).toFixed(1).replace(".", ",") : null;

  function duration(stage: string, index: number): string | null {
    const event = latest.get(stage);
    if (!event || stageState(event) === "waiting") return null;
    const previous = index === 0 ? startedAt : latest.get(STAGES[index - 1])?.at;
    if (!previous) return null;
    return `${((event.at - previous) / 1000).toFixed(1).replace(".", ",")} s`;
  }

  return (
    <>
      <div>
        <h1 className="page__title">{pl["scan.title"]}</h1>
        <p className="page__sub">{pl["scan.lede"]}</p>
      </div>

      <form className="panel scanform" onSubmit={handleScan}>
        <input
          className="input scanform__input"
          type="url"
          required
          placeholder={pl["scan.placeholder"]}
          aria-label={pl["scan.title"]}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <select className="input scanform__modules is-soon" disabled title="API skanu przyjmuje tylko adres" aria-label="Moduły">
          <option>Moduły: wszystkie</option>
        </select>
        <button className="btn btn--primary" type="submit" disabled={inFlight || !url}>
          {submitting ? pl["scan.starting"] : inFlight ? pl["scan.running"] : pl["scan.button"]}
        </button>
      </form>

      {requestFailed && <QueryError message={pl["scan.failed"]} />}
      {timedOut && !started && <QueryError message={pl["scan.noResponse"]} />}

      {scanId && (
        <>
          <section className="panel">
            <div className="panel__head">
              <h2>Przebieg skanu</h2>
              <span className="muted mono">
                {scanId.slice(0, 8)}
                {total ? ` · ${total} s` : ""}
              </span>
            </div>
            <ol className="stepper" aria-label={pl["scan.running"]}>
              {STAGES.map((stage, index) => {
                const event = latest.get(stage);
                const state = stageState(event);
                return (
                  <li key={stage} className={`step step--${state}`}>
                    <span className="step__dot" aria-hidden="true">
                      {state === "done" ? "✓" : state === "error" ? "!" : state === "running" ? "" : index + 1}
                    </span>
                    <span className="step__name">{labels[`scan.stage.${stage}`]}</span>
                    <span className="step__time mono">{state === "waiting" ? "oczekuje" : duration(stage, index)}</span>
                    {state === "error" ? (
                      <span className="step__msg step__msg--error">{event?.message || pl["scan.stageFailed"]}</span>
                    ) : (
                      event?.message && <span className="step__msg">{event.message}</span>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
          {!started && !timedOut && <Loading label={pl["scan.queued"]} />}

          <div className="row-split">
            <section className="panel row-split__main">
              <div className="panel__head">
                <h2>Zdarzenia na żywo</h2>
                <span className={connected ? "ok-text" : "muted"}>WebSocket · {connected ? "połączono" : "brak połączenia"}</span>
              </div>
              <ul className="eventlog">
                {events.map((ev, i) => (
                  <li key={i}>
                    <span className="muted mono">{clock(ev.at)}</span>
                    <span className={`eventlog__name mono${ev.status === "error" ? " text-critical" : ""}`}>
                      {ev.stage}.{ev.status}
                    </span>
                    <span className="eventlog__msg">{ev.message}</span>
                  </li>
                ))}
                {events.length === 0 && <li className="muted">Oczekiwanie na pierwsze zdarzenie</li>}
              </ul>
            </section>

            <section className="panel row-split__side">
              <div className="panel__head">
                <h2>Wynik skanu</h2>
              </div>
              <div className="panel__body levels">
                {doneEvent?.message && (
                  <p className={failedEvent ? "text-critical" : findingIds.length ? "ok-text" : "muted"} role="status">
                    {doneEvent.message}
                  </p>
                )}
                {["m1", "m2", "m3"].map((m) => {
                  const result = moduleResults?.[m];
                  return (
                    <div className="levels__row" key={m}>
                      <span className="levels__label">
                        <ModuleBadge module={m} />
                      </span>
                      <span className="levels__track" title="Trafność: jak bardzo treść dotyczy modułu">
                        {result && <span className="levels__bar" style={{ width: `${result.relevance * 100}%`, background: "var(--brand)" }} />}
                      </span>
                      <span className="levels__count">
                        {result ? result.relevance.toFixed(2).replace(".", ",") : "-"}
                      </span>
                    </div>
                  );
                })}
                <p className="muted">Pasek to trafność tematyczna (próg 0,50). Poniżej progu moduł nie tworzy findingu.</p>
                {findingIds.length > 0 && (
                  <ul className="levels">
                    {findingIds.map((id) => (
                      <li key={id}>
                        <Link to={`/findings/${id}`}>Finding #{id}</Link>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </>
  );
}
