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

export default function ScanNow() {
  const [url, setUrl] = useState("");
  const [scanId, setScanId] = useState<string | null>(null);
  const [stages, setStages] = useState<StageEvent[]>([]);

  useEffect(() => {
    function onStage(event: StageEvent) {
      if (event.scan_id !== scanId) return;
      setStages((prev) => [...prev, event]);
    }
    socket.on("scan_stage", onStage);
    return () => {
      socket.off("scan_stage", onStage);
    };
  }, [scanId]);

  async function handleScan() {
    setStages([]);
    const { scan_id } = await api.scanUrl(url);
    setScanId(scan_id);
    socket.emit("subscribe_scan", { scan_id });
  }

  return (
    <div>
      <h2>{pl["nav.scan"]}</h2>
      <div className="card">
        <input
          style={{ width: "70%" }}
          placeholder={pl["scan.placeholder"]}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button className="btn" onClick={handleScan} style={{ marginLeft: "0.5rem" }}>
          {pl["scan.button"]}
        </button>

        <ul style={{ marginTop: "1rem" }}>
          {stages.map((s, i) => (
            <li key={i}>
              <strong>{s.stage}</strong>: {s.status} {s.message ? `- ${s.message}` : ""}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
