import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import ModuleTag from "../components/ModuleTag";
import Ruler from "../components/Ruler";
import { api } from "../lib/api";
import { HIGH_RISK, MODULES, STATUSES, formatDate, statusLabel } from "../lib/modules";

interface ChipsProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

function Chips({ label, value, options, onChange }: ChipsProps) {
  return (
    <div className="chips" role="group" aria-label={label}>
      <span className="chips__label">{label}</span>
      {[{ value: "", label: pl["common.all"] }, ...options].map((o) => (
        <button key={o.value} className="chip" aria-pressed={value === o.value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export default function Findings() {
  const [module, setModule] = useState("");
  const [status, setStatus] = useState("");

  const { data, isError, isSuccess } = useQuery({
    queryKey: ["findings", module, status],
    queryFn: () => api.listFindings({ module: module || undefined, status: status || undefined }),
  });

  return (
    <>
      <h1 className="page__title">{pl["findings.title"]}</h1>

      <div className="filters">
        <Chips
          label={pl["common.module"]}
          value={module}
          onChange={setModule}
          options={MODULES.map((m) => ({ value: m.id, label: m.short }))}
        />
        <Chips
          label={pl["common.status"]}
          value={status}
          onChange={setStatus}
          options={STATUSES.map((s) => ({ value: s, label: statusLabel(s) }))}
        />
      </div>

      {isError && <p className="notice">{pl["common.error"]}</p>}
      {isSuccess && data.length === 0 && <p className="empty">{pl["findings.empty"]}</p>}

      <ul className="rows">
        {(data ?? []).map((f) => (
          <li key={f.id}>
            <Link to={`/findings/${f.id}`} className="row row--wide">
              <span className="row__id">#{f.id}</span>
              <ModuleTag module={f.module} />
              <Ruler score={f.score} module={f.module} />
              <span className={`score${f.score >= HIGH_RISK ? " score--high" : ""}`}>{f.score.toFixed(2)}</span>
              <span className={`status status--${f.status}`}>{statusLabel(f.status)}</span>
              <span className="row__meta">{formatDate(f.created_at)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
