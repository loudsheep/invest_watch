import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatShortDate } from "../lib/modules";
import ModuleBadge from "./ModuleBadge";
import RiskCell from "./RiskCell";

interface AlertsPanelProps {
  readIds: Set<number>;
  onMarkRead: (ids: number[]) => void;
  onClose: () => void;
}

export function useHighRiskAlerts(enabled = true) {
  return useQuery({
    enabled,
    queryKey: ["findings", "alerts"],
    queryFn: () => api.listFindings({ status: "new", min_score: 0.8, limit: 10 }),
  });
}

export default function AlertsPanel({ readIds, onMarkRead, onClose }: AlertsPanelProps) {
  const { data = [] } = useHighRiskAlerts();
  const unread = data.filter((f) => !readIds.has(f.id));

  return (
    <div className="alerts-panel panel" role="dialog" aria-label="Alerty">
      <div className="panel__head">
        <span>Alerty · {unread.length} nowe</span>
        <button className="linkbtn" onClick={() => onMarkRead(data.map((f) => f.id))}>
          Oznacz jako przeczytane
        </button>
      </div>
      {data.length === 0 && <p className="empty">Brak alertów wysokiego ryzyka.</p>}
      {data.map((f) => {
        const isUnread = !readIds.has(f.id);
        return (
          <Link
            key={f.id}
            to={`/findings/${f.id}`}
            className={`alerts-panel__row${isUnread ? " alerts-panel__row--unread" : ""}`}
            onClick={() => {
              onMarkRead([f.id]);
              onClose();
            }}
          >
            <span className="alerts-panel__dot" aria-hidden="true" />
            <span className="alerts-panel__body">
              <span className="alerts-panel__meta">
                <ModuleBadge module={f.module} /> <span className="muted mono">{formatShortDate(f.created_at)}</span>
              </span>
              <span className="cell-title">{f.title ?? `Finding #${f.id}`}</span>
            </span>
            <RiskCell score={f.score} />
          </Link>
        );
      })}
    </div>
  );
}
