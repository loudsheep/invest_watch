import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import QueryError from "../components/QueryError";
import { api } from "../lib/api";
import { MODULES, moduleInfo } from "../lib/modules";

export default function Calibration() {
  const [module, setModule] = useState("m1");
  const [draft, setDraft] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, staleTime: Infinity });
  const isAdmin = me.data?.role === "admin";

  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ["calibration", module],
    queryFn: () => api.getCalibration(module),
  });

  const setThreshold = useMutation({
    mutationFn: (value: number) => api.setThreshold(module, value),
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: ["calibration", module] });
      setDraft(null);
    },
  });

  const retrain = useMutation({ mutationFn: () => api.retrain(module) });

  const color = moduleInfo(module).color;
  const threshold = draft ?? data?.threshold ?? 0.5;

  return (
    <>
      <h1 className="page__title">{pl["calibration.title"]}</h1>
      <p className="lede">{pl["calibration.lede"]}</p>

      <div className="chips" role="group" aria-label={pl["common.module"]}>
        <span className="chips__label">{pl["common.module"]}</span>
        {MODULES.map((m) => (
          <button
            key={m.id}
            className="chip"
            aria-pressed={module === m.id}
            onClick={() => {
              setModule(m.id);
              setDraft(null);
            }}
          >
            {m.short} {m.name}
          </button>
        ))}
      </div>

      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
      {setThreshold.isError && <QueryError message="Nie udało się zapisać progu." onRetry={() => draft !== null && setThreshold.mutate(draft)} />}
      {retrain.isError && <QueryError message="Nie udało się uruchomić trenowania." onRetry={() => retrain.mutate()} />}

      {data && (
        <div className="split split--calibration">
          <section>
            <label className="threshold" htmlFor="threshold">
              <span className="field__label">{pl["calibration.threshold"]}</span>
              <span className="threshold__value">{threshold.toFixed(2)}</span>
            </label>
            <input
              id="threshold"
              className="slider"
              style={{ accentColor: color }}
              type="range"
              disabled={!isAdmin}
              min={0}
              max={1}
              step={0.01}
              value={threshold}
              onChange={(e) => setDraft(Number(e.target.value))}
              onPointerUp={() => draft !== null && setThreshold.mutate(draft)}
              onKeyUp={() => draft !== null && setThreshold.mutate(draft)}
            />

            <dl className="metrics">
              <div>
                <dt>{pl["calibration.precision"]}</dt>
                <dd>{(data.precision * 100).toFixed(1)}%</dd>
              </div>
              <div>
                <dt>{pl["calibration.recall"]}</dt>
                <dd>{(data.recall * 100).toFixed(1)}%</dd>
              </div>
              <div>
                <dt>{pl["calibration.falsePositives"]}</dt>
                <dd>{data.false_positives}</dd>
              </div>
              <div>
                <dt>{pl["calibration.falseNegatives"]}</dt>
                <dd>{data.false_negatives}</dd>
              </div>
            </dl>

            {isAdmin ? (
              <button className="btn btn--ghost" disabled={retrain.isPending} onClick={() => retrain.mutate()}>
                {retrain.isPending ? `${pl["calibration.retrain"]}...` : pl["calibration.retrain"]}
              </button>
            ) : (
              <p className="empty">{pl["calibration.adminOnly"]}</p>
            )}
            {retrain.isSuccess && (
              <p className="saved" role="status">
                {pl["calibration.retrainStarted"]}
              </p>
            )}
          </section>

          <section>
            <h2 className="section__title">{pl["calibration.curve"]}</h2>
            <div className="chart">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={data.pr_curve}>
                  <CartesianGrid vertical={false} stroke="#c3ced2" />
                  <XAxis dataKey="threshold" type="number" domain={[0, 1]} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 1]} tickLine={false} axisLine={false} width={32} />
                  <Tooltip />
                  <ReferenceLine x={threshold} stroke="#12252d" strokeDasharray="4 3" />
                  <Line type="monotone" dataKey="precision" name={pl["calibration.precision"]} stroke={color} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="recall" name={pl["calibration.recall"]} stroke="#4b5f68" strokeWidth={2} strokeDasharray="5 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
