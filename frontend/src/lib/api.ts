export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:47800";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export interface Finding {
  id: number;
  document_id: number;
  module: string;
  score: number;
  status: string;
  created_at: string;
  title?: string | null;
  domain?: string | null;
  entity_name?: string | null;
  platform?: string;
}

export interface Mention {
  entity_id: number;
  entity_name: string;
  role: string | null;
  authorized: boolean | null;
}

export interface FindingDetail extends Finding {
  mentions: Mention[];
  computed_styles: Record<string, unknown> | null;
  model_version: number;
  prompt_version: number;
  evidence: string | null;
  explanation: string | null;
  details: Record<string, unknown>;
  document_url: string;
  document_title: string | null;
  document_platform: string | null;
  screenshot_url: string | null;
  device_screenshots: string[];
}

export interface SimilarFinding {
  id: number;
  module: string;
  score: number;
  title: string | null;
  url: string;
  similarity: number;
}

export interface EvidenceManifest {
  document_id: number;
  url: string;
  fetched_at: string | null;
  content_hash: string;
  files: Record<string, { sha256: string; bytes: number }>;
  custody: {
    captured_at: string;
    manifest_sha256: string;
    manifest_ok: boolean;
    verified: boolean;
    files: Record<string, { sha256: string; bytes: number; status: "ok" | "modified" | "missing" }>;
  } | null;
}

export interface CaseRow {
  id: number;
  primary_entity_id: number;
  primary_entity_name: string | null;
  finding_ids: number[] | null;
  description: string | null;
  status: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "advertiser" | "entity" | "document" | "promo_code" | "domain";
  finding_id?: number;
}

export interface CaseGraph {
  nodes: GraphNode[];
  edges: { source: string; target: string; label: string }[];
}

export interface SystemHealth {
  queues: Record<string, number>;
  collectors: {
    name: string;
    type: string | null;
    enabled: boolean;
    last_crawl_at: string | null;
    schedule_seconds: number | null;
    documents: number;
  }[];
  proxies: { url: string; failures: number; circuit_open: boolean }[];
  services: { name: string; ok: boolean; latency_ms: number }[];
  activity: { t: string; documents: number; findings: number }[];
  recent_findings: { id: number; module: string; score: number; title: string | null; created_at: string }[];
}

export interface RegistrySyncSummary {
  at: string;
  created: number;
  updated: number;
  providers: Record<string, { records: number; origin: "live" | "snapshot" }>;
}

export interface AppSettings {
  settings: { m3_suppress_authorized_domains: boolean };
  sources: { name: string; type: string | null; enabled: boolean; last_crawl_at: string | null }[];
  registry: {
    entities_by_source: Record<string, number>;
    authorized: number;
    unauthorized: number;
    last_sync: RegistrySyncSummary | null;
  };
}

export interface CaseDetail {
  id: number;
  findings: { id: number; module: string; score: number; document_id: number }[];
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  role: string;
}

export interface Campaign {
  id: number;
  size: number;
  authors: string[];
  domains: string[];
  promo_codes: string[];
  modules: string[];
  max_score: number;
  first_seen: string;
  last_seen: string;
  documents: {
    document_id: number;
    title: string | null;
    url: string;
    domain: string | null;
    author: string | null;
    platform: string | null;
    fetched_at: string;
    findings: { id: number; module: string; score: number }[];
  }[];
}

export interface ModelQuality {
  threshold: number;
  matrix: { tp: number; fp: number; fn: number; tn: number };
  histogram: { from: number; confirmed: number; dismissed: number }[];
  runs: {
    version: number;
    created_at: string;
    labels: number;
    positives: number;
    metrics: { precision: number; recall: number; f1: number; folds: number } | null;
  }[];
}

export interface UncertainFinding {
  id: number;
  score: number;
  distance: number;
  title: string | null;
  url: string;
}

export interface CalibrationMetrics {
  module: string;
  threshold: number;
  precision: number;
  recall: number;
  false_positives: number;
  false_negatives: number;
  labeled: number;
  positives: number;
  pr_curve: { threshold: number; precision: number; recall: number }[];
}

export const api = {
  login: (username: string, password: string) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  me: () => request<CurrentUser | null>("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),

  listFindings: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) query.set(key, String(value));
    });
    return request<Finding[]>(`/api/findings?${query.toString()}`);
  },
  getFinding: (id: number) => request<FindingDetail>(`/api/findings/${id}`),
  updateFindingStatus: (id: number, status: string, note?: string) =>
    request<Finding>(`/api/findings/${id}/status`, { method: "PATCH", body: JSON.stringify({ status, note }) }),
  similarFindings: (id: number) => request<SimilarFinding[]>(`/api/findings/${id}/similar`),
  getEvidenceManifest: (documentId: number) => request<EvidenceManifest>(`/api/documents/${documentId}/evidence`),
  findingsTrend: () => request<{ day: string; module: string; count: number }[]>("/api/findings/trend"),
  findingsCounters: () => request<{ by_module: Record<string, number>; high_risk: number }>("/api/findings/counters"),

  listCases: () => request<CaseRow[]>("/api/cases"),
  getCase: (id: number) => request<CaseDetail>(`/api/cases/${id}`),
  getCaseGraph: (id: number) => request<CaseGraph>(`/api/cases/${id}/graph`),
  getSettings: () => request<AppSettings>("/api/settings"),
  updateSetting: (key: string, value: unknown) =>
    request(`/api/settings/${key}`, { method: "PUT", body: JSON.stringify({ value }) }),
  updateSource: (name: string, enabled: boolean) =>
    request(`/api/settings/sources/${name}`, { method: "PUT", body: JSON.stringify({ enabled }) }),
  runSource: (name: string) => request(`/api/settings/sources/${name}/run`, { method: "POST" }),
  syncRegistry: () => request("/api/settings/registry-sync", { method: "POST" }),
  systemHealth: () => request<SystemHealth>("/api/system/health"),

  listEntities: (q?: string) => request(`/api/entities${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  campaigns: (threshold: number) => request<Campaign[]>(`/api/campaigns?threshold=${threshold}`),
  modelQuality: (module: string) => request<ModelQuality>(`/api/calibration/${module}/quality`),
  uncertainFindings: (module: string) => request<UncertainFinding[]>(`/api/calibration/${module}/uncertain`),
  getCalibration: (module: string) => request<CalibrationMetrics>(`/api/calibration/${module}`),
  setThreshold: (module: string, threshold: number) =>
    request(`/api/calibration/${module}/threshold?threshold=${threshold}`, { method: "PUT" }),
  retrain: (module: string) => request(`/api/calibration/${module}/retrain`, { method: "POST" }),

  scanUrl: (url: string) => request<{ scan_id: string }>("/api/scan", { method: "POST", body: JSON.stringify({ url }) }),
};
