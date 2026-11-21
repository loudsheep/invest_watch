import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import { Criteria, Entities, Metrics, ModuleFacts, quotesFor } from "../components/FindingFacts";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import SoonTag from "../components/SoonTag";
import StatusBadge from "../components/StatusBadge";
import { API_URL, api } from "../lib/api";
import { HIGH_RISK, formatDate, moduleInfo, riskBand } from "../lib/modules";

const BAND_LABEL = { low: "Niskie", medium: "Średnie", high: "Wysokie", critical: "Krytyczne" } as const;

export default function FindingDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const { data, isError, refetch } = useQuery({
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

  if (isError) return <QueryError onRetry={() => refetch()} />;
  if (!data) return <Loading />;

  const screenshot = data.screenshot_url
    ? data.screenshot_url.startsWith("http")
      ? data.screenshot_url
      : `${API_URL}${data.screenshot_url}`
    : null;
  const band = riskBand(data.score);
  const quotes = quotesFor(data);
  const busy = mutation.isPending;

  return (
    <>
      <div className="page__header page__header--top">
        <div>
          <p className="crumbs">
            <Link to="/findings">← {pl["findings.title"]}</Link>
            <span className="muted"> / #{data.id}</span>
          </p>
          <p className="module-line">
            <ModuleBadge module={data.module} /> <span className="muted">{moduleInfo(data.module).name}</span>
          </p>
          <h1 className="page__title">{data.document_title || `Finding #${data.id}`}</h1>
          <p className="source-line">
            <a href={data.document_url} target="_blank" rel="noreferrer" className="source-line__url">
              {data.document_url}
            </a>
            {data.document_platform && <span className="muted">{data.document_platform}</span>}
            <span className="muted">wykryto {formatDate(data.created_at)}</span>
          </p>
        </div>
        <button className="btn btn--secondary" disabled title="Wymaga endpointu pakietu dowodów">
          Pobierz pakiet dowodów <SoonTag />
        </button>
      </div>

      <div className="row-split">
        <div className="row-split__main detail-main">
          <section className="panel">
            <div className="panel__head">
              <h2>Dowód: zrzut strony</h2>
              {data.module === "m2" && <span className="muted">Wizualna wyrazistość ostrzeżenia</span>}
            </div>
            {screenshot ? (
              <div className="panel__body">
                <img className="shot" src={screenshot} alt="Zrzut ekranu zapisany jako dowód" />
              </div>
            ) : (
              <p className="empty">Brak zrzutu ekranu dla tego findingu.</p>
            )}
            <Metrics data={data} />
          </section>

          <Criteria data={data} />
          <ModuleFacts data={data} />

          {(quotes.length > 0 || data.explanation) && (
            <section className="panel">
              <div className="panel__head">
                <h2>Cytaty i wyjaśnienie modelu</h2>
              </div>
              <div className="panel__body quotes">
                {quotes.map((q) => (
                  <blockquote key={`${q.label}-${q.text}`} className={`quote quote--${q.tone}`}>
                    <span className="micro">{q.label}</span>
                    <p>„{q.text}”</p>
                  </blockquote>
                ))}
                {data.explanation && <p className="prose">{data.explanation}</p>}
              </div>
            </section>
          )}

          <details className="panel tech">
            <summary className="panel__head">{pl["finding.details"]}</summary>
            <pre className="panel__body">{JSON.stringify(data.details, null, 2)}</pre>
          </details>
        </div>

        <aside className="row-split__side">
          <section className="panel">
            <div className="panel__head">
              <h2>Ocena modelu</h2>
              <span className="mono muted">
                model v{data.model_version} · prompt v{data.prompt_version}
              </span>
            </div>
            <div className="panel__body">
              <div className="score-line">
                <span className={`score-big score-big--${band}`}>{data.score.toFixed(2).replace(".", ",")}</span>
                <span className={`band-tag band-tag--${band}`}>{BAND_LABEL[band]}</span>
              </div>
              <div className="score-bar">
                <span className={`score-bar__fill score-bar__fill--${band}`} style={{ width: `${data.score * 100}%` }} />
                <span className="score-bar__mark" style={{ left: `${HIGH_RISK * 100}%` }} />
              </div>
              <div className="score-scale mono muted">
                <span>0,00</span>
                <span>próg wysokiego ryzyka {HIGH_RISK.toFixed(2).replace(".", ",")}</span>
                <span>1,00</span>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <h2>{pl["finding.decision"]}</h2>
            </div>
            <div className="panel__body decision">
              <p className="decision__status">
                <span className="muted">{pl["common.status"]}</span> <StatusBadge status={data.status} />
              </p>
              <div className="decision__grid">
                <button className="btn btn--primary" disabled={busy || data.status === "confirmed"} onClick={() => mutation.mutate("confirmed")}>
                  Potwierdź
                </button>
                <button className="btn btn--secondary" disabled={busy || data.status === "dismissed"} onClick={() => mutation.mutate("dismissed")}>
                  Odrzuć
                </button>
                <button className="btn btn--secondary" disabled={busy || data.status === "in_review"} onClick={() => mutation.mutate("in_review")}>
                  Przejmij
                </button>
                <button className="btn btn--danger" disabled={busy || data.status === "escalated"} onClick={() => mutation.mutate("escalated")}>
                  Eskaluj
                </button>
              </div>
              <textarea
                className="input is-soon"
                rows={3}
                disabled
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Notatka do decyzji (trafi do audit logu)"
                title="API statusu nie przyjmuje notatki"
              />
              {mutation.isSuccess && (
                <p className="saved" role="status">
                  {pl["finding.saved"]}
                </p>
              )}
              {mutation.isError && <QueryError onRetry={() => mutation.mutate(mutation.variables ?? "in_review")} />}
            </div>
          </section>

          <Entities data={data} />

          <section className="panel is-soon">
            <div className="panel__head">
              <h2>Łańcuch dowodowy</h2>
              <SoonTag />
            </div>
            <div className="panel__body custody">
              {["HTML", "Zrzut ekranu", "Computed styles"].map((label) => (
                <div key={label}>
                  <p className="custody__label">{label}</p>
                  <p className="cell-sub">SHA-256 -</p>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}
