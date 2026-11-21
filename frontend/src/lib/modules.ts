import pl from "../i18n/pl.json";

export const HIGH_RISK = 0.8;
export const CRITICAL_RISK = 0.9;
export const MEDIUM_RISK = 0.5;

export type RiskBand = "low" | "medium" | "high" | "critical";

export interface ModuleInfo {
  id: "m1" | "m2" | "m3";
  short: string;
  name: string;
  color: string;
}

export const MODULES: ModuleInfo[] = [
  { id: "m1", short: "Finfluencer", name: "Reklamy finfluencerów", color: "#0e1424" },
  { id: "m2", short: "Ryzyko", name: "Zgodność informacji o ryzyku", color: "#2340d8" },
  { id: "m3", short: "Bez licencji", name: "Doradztwo bez zezwolenia", color: "#6f86e8" },
];

export const STATUSES = ["new", "in_review", "confirmed", "dismissed", "escalated"] as const;

const labels = pl as Record<string, string>;

export function moduleInfo(id: string): ModuleInfo {
  return MODULES.find((m) => m.id === id) ?? { id: "m1", short: id.toUpperCase(), name: id, color: "#0e1424" };
}

export function riskBand(score: number): RiskBand {
  if (score >= CRITICAL_RISK) return "critical";
  if (score >= HIGH_RISK) return "high";
  if (score >= MEDIUM_RISK) return "medium";
  return "low";
}

export function statusLabel(status: string): string {
  return labels[`findings.status.${status}`] ?? status;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function formatShortDate(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
  }
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "wczoraj";
  return date.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit" });
}
