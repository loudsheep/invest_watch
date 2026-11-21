import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleTag from "../components/ModuleTag";
import QueryError from "../components/QueryError";
import Ruler from "../components/Ruler";
import { api } from "../lib/api";
import { HIGH_RISK, MODULES, STATUSES, formatDate, statusLabel } from "../lib/modules";

const labels = pl as Record<string, string>;

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

const RISK_RANGES: Record<string, { min?: number; max?: number }> = {
  high: { min: HIGH_RISK },
  medium: { min: 0.5, max: HIGH_RISK },
  low: { max: 0.5 },
};
const PLATFORMS = ["web", "youtube", "dataset"];

export default function Findings() {
  const [module, setModule] = useState("");
  const [status, setStatus] = useState("");
  const [risk, setRisk] = useState("");
  const [platform, setPlatform] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data, isError, isSuccess, isPending, refetch } = useQuery({
    queryKey: ["findings", module, status, risk, platform, dateFrom, dateTo],
    queryFn: () =>
      api.listFindings({
        module: module || undefined,
        status: status || undefined,
        source_platform: platform || undefined,
        min_score: RISK_RANGES[risk]?.min,
        max_score: RISK_RANGES[risk]?.max,
        date_from: dateFrom ? `${dateFrom}T00:00:00` : undefined,
        date_to: dateTo ? `${dateTo}T23:59:59` : undefined,
      }),
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
        <Chips
          label={pl["common.risk"]}
          value={risk}
          onChange={setRisk}
          options={Object.keys(RISK_RANGES).map((r) => ({ value: r, label: labels[`filters.risk.${r}`] }))}
        />
        <Chips
          label={pl["common.source"]}
          value={platform}
          onChange={setPlatform}
          options={PLATFORMS.map((p) => ({ value: p, label: p }))}
        />
        <div className="chips">
          <span className="chips__label">{pl["common.date"]}</span>
          <label className="datefield">
            {pl["common.from"]}
            <input className="input" type="date" value={dateFrom} max={dateTo || undefined} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label className="datefield">
            {pl["common.to"]}
            <input className="input" type="date" value={dateTo} min={dateFrom || undefined} onChange={(e) => setDateTo(e.target.value)} />
          </label>
        </div>
      </div>

      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
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
