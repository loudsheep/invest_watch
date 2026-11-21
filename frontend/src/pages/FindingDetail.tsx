import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function FindingDetail() {
  const { id } = useParams();
  const { data } = useQuery({
    queryKey: ["finding", id],
    queryFn: () => api.getFinding(Number(id)),
    enabled: !!id,
  });

  if (!data) return <p>Wczytywanie...</p>;

  return (
    <div>
      <h2>
        Finding #{data.id} - {data.module.toUpperCase()}
      </h2>
      <div className="card">
        <p>
          <strong>URL:</strong> <a href={data.document_url} target="_blank" rel="noreferrer">{data.document_url}</a>
        </p>
        <p>
          <strong>Tytuł:</strong> {data.document_title}
        </p>
        <p>
          <strong>Score:</strong> {data.score.toFixed(3)} (model v{data.model_version}, prompt v{data.prompt_version})
        </p>
        <p>
          <strong>Wyjaśnienie:</strong> {data.explanation}
        </p>
        {data.screenshot_url && (
          <div>
            <strong>Screenshot:</strong>
            <br />
            <img src={data.screenshot_url} alt="evidence screenshot" style={{ maxWidth: "100%" }} />
          </div>
        )}
        <details>
          <summary>Szczegóły (JSON)</summary>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(data.details, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
