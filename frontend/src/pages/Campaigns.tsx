import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import RiskCell from "../components/RiskCell";
import { api, type Campaign } from "../lib/api";
import { formatDate } from "../lib/modules";

const MIN_SIMILARITY = 0.9;
const MAX_SIMILARITY = 0.99;

function formatOffset(from: string, to: string): string {
  const minutes = Math.round((new Date(to).getTime() - new Date(from).getTime()) / 60000);
  if (minutes < 1) return "start";
  if (minutes < 120) return `+${minutes} min`;
  return `+${Math.round(minutes / 60)} h`;
}

export default function Campaigns() {
  const [similarity, setSimilarity] = useState(0.95);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ["campaigns", similarity],
    queryFn: () => api.campaigns(similarity),
  });

  const current: Campaign | undefined = data?.find((c) => c.id === selectedId) ?? data?.[0];

  return (
    <>
      <div className="page__header">
        <div>
          <h1 className="page__title">Kampanie</h1>
          <p className="page__sub">
            Ta sama treść u wielu autorów lub w wielu miejscach, wykryta po podobieństwie wektorowym dokumentów.
          </p>
        </div>
        <label className="campaign-slider">
          <span className="micro">Minimalne podobieństwo: {similarity.toFixed(2).replace(".", ",")}</span>
          <input
            type="range"
            className="slider"
            min={MIN_SIMILARITY}
            max={MAX_SIMILARITY}
            step={0.01}
            value={similarity}
            onChange={(e) => setSimilarity(Number(e.target.value))}
            aria-label="Minimalne podobieństwo"
          />
        </label>
      </div>

      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
      {data && data.length === 0 && <p className="empty">Brak kampanii przy tym progu podobieństwa. Obniż próg.</p>}

      {data && current && (
        <div className="row-split">
          <section className="panel row-split__side">
            <div className="panel__head">
              <h2>Klastry ({data.length})</h2>
            </div>
            {data.map((c) => (
              <button
                key={c.id}
                className={`campaign-item${c.id === current.id ? " campaign-item--on" : ""}`}
                onClick={() => setSelectedId(c.id)}
              >
                <span className="cell-id">{c.documents[0]?.title ?? `Kampania #${c.id}`}</span>
                <span className="muted">
                  {c.size} treści · {c.authors.length || c.domains.length} {c.authors.length ? "autorów" : "domen"}
                </span>
                <span className="campaign-item__meta">
                  {c.modules.map((m) => (
                    <ModuleBadge key={m} module={m} />
                  ))}
                  <RiskCell score={c.max_score} />
                </span>
              </button>
            ))}
          </section>

          <section className="panel row-split__main">
            <div className="panel__head">
              <h2>Kampania #{current.id}</h2>
              <span className="muted">
                {formatDate(current.first_seen)} - {formatDate(current.last_seen)}
              </span>
            </div>
            <dl className="facts">
              <dt>Autorzy</dt>
              <dd>{current.authors.join(", ") || "-"}</dd>
              <dt>Domeny</dt>
              <dd>{current.domains.join(", ") || "-"}</dd>
              <dt>Wspólne kody promo</dt>
              <dd>{current.promo_codes.map((code) => <code key={code}>{code}</code>)}{current.promo_codes.length === 0 && "-"}</dd>
            </dl>
            <div className="table-head micro">
              <span className="col-docs">Kiedy</span>
              <span className="col-grow">Treść</span>
              <span className="col-health">Autor</span>
              <span className="col-mod">Typ</span>
            </div>
            {current.documents.map((doc) => {
              const best = doc.findings[0];
              return (
                <div className="table-row" key={doc.document_id}>
                  <span className="col-docs mono muted">{formatOffset(current.first_seen, doc.fetched_at)}</span>
                  <span className="col-grow">
                    {best ? <Link to={`/findings/${best.id}`}>{doc.title || doc.url}</Link> : doc.title || doc.url}
                    <p className="muted mono">{doc.domain}</p>
                  </span>
                  <span className="col-health">{doc.author ?? "-"}</span>
                  <span className="col-mod">{best && <ModuleBadge module={best.module} />}</span>
                </div>
              );
            })}
          </section>
        </div>
      )}
    </>
  );
}
