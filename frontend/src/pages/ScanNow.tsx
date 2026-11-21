import { useEffect, useState } from "react";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";
import { socket } from "../lib/socket";

interface StageEvent {
  scan_id: string;
  stage: string;
  status: string;
  message?: string | null;
}

const STAGES = ["fetch", "preprocess", "embed", "classify", "llm", "done"] as const;
const labels = pl as Record<string, string>;

export default function ScanNow() {
  const [url, setUrl] = useState("");
  const [scanId, setScanId] = useState<string | null>(null);
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    function onStage(event: StageEvent) {
      if (event.scan_id !== scanId) return;
      setEvents((prev) => [...prev, event]);
    }
    socket.on("scan_stage", onStage);
    return () => {
      socket.off("scan_stage", onStage);
    };
  }, [scanId]);

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    setEvents([]);
    setFailed(false);
    setBusy(true);
    try {
      const { scan_id } = await api.scanUrl(url);
      setScanId(scan_id);
      socket.emit("subscribe_scan", { scan_id });
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  const latest = new Map(events.map((e) => [e.stage, e]));
  const errored = events.find((e) => e.stage === "error" || e.status === "error");

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
        <button className="btn" type="submit" disabled={busy || !url}>
          {pl["scan.button"]}
        </button>
      </form>

      {(failed || errored) && (
        <p className="notice" role="alert">
          {errored?.message || pl["scan.failed"]}
        </p>
      )}

      {scanId && (
        <ol className="stages" aria-label={pl["scan.running"]}>
          {STAGES.map((stage) => {
            const event = latest.get(stage);
            const state = event?.status === "done" || (stage === "done" && event) ? "done" : event ? "running" : "waiting";
            return (
              <li key={stage} className={`stage stage--${state}`}>
                <span className="stage__dot" aria-hidden="true" />
                <span className="stage__name">{labels[`scan.stage.${stage}`]}</span>
                {event?.message && <span className="stage__msg">{event.message}</span>}
              </li>
            );
          })}
        </ol>
      )}
    </>
  );
}
