import { useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import CaseGraph from "../components/CaseGraph";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import RiskCell from "../components/RiskCell";
import SoonTag from "../components/SoonTag";
import { api, type CaseDetail, type CaseRow } from "../lib/api";
import { MODULES, formatShortDate } from "../lib/modules";

function summarize(detail?: CaseDetail) {
  const findings = detail?.findings ?? [];
  return {
    count: findings.length,
    max: findings.reduce((acc, f) => Math.max(acc, f.score), 0),
    byModule: MODULES.map((m) => ({ id: m.id, n: findings.filter((f) => f.module === m.id).length })).filter((m) => m.n > 0),
  };
}

function caseName(item: CaseRow) {
  return item.primary_entity_name ?? `${pl["cases.entity"]} #${item.primary_entity_id}`;
}

export default function Cases() {
  const cases = useQuery({ queryKey: ["cases"], queryFn: api.listCases });
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const items = cases.data ?? [];

  const details = useQueries({
    queries: items.map((c) => ({ queryKey: ["case", c.id], queryFn: () => api.getCase(c.id) })),
  });
  const summaries = new Map(items.map((c, i) => [c.id, summarize(details[i]?.data)]));
  const sorted = [...items].sort((a, b) => (summaries.get(b.id)?.max ?? 0) - (summaries.get(a.id)?.max ?? 0));
  const current = sorted.find((c) => c.id === selectedId) ?? sorted[0];
  const currentDetail = details[items.findIndex((c) => c.id === current?.id)];
  const currentSummary = current ? summaries.get(current.id) : undefined;

  return (
    <>
      <div>
        <h1 className="page__title">{pl["cases.title"]}</h1>
        <p className="page__sub">
          Findingi łączone w case, gdy dotyczą tego samego podmiotu{cases.isSuccess ? ` · ${items.length} case'ów` : ""}
        </p>
      </div>

      {cases.isPending && <Loading />}
      {cases.isError && <QueryError onRetry={() => cases.refetch()} />}
      {cases.isSuccess && items.length === 0 && <p className="empty">{pl["cases.empty"]}</p>}

      {current && (
        <div className="cases-layout">
          <aside className="panel case-list">
            <div className="case-list__sort micro">Sortuj: najwyższe ryzyko</div>
            {sorted.map((c) => {
              const summary = summaries.get(c.id);
              return (
                <button
                  key={c.id}
                  className={`case-item${c.id === current.id ? " case-item--on" : ""}`}
                  onClick={() => setSelectedId(c.id)}
                >
                  <span className="case-item__top">
                    <strong>{caseName(c)}</strong>
                    {summary && summary.count > 0 && <RiskCell score={summary.max} />}
                  </span>
                  <span className="case-item__modules">
                    {summary?.byModule.map((m) => (
                      <span key={m.id} className="case-item__module">
                        <ModuleBadge module={m.id} /> <span className="muted mono">×{m.n}</span>
                      </span>
                    ))}
                  </span>
                  <span className="muted mono case-item__meta">
                    {summary?.count ?? 0} findingów · {formatShortDate(c.created_at)}
                  </span>
                </button>
              );
            })}
          </aside>

          <div className="case-detail">
            <section className="panel case-head">
              <div>
                <h2 className="case-head__title">{caseName(current)}</h2>
                <p className="muted">
                  case #{current.id} · {current.description || pl["cases.noDescription"]} · {currentSummary?.count ?? 0} findingów · utworzony{" "}
                  {formatShortDate(current.created_at)}
                </p>
              </div>
              <div className="case-head__actions">
                {currentSummary && currentSummary.count > 0 && <RiskCell score={currentSummary.max} />}
                <button className="btn btn--secondary" disabled title="Wymaga endpointu raportu PDF">
                  Raport PDF z hashami <SoonTag />
                </button>
                <button className="btn btn--primary" disabled title="Wymaga endpointu zmiany statusu case'a">
                  Eskaluj case <SoonTag />
                </button>
              </div>
            </section>

            <section className="panel">
              <div className="panel__head">
                <h2>{pl["cases.graph"]}</h2>
              </div>
              <CaseGraph caseId={current.id} />
            </section>

            <section className="panel">
              <div className="panel__head">
                <h2>{pl["cases.findings"]}</h2>
                <span className="muted">{currentSummary?.count ?? 0}</span>
              </div>
              {currentDetail?.isPending && <Loading />}
              {currentDetail?.isError && <QueryError onRetry={() => currentDetail.refetch()} />}
              {(currentDetail?.data?.findings ?? []).map((f) => (
                <Link key={f.id} to={`/findings/${f.id}`} className="table-row">
                  <span className="col-mod">
                    <ModuleBadge module={f.module} />
                  </span>
                  <span className="col-grow">
                    <p className="cell-title">Finding #{f.id}</p>
                  </span>
                  <span className="col-risk">
                    <RiskCell score={f.score} />
                  </span>
                </Link>
              ))}
            </section>
          </div>
        </div>
      )}
    </>
  );
}
