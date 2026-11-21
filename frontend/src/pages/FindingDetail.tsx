import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import ModuleTag from "../components/ModuleTag";
import Ruler from "../components/Ruler";
import { API_URL, api } from "../lib/api";
import { HIGH_RISK, STATUSES, formatDate, moduleInfo, statusLabel } from "../lib/modules";

const ACTIONS: Record<string, string> = {
  in_review: "Przejmij do przeglądu",
  confirmed: "Potwierdź",
  dismissed: "Odrzuć",
  escalated: "Eskaluj",
};

export default function FindingDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();

  const { data, isError } = useQuery({
    queryKey: ["finding", id],
    queryFn: () => api.getFinding(Number(id)),
    enabled: !!id,
  });

  const mutation = useMutation({
    mutationFn: (status: string) => api.updateFindingStatus(Number(id), status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["finding", id] });
      queryClient.invalidateQueries({ queryKey: ["findings"] });
      queryClient.invalidateQueries({ queryKey: ["counters"] });
    },
  });

  if (isError) return <p className="notice">{pl["common.error"]}</p>;
  if (!data) return <p className="boot">{pl["common.loading"]}</p>;

  const screenshot = data.screenshot_url
    ? data.screenshot_url.startsWith("http")
      ? data.screenshot_url
      : `${API_URL}${data.screenshot_url}`
    : null;
  const high = data.score >= HIGH_RISK;

  return (
    <>
      <Link to="/findings" className="link link--back">
        {pl["finding.back"]}
      </Link>
      <h1 className="page__title page__title--tight">{data.document_title || `Finding #${data.id}`}</h1>
      <p className="source">
        <ModuleTag module={data.module} /> {moduleInfo(data.module).name}
        {data.document_platform && <span className="source__platform"> na {data.document_platform}</span>}
        <br />
        <a href={data.document_url} target="_blank" rel="noreferrer" className="source__url">
          {data.document_url}
        </a>
      </p>

      <div className="dossier">
        <div className="dossier__main">
          <section>
            <h2 className="section__title">{pl["finding.evidence"]}</h2>
            {data.evidence ? (
              <blockquote className="evidence">
                <mark>{data.evidence}</mark>
              </blockquote>
            ) : (
              <p className="empty">{pl["finding.evidenceEmpty"]}</p>
            )}
          </section>

          {data.explanation && (
            <section>
              <h2 className="section__title">{pl["finding.explanation"]}</h2>
              <p className="prose">{data.explanation}</p>
            </section>
          )}

          {screenshot && (
            <section>
              <h2 className="section__title">{pl["finding.screenshot"]}</h2>
              <img className="shot" src={screenshot} alt="Zrzut ekranu zapisany jako dowód" />
            </section>
          )}

          <details className="tech">
            <summary>{pl["finding.details"]}</summary>
            <pre>{JSON.stringify(data.details, null, 2)}</pre>
          </details>
        </div>

        <aside className="dossier__side">
          <div className="verdict">
            <span className={`verdict__score${high ? " verdict__score--high" : ""}`}>{data.score.toFixed(2)}</span>
            <Ruler score={data.score} module={data.module} />
            <span className="verdict__meta">
              {pl["finding.versions"].replace("{model}", String(data.model_version)).replace("{prompt}", String(data.prompt_version))}
              <br />
              {formatDate(data.created_at)}
            </span>
          </div>

          <h2 className="section__title">{pl["finding.decision"]}</h2>
          <p className="current">
            {pl["common.status"]}: <span className={`status status--${data.status}`}>{statusLabel(data.status)}</span>
          </p>
          <div className="actions">
            {STATUSES.filter((s) => s !== "new").map((s) => (
              <button
                key={s}
                className={`btn${s === "confirmed" ? "" : " btn--ghost"}`}
                disabled={mutation.isPending || data.status === s}
                onClick={() => mutation.mutate(s)}
              >
                {ACTIONS[s]}
              </button>
            ))}
          </div>
          {mutation.isSuccess && (
            <p className="saved" role="status">
              {pl["finding.saved"]}
            </p>
          )}
          {mutation.isError && <p className="notice">{pl["common.error"]}</p>}
        </aside>
      </div>
    </>
  );
}
