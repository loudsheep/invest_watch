import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleTag from "../components/ModuleTag";
import QueryError from "../components/QueryError";
import Ruler from "../components/Ruler";
import { api, type CaseRow } from "../lib/api";
import { formatDate } from "../lib/modules";

function CaseItem({ item }: { item: CaseRow }) {
  const [open, setOpen] = useState(false);
  const detail = useQuery({ queryKey: ["case", item.id], queryFn: () => api.getCase(item.id), enabled: open });
  const count = item.finding_ids?.length ?? 0;

  return (
    <li className="case">
      <button className="case__head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="row__id">#{item.id}</span>
        <span className="case__title">
          {pl["cases.entity"]} #{item.primary_entity_id}
          <span className="case__desc">{item.description || pl["cases.noDescription"]}</span>
        </span>
        <span className="case__count">{count}</span>
        <span className="status">{item.status}</span>
        <span className="row__meta">{formatDate(item.created_at)}</span>
      </button>
      {open && (
        <div className="case__body">
          <h3 className="section__title">{pl["cases.findings"]}</h3>
          {detail.isPending && <Loading />}
          {detail.isError && <QueryError onRetry={() => detail.refetch()} />}
          <ul className="rows">
            {(detail.data?.findings ?? []).map((f) => (
              <li key={f.id}>
                <Link to={`/findings/${f.id}`} className="row row--finding">
                  <ModuleTag module={f.module} />
                  <Ruler score={f.score} module={f.module} />
                  <span className="score">{f.score.toFixed(2)}</span>
                  <span className="row__meta">#{f.id}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}

export default function Cases() {
  const { data, isError, isSuccess, isPending, refetch } = useQuery({ queryKey: ["cases"], queryFn: api.listCases });

  return (
    <>
      <h1 className="page__title">{pl["cases.title"]}</h1>
      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
      {isSuccess && data.length === 0 && <p className="empty">{pl["cases.empty"]}</p>}
      <ul className="rows">
        {(data ?? []).map((c) => (
          <CaseItem key={c.id} item={c} />
        ))}
      </ul>
    </>
  );
}
