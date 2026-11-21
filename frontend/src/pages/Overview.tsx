import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";

export default function Overview() {
  const trendQuery = useQuery({ queryKey: ["trend"], queryFn: api.findingsTrend });
  const countersQuery = useQuery({ queryKey: ["counters"], queryFn: api.findingsCounters });

  const trendData = (trendQuery.data || []).reduce<Record<string, Record<string, number | string>>>((acc, row) => {
    acc[row.day] = acc[row.day] || { day: row.day };
    acc[row.day][row.module] = row.count;
    return acc;
  }, {});

  return (
    <div>
      <h2>{pl["overview.title"]}</h2>
      <div className="grid-2">
        <div className="card">
          <h3>{pl["overview.trend"]}</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={Object.values(trendData)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="m1" stroke="#1e40af" />
              <Line type="monotone" dataKey="m2" stroke="#92400e" />
              <Line type="monotone" dataKey="m3" stroke="#991b1b" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>{pl["overview.counters"]}</h3>
          {countersQuery.data && (
            <ul>
              {Object.entries(countersQuery.data.by_module).map(([module, count]) => (
                <li key={module}>
                  {module.toUpperCase()}: {count}
                </li>
              ))}
              <li>
                <strong>{pl["overview.highRisk"]}:</strong> {countersQuery.data.high_risk}
              </li>
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
