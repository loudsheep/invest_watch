import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import pl from "../i18n/pl.json";
import Loading from "../components/Loading";
import ModuleBadge from "../components/ModuleBadge";
import QueryError from "../components/QueryError";
import RiskCell from "../components/RiskCell";
import StatusBadge from "../components/StatusBadge";
import { api, type Finding } from "../lib/api";
import { MODULES, STATUSES, formatShortDate, statusLabel } from "../lib/modules";

const PLATFORMS = ["web", "youtube", "tiktok", "dataset"];
const PAGE_SIZE = 10;
const BINS = 20;

const SORTS = ["score_desc", "score_asc", "date_desc", "date_asc"] as const;
type Sort = (typeof SORTS)[number];
const FILTER_KEYS = ["module", "status", "source", "min", "max", "from", "to", "risk"];

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

function formatScore(value: number): string {
  return value.toFixed(2).replace(".", ",");
}

function csvEscape(value: string): string {
  return `"${value.replace(/"/g, '""')}"`;
}

interface CheckGroupProps {
  title: string;
  options: { value: string; label: React.ReactNode; count: number }[];
  selected: string[];
  onToggle: (value: string) => void;
}

function CheckGroup({ title, options, selected, onToggle }: CheckGroupProps) {
  return (
    <div className="filters__group">
      <span className="micro">{title}</span>
      {options.map((o) => {
        const on = selected.includes(o.value);
        return (
          <label key={o.value} className={`check${on ? " check--on" : ""}`}>
            <input type="checkbox" checked={on} onChange={() => onToggle(o.value)} />
            <span className="check__label">{o.label}</span>
            <span className="check__count">{o.count}</span>
          </label>
        );
      })}
    </div>
  );
}

