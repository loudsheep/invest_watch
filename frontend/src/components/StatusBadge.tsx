import { statusLabel } from "../lib/modules";

export default function StatusBadge({ status }: { status: string }) {
  return <span className={`status-badge status-badge--${status}`}><span className="status-badge__text">{statusLabel(status)}</span></span>;
}
