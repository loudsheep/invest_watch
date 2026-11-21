import pl from "../i18n/pl.json";

export const HIGH_RISK = 0.8;

export interface ModuleInfo {
  id: "m1" | "m2" | "m3";
  short: string;
  name: string;
  color: string;
}

export const MODULES: ModuleInfo[] = [
  { id: "m1", short: "M1", name: "Finfluencerzy", color: "#1d6e7a" },
  { id: "m2", short: "M2", name: "Informacja o ryzyku", color: "#b06f12" },
  { id: "m3", short: "M3", name: "Shadow advisory", color: "#7b3a6b" },
];

export const STATUSES = ["new", "in_review", "confirmed", "dismissed", "escalated"] as const;

const labels = pl as Record<string, string>;

export function moduleInfo(id: string): ModuleInfo {
  return MODULES.find((m) => m.id === id) ?? { id: "m1", short: id.toUpperCase(), name: id, color: "#4b5f68" };
}

export function statusLabel(status: string): string {
  return labels[`findings.status.${status}`] ?? status;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
