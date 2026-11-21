const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
    throw new Error(`${response.status} ${response.statusText}`);
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
}

export interface FindingDetail extends Finding {
  model_version: number;
  prompt_version: number;
  evidence: string | null;
  explanation: string | null;
  details: Record<string, unknown>;
  document_url: string;
  document_title: string | null;
  document_platform: string | null;
  screenshot_url: string | null;
}

export interface CalibrationMetrics {
  module: string;
  threshold: number;
  precision: number;
  recall: number;
  false_positives: number;
  false_negatives: number;
  pr_curve: { threshold: number; precision: number; recall: number }[];
}

export const api = {
  login: (username: string, password: string) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  me: () => request("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),

  listFindings: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) query.set(key, String(value));
    });
    return request<Finding[]>(`/api/findings?${query.toString()}`);
  },
  getFinding: (id: number) => request<FindingDetail>(`/api/findings/${id}`),
  updateFindingStatus: (id: number, status: string) =>
    request<Finding>(`/api/findings/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  findingsTrend: () => request<{ day: string; module: string; count: number }[]>("/api/findings/trend"),
  findingsCounters: () => request<{ by_module: Record<string, number>; high_risk: number }>("/api/findings/counters"),

  listCases: () => request("/api/cases"),
  getCase: (id: number) => request(`/api/cases/${id}`),
  getCaseGraph: (id: number) => request(`/api/cases/${id}/graph`),

  listEntities: (q?: string) => request(`/api/entities${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  getCalibration: (module: string) => request<CalibrationMetrics>(`/api/calibration/${module}`),
  setThreshold: (module: string, threshold: number) =>
    request(`/api/calibration/${module}/threshold?threshold=${threshold}`, { method: "PUT" }),
  retrain: (module: string) => request(`/api/calibration/${module}/retrain`, { method: "POST" }),

  scanUrl: (url: string) => request<{ scan_id: string }>("/api/scan", { method: "POST", body: JSON.stringify({ url }) }),
};
