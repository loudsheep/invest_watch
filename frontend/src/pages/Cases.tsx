import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

interface CaseRow {
  id: number;
  primary_entity_id: number;
  status: string;
  description: string | null;
}

export default function Cases() {
  const { data } = useQuery({ queryKey: ["cases"], queryFn: () => api.listCases() as Promise<CaseRow[]> });

  return (
    <div>
      <h2>Case&apos;y</h2>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Podmiot</th>
              <th>Status</th>
              <th>Opis</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((c) => (
              <tr key={c.id}>
                <td>#{c.id}</td>
                <td>{c.primary_entity_id}</td>
                <td>{c.status}</td>
                <td>{c.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
