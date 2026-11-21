import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";

export default function Calibration() {
  const [module, setModule] = useState("m1");
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ["calibration", module],
    queryFn: () => api.getCalibration(module),
  });

  async function handleThresholdChange(value: number) {
    await api.setThreshold(module, value);
    queryClient.invalidateQueries({ queryKey: ["calibration", module] });
  }

  async function handleRetrain() {
    await api.retrain(module);
  }

  return (
    <div>
      <h2>{pl["nav.calibration"]}</h2>
      <div className="card">
        <select value={module} onChange={(e) => setModule(e.target.value)}>
          <option value="m1">M1</option>
          <option value="m2">M2</option>
          <option value="m3">M3</option>
        </select>

        {data && (
          <>
            <div style={{ margin: "1rem 0" }}>
              <label>
                {pl["calibration.threshold"]}: {data.threshold.toFixed(2)}
              </label>
              <br />
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={data.threshold}
                onChange={(e) => handleThresholdChange(Number(e.target.value))}
                style={{ width: "100%" }}
              />
            </div>
            <p>
              {pl["calibration.precision"]}: {(data.precision * 100).toFixed(1)}% &nbsp;
              {pl["calibration.recall"]}: {(data.recall * 100).toFixed(1)}% &nbsp;
              FP: {data.false_positives} &nbsp; FN: {data.false_negatives}
            </p>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data.pr_curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="threshold" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Line type="monotone" dataKey="precision" stroke="#2563eb" dot={false} />
                <Line type="monotone" dataKey="recall" stroke="#16a34a" dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <button className="btn" onClick={handleRetrain}>
              {pl["calibration.retrain"]}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
