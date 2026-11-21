import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import SoonTag from "../components/SoonTag";
import { api, type CalibrationMetrics } from "../lib/api";
import { MODULES, moduleInfo } from "../lib/modules";

const MIN_LABELS = 10;

function fmt(value: number, digits = 2): string {
  return value.toFixed(digits).replace(".", ",");
}

function bestF1(curve: CalibrationMetrics["pr_curve"]) {
  let best: { threshold: number; f1: number } | null = null;
  curve.forEach((p) => {
    const f1 = p.precision + p.recall === 0 ? 0 : (2 * p.precision * p.recall) / (p.precision + p.recall);
    if (!best || f1 > best.f1) best = { threshold: p.threshold, f1 };
  });
  return best as { threshold: number; f1: number } | null;
}

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
  const curve = [...(data?.pr_curve ?? [])].sort((a, b) => a.recall - b.recall);
  const atThreshold = curve.reduce<(typeof curve)[number] | null>(
    (nearest, p) => (!nearest || Math.abs(p.threshold - threshold) < Math.abs(nearest.threshold - threshold) ? p : nearest),
    null,
  );
  const suggested = data ? bestF1(data.pr_curve) : null;
  const moduleName = moduleInfo(module).short;

  return (
    <>
      <div className="page__header">
        <div>
          <h1 className="page__title">{pl["calibration.title"]}</h1>
          <p className="page__sub">{pl["calibration.lede"]}</p>
        </div>
        <div className="calib-actions">
          <span className="muted mono calib-actions__meta">
            etykiety: {data?.labeled ?? "-"} (potwierdzone: {data?.positives ?? "-"})
          </span>
          <button className="btn btn--primary" disabled={!isAdmin || retrain.isPending} onClick={() => retrain.mutate()}>
            {retrain.isPending ? `${pl["calibration.retrain"]}...` : pl["calibration.retrain"]}
          </button>
        </div>
      </div>

      <div className="segmented" role="group" aria-label={pl["common.module"]}>
        {MODULES.map((m) => (
          <button
            key={m.id}
            className={`segmented__item${module === m.id ? " segmented__item--on" : ""}`}
            aria-pressed={module === m.id}
            onClick={() => {
              setModule(m.id);
              setDraft(null);
            }}
          >
            <ModuleBadge module={m.id} /> {m.name}
          </button>
        ))}
      </div>

      {!isAdmin && me.isSuccess && <p className="muted">{pl["calibration.adminOnly"]}</p>}
      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}
      {setThreshold.isError && <QueryError message="Nie udało się zapisać progu." onRetry={() => draft !== null && setThreshold.mutate(draft)} />}
      {retrain.isError && <QueryError message="Nie udało się uruchomić trenowania." onRetry={() => retrain.mutate()} />}
      {retrain.isSuccess && (
        <p className="saved" role="status">
          {pl["calibration.retrainStarted"]}
        </p>
      )}

      {data && data.labeled < MIN_LABELS && (
        <div className="notice" role="status">
          <p className="notice__text">
            Za mało etykiet, żeby policzyć precyzję i czułość ({data.labeled} z {MIN_LABELS}). Oznacz findingi tego modułu jako
            Potwierdzony lub Odrzucony w widoku findingu. Do tego czasu metryki i krzywa poniżej są tylko wartościami domyślnymi.
          </p>
        </div>
      )}

      {data && (
        <>
          <div className="row-split">
            <section className="panel row-split__main">
              <div className="panel__head">
                <h2>
                  {pl["calibration.curve"]} · {moduleName}
                </h2>
                <span className="muted mono">punkt pracy dla progu {fmt(threshold)}</span>
              </div>
              <div className="panel__body">
                <div className="legend">
                  <span className="legend__item">
                    <span className="legend__line" style={{ background: "var(--brand)" }} /> model aktualny
                  </span>
                  <span className="legend__item is-soon">
                    <span className="legend__line legend__line--dashed" /> poprzedni model <SoonTag />
                  </span>
                </div>
                <ResponsiveContainer width="100%" height={340}>
                  <AreaChart data={curve}>
                    <CartesianGrid stroke="#d8dce4" />
                    <XAxis
                      dataKey="recall"
                      type="number"
                      domain={[0, 1]}
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }}
                      label={{ value: "Czułość (recall)", position: "insideBottom", offset: -4, fontSize: 11 }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      tickLine={false}
                      axisLine={false}
                      width={32}
                      tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }}
                    />
                    <Tooltip formatter={(v: number) => fmt(v)} />
                    <Area type="monotone" dataKey="precision" name={pl["calibration.precision"]} stroke="#2340d8" strokeWidth={2} fill="#e3e8fc" />
                    {atThreshold && <ReferenceDot x={atThreshold.recall} y={atThreshold.precision} r={5} fill="#fff" stroke="#2340d8" strokeWidth={2} />}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            <div className="row-split__side">
              <section className="panel">
                <div className="panel__head">
                  <h2>Próg wysokiego ryzyka · {moduleName}</h2>
                </div>
                <div className="panel__body">
                  <div className="threshold-row">
                    <span className="threshold-big">{fmt(threshold)}</span>
                    {suggested && (
                      <span className="threshold-hint">
                        <strong>sugerowany: {fmt(suggested.threshold)}</strong>
                        <span className="muted mono">maks. F1 = {fmt(suggested.f1)}</span>
                      </span>
                    )}
                  </div>
                  <div className="is-soon calib-hist" title="Wymaga rozkładu score wg decyzji analityków w API">
                    rozkład score: potwierdzone / odrzucone <SoonTag />
                  </div>
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
                    aria-label={pl["calibration.threshold"]}
                    onChange={(e) => setDraft(Number(e.target.value))}
                    onPointerUp={() => draft !== null && setThreshold.mutate(draft)}
                    onKeyUp={() => draft !== null && setThreshold.mutate(draft)}
                  />
                </div>
              </section>

              <section className="panel stat-grid">
                <div className="stat-grid__cell">
                  <span className="kpi__label">{pl["calibration.precision"]}</span>
                  <span className="kpi__value">{fmt(data.precision)}</span>
                </div>
                <div className="stat-grid__cell">
                  <span className="kpi__label">{pl["calibration.recall"]}</span>
                  <span className="kpi__value">{fmt(data.recall)}</span>
                </div>
                <div className="stat-grid__cell">
                  <span className="kpi__label">{pl["calibration.falsePositives"]}</span>
                  <span className="kpi__value kpi__value--high">{data.false_positives}</span>
                  <span className="kpi__note">FP · odrzucone mimo zgłoszenia</span>
                </div>
                <div className="stat-grid__cell">
                  <span className="kpi__label">{pl["calibration.falseNegatives"]}</span>
                  <span className="kpi__value kpi__value--critical">{data.false_negatives}</span>
                  <span className="kpi__note">FN · potwierdzone poniżej progu</span>
                </div>
              </section>
            </div>
          </div>

          <section className="panel is-soon">
            <div className="panel__head">
              <h2>
                Wersje modelu <SoonTag />
              </h2>
              <span className="muted">Przetrenowanie podbija model_version, a decyzje analityka trafiają do zbioru etykiet</span>
            </div>
            <div className="table-head micro">
              <span className="col-grow">Wersja</span>
              <span className="col-grow">Data</span>
              <span className="col-grow">Etykiety</span>
              <span className="col-grow">Precyzja</span>
              <span className="col-grow">Czułość</span>
              <span className="col-grow">Uwagi</span>
            </div>
            <p className="empty">Brak endpointu z historią wersji modelu.</p>
          </section>
        </>
      )}
    </>
  );
}
