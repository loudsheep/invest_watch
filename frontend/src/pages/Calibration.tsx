import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import { api, type CalibrationMetrics } from "../lib/api";
import { MODULES, formatDate, moduleInfo } from "../lib/modules";

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

  const quality = useQuery({ queryKey: ["quality", module], queryFn: () => api.modelQuality(module) });
  const uncertain = useQuery({ queryKey: ["uncertain", module], queryFn: () => api.uncertainFindings(module) });
  const decide = useMutation({
    mutationFn: ({ id, status }: { id: number; status: "confirmed" | "dismissed" }) => api.updateFindingStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uncertain", module] });
      queryClient.invalidateQueries({ queryKey: ["quality", module] });
      queryClient.invalidateQueries({ queryKey: ["calibration", module] });
      queryClient.invalidateQueries({ queryKey: ["findings"] });
    },
  });

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

          {quality.data && (
            <div className="row-split">
              <section className="panel row-split__main">
                <div className="panel__head">
                  <h2>Jakość modelu przy progu {fmt(quality.data.threshold)}</h2>
                  <span className="muted">na ocenach analityka</span>
                </div>
                <div className="panel__body">
                  <div className="confusion">
                    <span />
                    <span className="micro">model: zgłasza</span>
                    <span className="micro">model: pomija</span>
                    <span className="micro">analityk: potwierdził</span>
                    <span className="confusion__cell confusion__cell--good">{quality.data.matrix.tp}<small>trafne (TP)</small></span>
                    <span className="confusion__cell confusion__cell--bad">{quality.data.matrix.fn}<small>pominięte (FN)</small></span>
                    <span className="micro">analityk: odrzucił</span>
                    <span className="confusion__cell confusion__cell--bad">{quality.data.matrix.fp}<small>fałszywe alarmy (FP)</small></span>
                    <span className="confusion__cell confusion__cell--good">{quality.data.matrix.tn}<small>trafnie pominięte (TN)</small></span>
                  </div>
                  <p className="micro">rozkład wyniku wg decyzji analityków</p>
                  <ResponsiveContainer width="100%" height={140}>
                    <BarChart data={quality.data.histogram.map((b) => ({ ...b, label: fmt(b.from, 1) }))}>
                      <CartesianGrid vertical={false} stroke="#d8dce4" />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={24} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Bar dataKey="confirmed" name="potwierdzone" stackId="a" fill="#16a34a" isAnimationActive={false} />
                      <Bar dataKey="dismissed" name="odrzucone" stackId="a" fill="#dc2626" isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
              <section className="panel row-split__side">
                <div className="panel__head">
                  <h2>Wersje modelu</h2>
                  <span className="muted">metryki z walidacji krzyżowej</span>
                </div>
                {quality.data.runs.length === 0 && <p className="empty">Brak treningów. Oceń findingi i użyj "Przetrenuj model".</p>}
                {quality.data.runs.map((run) => (
                  <div className="table-row" key={run.version}>
                    <span className="col-grow">
                      <p className="cell-id">wersja {run.version}</p>
                      <p className="muted mono">
                        {formatDate(run.created_at)} · {run.labels} etykiet ({run.positives} pozytywnych)
                      </p>
                    </span>
                    <span className="mono">
                      {run.metrics
                        ? `P ${fmt(run.metrics.precision)} · R ${fmt(run.metrics.recall)} · F1 ${fmt(run.metrics.f1)}`
                        : "za mało danych"}
                    </span>
                  </div>
                ))}
              </section>
            </div>
          )}

          <section className="panel">
            <div className="panel__head">
              <h2>Do oceny w pierwszej kolejności</h2>
              <span className="muted">Findingi najbliższe progowi: Twoja decyzja najmocniej poprawi metryki</span>
            </div>
            {uncertain.data?.length === 0 && <p className="empty">Wszystkie findingi tego modułu mają już ocenę.</p>}
            {uncertain.data?.map((f) => (
              <div className="table-row" key={f.id}>
                <span className="col-grow">
                  <Link to={`/findings/${f.id}`}>{f.title || f.url}</Link>
                  <p className="muted mono">
                    wynik {fmt(f.score)} · odległość od progu {fmt(f.distance)}
                  </p>
                </span>
                <button
                  className="btn btn--primary btn--small"
                  disabled={decide.isPending}
                  onClick={() => decide.mutate({ id: f.id, status: "confirmed" })}
                >
                  Potwierdź
                </button>
                <button
                  className="btn btn--secondary btn--small"
                  disabled={decide.isPending}
                  onClick={() => decide.mutate({ id: f.id, status: "dismissed" })}
                >
                  Odrzuć
                </button>
              </div>
            ))}
          </section>
        </>
      )}
    </>
  );
}
