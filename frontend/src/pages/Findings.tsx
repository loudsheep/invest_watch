import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";

export default function Findings() {
  const [module, setModule] = useState("");
  const [status, setStatus] = useState("");
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ["findings", module, status],
    queryFn: () => api.listFindings({ module: module || undefined, status: status || undefined }),
  });

  async function changeStatus(id: number, newStatus: string) {
    await api.updateFindingStatus(id, newStatus);
    queryClient.invalidateQueries({ queryKey: ["findings"] });
  }

  return (
    <div>
      <h2>{pl["findings.title"]}</h2>
      <div className="card">
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
          <select value={module} onChange={(e) => setModule(e.target.value)}>
            <option value="">{pl["findings.filter.module"]}</option>
            <option value="m1">M1</option>
            <option value="m2">M2</option>
            <option value="m3">M3</option>
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{pl["findings.filter.status"]}</option>
            <option value="new">{pl["findings.status.new"]}</option>
            <option value="in_review">{pl["findings.status.in_review"]}</option>
            <option value="confirmed">{pl["findings.status.confirmed"]}</option>
            <option value="dismissed">{pl["findings.status.dismissed"]}</option>
            <option value="escalated">{pl["findings.status.escalated"]}</option>
          </select>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Moduł</th>
              <th>Score</th>
              <th>Status</th>
              <th>Data</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((finding) => (
              <tr key={finding.id}>
                <td>
                  <Link to={`/findings/${finding.id}`}>#{finding.id}</Link>
                </td>
                <td>
                  <span className={`badge badge-${finding.module}`}>{finding.module.toUpperCase()}</span>
                </td>
                <td>{finding.score.toFixed(2)}</td>
                <td>{finding.status}</td>
                <td>{new Date(finding.created_at).toLocaleString("pl-PL")}</td>
                <td>
                  <select value={finding.status} onChange={(e) => changeStatus(finding.id, e.target.value)}>
                    <option value="new">{pl["findings.status.new"]}</option>
                    <option value="in_review">{pl["findings.status.in_review"]}</option>
                    <option value="confirmed">{pl["findings.status.confirmed"]}</option>
                    <option value="dismissed">{pl["findings.status.dismissed"]}</option>
                    <option value="escalated">{pl["findings.status.escalated"]}</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
