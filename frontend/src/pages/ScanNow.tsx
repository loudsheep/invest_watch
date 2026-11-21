import { useEffect, useState } from "react";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import QueryError from "../components/QueryError";
import { api } from "../lib/api";
import { socket } from "../lib/socket";

interface StageEvent {
  scan_id: string;
  stage: string;
  status: string;
  message?: string | null;
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

export default function ScanNow() {
  const [url, setUrl] = useState("");
  const [scanId, setScanId] = useState<string | null>(null);
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [requestFailed, setRequestFailed] = useState(false);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    function onStage(event: StageEvent) {
      if (event.scan_id !== scanId) return;
      setTimedOut(false);
      setEvents((prev) => [...prev, event]);
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

  return (
    <>
      <h1 className="page__title">{pl["scan.title"]}</h1>
      <p className="lede">{pl["scan.lede"]}</p>

      <form className="scanform" onSubmit={handleScan}>
        <input
          className="input input--wide"
          type="url"
          required
          placeholder={pl["scan.placeholder"]}
          aria-label={pl["scan.title"]}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button className="btn btn--busy" type="submit" disabled={inFlight || !url}>
          {inFlight && <span className="spinner spinner--light" aria-hidden="true" />}
          {submitting ? pl["scan.starting"] : inFlight ? pl["scan.running"] : pl["scan.button"]}
        </button>
      </form>

      {requestFailed && <QueryError message={pl["scan.failed"]} />}
      {timedOut && !started && <QueryError message={pl["scan.noResponse"]} />}

      {scanId && (
        <>
          <ol className="stages" aria-label={pl["scan.running"]}>
            {STAGES.map((stage) => {
              const event = latest.get(stage);
              const state = stageState(event);
              return (
                <li key={stage} className={`stage stage--${state}`}>
                  <span className="stage__dot" aria-hidden="true" />
                  <span className="stage__name">{labels[`scan.stage.${stage}`]}</span>
                  {state === "error" && (
                    <span className="stage__msg stage__msg--error">{event?.message || pl["scan.stageFailed"]}</span>
                  )}
                  {state !== "error" && event?.message && <span className="stage__msg">{event.message}</span>}
                </li>
              );
            })}
          </ol>
          {!started && !timedOut && <Loading label={pl["scan.queued"]} />}
        </>
      )}
    </>
  );
}