export default function Findings() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const listParam = (key: string) => searchParams.get(key)?.split(",").filter(Boolean) ?? [];
  const modules = listParam("module");
  const statuses = listParam("status");
  const platforms = listParam("source");
  const minScore = Number(searchParams.get("min") ?? (searchParams.get("risk") === "high" ? 0.8 : 0));
  const maxScore = Number(searchParams.get("max") ?? 1);
  const dateFrom = searchParams.get("from") ?? "";
  const dateTo = searchParams.get("to") ?? "";
  const sortParam = searchParams.get("sort");
  const sort: Sort = SORTS.find((s) => s === sortParam) ?? "score_desc";
  const search = searchParams.get("q") ?? "";
  const page = Number(searchParams.get("page") ?? 0);

  function updateParams(changes: Record<string, string | null>) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)));
        if (!("page" in changes)) next.delete("page");
        return next;
      },
      { replace: true },
    );
  }

  const setList = (key: string) => (values: string[]) => updateParams({ [key]: values.join(",") || null });
  const setModules = setList("module");
  const setStatuses = setList("status");
  const setPlatforms = setList("source");
  const setMinScore = (value: number) => updateParams({ min: value > 0 ? String(value) : null, risk: null });
  const setMaxScore = (value: number) => updateParams({ max: value < 1 ? String(value) : null });
  const setDateFrom = (value: string) => updateParams({ from: value || null });
  const setDateTo = (value: string) => updateParams({ to: value || null });
  const setSort = (value: Sort) => updateParams({ sort: value === "score_desc" ? null : value });
  const setSearch = (value: string) => updateParams({ q: value || null });
  const setPage = (value: number) => updateParams({ page: value > 0 ? String(value) : null });

  const { data, isError, isPending, refetch } = useQuery({
    queryKey: ["findings", "list", minScore, maxScore, dateFrom, dateTo, search],
    queryFn: async () => {
      const lists = await Promise.all(
        PLATFORMS.map(async (platform) => {
          const rows = await api.listFindings({
            source_platform: platform,
            min_score: minScore > 0 ? minScore : undefined,
            max_score: maxScore < 1 ? maxScore : undefined,
            date_from: dateFrom ? `${dateFrom}T00:00:00` : undefined,
            date_to: dateTo ? `${dateTo}T23:59:59` : undefined,
            q: search || undefined,
            limit: 500,
          });
          return rows.map((row) => ({ ...row, platform }));
        }),
      );
      return lists.flat();
    },
  });

  const bulk = useMutation({
    mutationFn: (status: string) => Promise.all([...selected].map((id) => api.updateFindingStatus(id, status))),
    onSuccess: () => {
      setSelected(new Set());
      queryClient.invalidateQueries({ queryKey: ["findings"] });
      queryClient.invalidateQueries({ queryKey: ["counters"] });
    },
  });

  const all = useMemo(() => data ?? [], [data]);
  const filtered = useMemo(() => {
    const rows = all.filter(
      (f) =>
        (modules.length === 0 || modules.includes(f.module)) &&
        (statuses.length === 0 || statuses.includes(f.status)) &&
        (platforms.length === 0 || platforms.includes(f.platform ?? "")),
    );
    const factor = sort.endsWith("asc") ? 1 : -1;
    const key = (f: Finding) => (sort.startsWith("score") ? f.score : new Date(f.created_at).getTime());
    return rows.sort((a, b) => (key(a) - key(b)) * factor);
  }, [all, modules, statuses, platforms, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const rows = filtered.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const histogram = useMemo(() => {
    const bins = new Array(BINS).fill(0) as number[];
    all.forEach((f) => {
      bins[Math.min(BINS - 1, Math.floor(f.score * BINS))] += 1;
    });
    return bins;
  }, [all]);
  const maxBin = Math.max(1, ...histogram);

  function count(predicate: (f: Finding) => boolean) {
    return all.filter(predicate).length;
  }

  function clearFilters() {
    updateParams(Object.fromEntries(FILTER_KEYS.map((key) => [key, null])));
  }

  function toggleRow(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAllOnPage() {
    const allOn = rows.every((f) => selected.has(f.id));
    setSelected((prev) => {
      const next = new Set(prev);
      rows.forEach((f) => (allOn ? next.delete(f.id) : next.add(f.id)));
      return next;
    });
  }

  function exportCsv() {
    const header = ["id", "module", "score", "status", "source", "created_at"].join(",");
    const lines = filtered.map((f) =>
      [f.id, f.module, f.score, f.status, f.platform ?? "", f.created_at].map((v) => csvEscape(String(v))).join(","),
    );
    const blob = new Blob([[header, ...lines].join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "findingi.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const summary = [
    `${filtered.length} wyników`,
    modules.length ? modules.map((m) => m.toUpperCase()).join(", ") : null,
    statuses.length ? statuses.map(statusLabel).join(", ") : null,
    minScore > 0 || maxScore < 1 ? `ryzyko ${formatScore(minScore)}-${formatScore(maxScore)}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const pageAllSelected = rows.length > 0 && rows.every((f) => selected.has(f.id));

  return (
    <>
      <div className="page__header">
        <div>
          <h1 className="page__title">{pl["findings.title"]}</h1>
          <p className="page__sub">{summary}</p>
        </div>
        <button className="btn btn--secondary" onClick={exportCsv} disabled={filtered.length === 0}>
          Eksport CSV
        </button>
      </div>

      <div className="findings-layout">
        <aside className="panel filters">
          <div className="panel__head">
            <span>Filtry</span>
            <button className="linkbtn" onClick={clearFilters}>
              Wyczyść
            </button>
          </div>
          <CheckGroup
            title={pl["common.module"]}
            selected={modules}
            onToggle={(v) => setModules(toggle(modules, v))}
            options={MODULES.map((m) => ({
              value: m.id,
              label: (
                <>
                  <ModuleBadge module={m.id} /> {m.name}
                </>
              ),
              count: count((f) => f.module === m.id),
            }))}
          />
          <CheckGroup
            title={pl["common.status"]}
            selected={statuses}
            onToggle={(v) => setStatuses(toggle(statuses, v))}
            options={STATUSES.map((s) => ({ value: s, label: statusLabel(s), count: count((f) => f.status === s) }))}
          />
          <div className="filters__group">
            <span className="micro">Ryzyko (score)</span>
            <div className="histogram" aria-hidden="true">
              {histogram.map((value, index) => {
                const lower = index / BINS;
                const on = lower + 1 / BINS > minScore && lower < maxScore;
                return (
                  <span
                    key={index}
                    className={`histogram__bin${on ? " histogram__bin--on" : ""}`}
                    style={{ height: `${(value / maxBin) * 100}%` }}
                  />
                );
              })}
            </div>
            <div className="range">
              <span className="range__track" />
              <span className="range__fill" style={{ left: `${minScore * 100}%`, right: `${(1 - maxScore) * 100}%` }} />
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={minScore}
                aria-label="Ryzyko od"
                onChange={(e) => setMinScore(Math.min(Number(e.target.value), maxScore - 0.01))}
              />
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={maxScore}
                aria-label="Ryzyko do"
                onChange={(e) => setMaxScore(Math.max(Number(e.target.value), minScore + 0.01))}
              />
            </div>
            <div className="range__values">
              <span>{formatScore(minScore)}</span>
              <span>{formatScore(maxScore)}</span>
            </div>
          </div>
          <CheckGroup
            title={pl["common.source"]}
            selected={platforms}
            onToggle={(v) => setPlatforms(toggle(platforms, v))}
            options={PLATFORMS.map((p) => ({ value: p, label: p, count: count((f) => f.platform === p) }))}
          />
          <div className="filters__group">
            <span className="micro">{pl["common.date"]}</span>
            <div className="date-range">
              <input className="input input--mono" type="date" value={dateFrom} max={dateTo || undefined} onChange={(e) => setDateFrom(e.target.value)} />
              <span className="muted">-</span>
              <input className="input input--mono" type="date" value={dateTo} min={dateFrom || undefined} onChange={(e) => setDateTo(e.target.value)} />
            </div>
          </div>
        </aside>

        <div className="results">
          <div className="toolbar">
            <input
              className="input"
              placeholder="Szukaj w treści, podmiocie lub domenie"
              aria-label="Szukaj"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select className="input" value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sortowanie">
              <option value="score_desc">Sortuj: Ryzyko malejąco</option>
              <option value="score_asc">Sortuj: Ryzyko rosnąco</option>
              <option value="date_desc">Sortuj: Najnowsze</option>
              <option value="date_asc">Sortuj: Najstarsze</option>
            </select>
          </div>

          {selected.size > 0 && (
            <div className="bulk">
              <span className="bulk__count">Zaznaczono {selected.size}</span>
              <button className="btn btn--secondary" disabled={bulk.isPending} onClick={() => bulk.mutate("in_review")}>
                Przejmij do przeglądu
              </button>
              <button className="btn btn--secondary" disabled={bulk.isPending} onClick={() => bulk.mutate("dismissed")}>
                Odrzuć
              </button>
              <button className="btn btn--danger" disabled={bulk.isPending} onClick={() => bulk.mutate("escalated")}>
                Eskaluj
              </button>
            </div>
          )}

          <section className="panel">
            <div className="table-head table-head--check micro">
              <input type="checkbox" checked={pageAllSelected} onChange={toggleAllOnPage} aria-label="Zaznacz wszystkie na stronie" />
              <span className="col-id">ID</span>
              <span className="col-mod">Mod</span>
              <span className="col-grow">Treść</span>
              <span className="col-entity-sm">Podmiot</span>
              <span className="col-source">Źródło</span>
              <span className="col-risk">Ryzyko</span>
              <span className="col-status">Status</span>
              <span className="col-date-lg">Data</span>
            </div>
            {isPending && <Loading />}
            {isError && <QueryError onRetry={() => refetch()} />}
            {!isPending && !isError && rows.length === 0 && <p className="empty">{pl["findings.empty"]}</p>}
            {rows.map((f) => {
              const dim = f.status === "dismissed";
              return (
                <div
                  key={f.id}
                  className={`table-row table-row--check${selected.has(f.id) ? " table-row--selected" : ""}${dim ? " table-row--dim" : ""}`}
                >
                  <input type="checkbox" checked={selected.has(f.id)} onChange={() => toggleRow(f.id)} aria-label={`Zaznacz #${f.id}`} />
                  <span className="col-id">#{f.id}</span>
                  <span className="col-mod">
                    <ModuleBadge module={f.module} />
                  </span>
                  <Link to={`/findings/${f.id}`} state={{ listSearch: searchParams.toString() }} className="col-grow">
                    <p className="cell-title">{f.title ?? `Finding #${f.id}`}</p>
                    <p className="cell-sub">{f.domain ?? "-"}</p>
                  </Link>
                  <span className="col-entity-sm">{f.entity_name ?? "-"}</span>
                  <span className="col-source">{f.platform ?? "-"}</span>
                  <span className="col-risk">
                    <RiskCell score={f.score} />
                  </span>
                  <span className="col-status">
                    <StatusBadge status={f.status} />
                  </span>
                  <span className="col-date-lg">{formatShortDate(f.created_at)}</span>
                </div>
              );
            })}
          </section>

          <div className="pagination">
            <span>
              {filtered.length === 0 ? "0" : `${safePage * PAGE_SIZE + 1}-${safePage * PAGE_SIZE + rows.length}`} z {filtered.length}
            </span>
            <div className="pagination__buttons">
              <button className="btn btn--secondary" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>
                ← Poprzednia
              </button>
              <button className="btn btn--secondary" disabled={safePage >= pageCount - 1} onClick={() => setPage(safePage + 1)}>
                Następna →
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
