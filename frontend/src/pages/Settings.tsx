import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Loading from "../components/Loading";
import QueryError from "../components/QueryError";
import { api } from "../lib/api";
import { formatDate } from "../lib/modules";

const SOURCE_LABELS: Record<string, string> = {
  "open-web": "Otwarty internet (SearXNG, strony firm z rejestru)",
  youtube: "YouTube",
  tiktok: "TikTok",
  "demo-sites": "Strony demo (lokalne)",
  dataset: "Dataset z pendrive'a",
};

const REGISTRY_LABELS: Record<string, string> = {
  knf: "KNF: firmy inwestycyjne i banki",
  knf_branch: "KNF: oddziały firm zagranicznych",
  esma_passport: "Firmy UE z paszportem (rejestr notyfikacji)",
  knf_warning: "Lista ostrzeżeń publicznych KNF",
};

const PROVIDER_LABELS: Record<string, string> = {
  knf_investment_firms: "Domy maklerskie",
  knf_brokerage_banks: "Banki z działalnością maklerską",
  knf_foreign_branches: "Oddziały zagranicznych firm",
  knf_foreign_notified: "Zagraniczne firmy bez oddziału",
  knf_warnings: "Ostrzeżenia publiczne",
};

export default function Settings() {
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });
  const isAdmin = me.data?.role === "admin";
  const { data, isError, isPending, refetch } = useQuery({ queryKey: ["settings"], queryFn: api.getSettings });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["settings"] });
  const toggleSource = useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) => api.updateSource(name, enabled),
    onSuccess: refresh,
  });
  const updateSetting = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => api.updateSetting(key, value),
    onSuccess: refresh,
  });
  const runSource = useMutation({ mutationFn: (name: string) => api.runSource(name), onSuccess: refresh });
  const sync = useMutation({
    mutationFn: api.syncRegistry,
    onSuccess: () => window.setTimeout(refresh, 8000),
  });

  return (
    <>
      <div className="page__header">
        <div>
          <h1 className="page__title">Ustawienia</h1>
          <p className="page__sub">
            Źródła danych, reguły wyciszania i rejestr podmiotów.
            {!isAdmin && me.isSuccess && " Zmiany wymagają roli admin."}
          </p>
        </div>
      </div>

      {isPending && <Loading />}
      {isError && <QueryError onRetry={() => refetch()} />}

      {data && (
        <>
          <section className="panel">
            <div className="panel__head">
              <h2>Źródła danych</h2>
              <span className="muted">Wyłączone źródło nie jest crawlowane przez scheduler</span>
            </div>
            {data.sources.map((source) => (
              <div className="table-row" key={source.name}>
                <span className="col-grow">
                  <p className="cell-id">{source.name}</p>
                  <p className="muted">{SOURCE_LABELS[source.name] ?? source.type}</p>
                </span>
                <span className="col-crawl mono muted">
                  {source.last_crawl_at ? formatDate(source.last_crawl_at) : "jeszcze nie crawlowano"}
                </span>
                <button
                  className="btn btn--secondary btn--small"
                  disabled={!isAdmin || !source.enabled || runSource.isPending}
                  onClick={() => runSource.mutate(source.name)}
                >
                  Uruchom teraz
                </button>
                <label className="col-health">
                  <input
                    type="checkbox"
                    checked={source.enabled}
                    disabled={!isAdmin || toggleSource.isPending}
                    onChange={(e) => toggleSource.mutate({ name: source.name, enabled: e.target.checked })}
                  />{" "}
                  {source.enabled ? "Włączone" : "Wyłączone"}
                </label>
              </div>
            ))}
          </section>

          <section className="panel">
            <div className="panel__head">
              <h2>Reguły wyciszania</h2>
            </div>
            <div className="table-row">
              <span className="col-grow">
                <p className="cell-id">M3: pomijaj strony autoryzowanych firm</p>
                <p className="muted">
                  Strona na zarejestrowanej domenie firmy z rejestru nie tworzy findingu M3. Lookalike domeny są nadal zgłaszane.
                </p>
              </span>
              <label className="col-health">
                <input
                  type="checkbox"
                  checked={data.settings.m3_suppress_authorized_domains}
                  disabled={!isAdmin || updateSetting.isPending}
                  onChange={(e) => updateSetting.mutate({ key: "m3_suppress_authorized_domains", value: e.target.checked })}
                />{" "}
                {data.settings.m3_suppress_authorized_domains ? "Włączone" : "Wyłączone"}
              </label>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <h2>Rejestr podmiotów</h2>
              <button className="btn btn--secondary" disabled={!isAdmin || sync.isPending} onClick={() => sync.mutate()}>
                {sync.isPending ? "Zlecanie..." : "Synchronizuj teraz"}
              </button>
            </div>
            <div className="panel__body">
              <p>
                Autoryzowanych: <b>{data.registry.authorized}</b> · z listy ostrzeżeń: <b>{data.registry.unauthorized}</b>
              </p>
              {Object.entries(data.registry.entities_by_source).map(([source, count]) => (
                <p className="muted" key={source}>
                  {REGISTRY_LABELS[source] ?? source}: {count}
                </p>
              ))}
              {sync.isSuccess && <p role="status">Synchronizacja zlecona, wyniki pojawią się za kilkanaście sekund.</p>}
            </div>
            {data.registry.last_sync ? (
              <>
                <div className="table-head micro">
                  <span className="col-grow">Lista KNF</span>
                  <span className="col-docs">Rekordy</span>
                  <span className="col-health">Pochodzenie</span>
                </div>
                {Object.entries(data.registry.last_sync.providers).map(([name, info]) => (
                  <div className="table-row" key={name}>
                    <span className="col-grow cell-id">{PROVIDER_LABELS[name] ?? name}</span>
                    <span className="col-docs mono">{info.records}</span>
                    <span className="col-health">
                      <span className={`dot-label${info.origin === "live" ? " dot-label--ok" : " dot-label--off"}`}>
                        {info.origin === "live" ? "Pobrane na żywo" : "Snapshot z repozytorium"}
                      </span>
                    </span>
                  </div>
                ))}
                <p className="muted panel__body">Ostatnia synchronizacja: {formatDate(data.registry.last_sync.at)}</p>
              </>
            ) : (
              <p className="empty">Rejestr nie był jeszcze synchronizowany.</p>
            )}
          </section>
        </>
      )}
    </>
  );
}
