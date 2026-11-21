import pl from "../i18n/pl.json";
import type { FindingDetail } from "../lib/api";

interface Criterion {
  id: string;
  name?: string;
  detector?: string;
  description: string;
  legal_basis: string;
  applicable?: boolean;
  score: number;
  weight: number;
  evidence: string | null;
}

interface FontComparison {
  risk_px: number;
  risk_text?: string;
  profit_px?: number;
  profit_text?: string;
  ratio?: number;
}

type Details = Record<string, unknown>;

export interface Quote {
  label: string;
  text: string;
  tone: "claim" | "warning";
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

export function quotesFor(data: FindingDetail): Quote[] {
  const d = data.details as Details;
  const llm = (d.llm ?? {}) as Details;
  return [
    ...list(d.affiliate_evidence).map((text) => ({ label: "Link afiliacyjny", text, tone: "claim" as const })),
    ...list(d.advisory_offer_evidence).map((text) => ({ label: "Oferta doradztwa", text, tone: "claim" as const })),
    ...list(llm.profit_claims).map((text) => ({ label: "Obietnica zysku", text, tone: "claim" as const })),
    ...list(llm.risk_statements).map((text) => ({ label: "Ostrzeżenie o ryzyku", text, tone: "warning" as const })),
  ];
}

function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="metric">
      <span className="micro">{label}</span>
      <span className="metric__line">
        <span className="metric__value">{value}</span>
        {note && <span className="muted">{note}</span>}
      </span>
    </div>
  );
}

export function Metrics({ data }: { data: FindingDetail }) {
  if (data.module !== "m2") return null;
  const fonts = (data.details as Details).font_comparison as FontComparison | null | undefined;
  const ratio =
    fonts?.profit_px && fonts.risk_px ? `${(fonts.profit_px / fonts.risk_px).toFixed(1).replace(".", ",")}×` : "-";
  const criteria = ((data.details as Details).criteria as Criterion[] | undefined) ?? [];
  const find = (id: string) => criteria.find((c) => c.id === id && c.applicable !== false);
  const contrast = /contrast=([\d.]+)/.exec(find("risk_contrast")?.evidence ?? "")?.[1]?.replace(".", ",") ?? "-";
  const hidden = find("risk_hidden");
  const visibility = hidden ? (hidden.score < 0.5 ? "ukryte" : "widoczne") : "-";
  const balance = /ratio=([\d.]+)/.exec(find("profit_risk_balance")?.evidence ?? "")?.[1]?.replace(".", ",") ?? "-";
  return (
    <div className="metrics">
      <Metric
        label="Rozmiar fontu: zysk vs ostrzeżenie"
        value={ratio}
        note={fonts?.profit_px ? `${fonts.profit_px} px : ${fonts.risk_px} px` : undefined}
      />
      <Metric label="Kontrast ostrzeżenia (WCAG)" value={contrast} />
      <Metric label="Widoczność ostrzeżenia" value={visibility} />
      <Metric label="Proporcja zysk : ryzyko" value={balance} />
    </div>
  );
}

export function Criteria({ data }: { data: FindingDetail }) {
  const d = data.details as Details;
  const criteria = (d.criteria as Criterion[] | undefined) ?? [];
  if (data.module !== "m2" || criteria.length === 0) return null;
  const applicable = criteria.filter((c) => c.applicable !== false);
  const failed = applicable.filter((c) => c.score < 0.5).length;
  const change = d.change_detection as { removed_risk_statements: string[]; previous_fetched_at?: string } | null | undefined;
  return (
    <section className="panel">
      <div className="panel__head">
        <h2>Kryteria zgodności i podstawa prawna</h2>
        <span className={failed ? "text-critical" : "muted"}>
          {failed} z {applicable.length} niespełnionych
        </span>
      </div>
      {change && (
        <div className="panel__body">
          <p className="text-critical">Wykryto zmianę przy ponownym crawlu: usunięto informację o ryzyku.</p>
          {change.removed_risk_statements.map((statement) => (
            <p className="muted" key={statement}>
              „{statement}”
            </p>
          ))}
        </div>
      )}
      <div className="table-head micro">
        <span className="col-grow">Kryterium</span>
        <span className="col-detector">Detektor</span>
        <span className="col-basis">Podstawa prawna</span>
        <span className="col-weight">Waga</span>
        <span className="col-result">Wynik</span>
      </div>
      {criteria.map((c) => {
        const na = c.applicable === false;
        const ok = na || c.score >= 0.5;
        return (
          <div className="table-row" key={c.id}>
            <span className="col-grow">
              <p className="cell-id">{c.name ?? c.id}</p>
              <p className="muted">{c.description}</p>
            </span>
            <span className="col-detector mono muted">{c.detector ?? "-"}</span>
            <span className="col-basis">{c.legal_basis}</span>
            <span className="col-weight mono">{c.weight.toFixed(2).replace(".", ",")}</span>
            <span className="col-result">
              <span className={`verdict-pill ${na ? "verdict-pill--na" : ok ? "verdict-pill--ok" : "verdict-pill--fail"}`}>
                {na ? pl["finding.m2.notApplicable"] : ok ? "Spełnione" : "Niespełnione"}
              </span>
            </span>
          </div>
        );
      })}
    </section>
  );
}

export function ModuleFacts({ data }: { data: FindingDetail }) {
  const d = data.details as Details;
  if (data.module === "m1") {
    const disclosed = Boolean(d.has_cooperation_disclosure);
    const affiliate = list(d.affiliate_evidence);
    return (
      <section className="panel">
        <div className="panel__head">
          <h2>{pl["finding.m1.title"]}</h2>
        </div>
        <dl className="facts">
          <dt>{pl["finding.m1.promo"]}</dt>
          <dd>{d.promo_code ? <code>{String(d.promo_code)}</code> : "-"}</dd>
          <dt>{pl["finding.m1.affiliate"]}</dt>
          <dd>{affiliate.length ? affiliate.map((a) => <code key={a}>{a}</code>) : "-"}</dd>
          <dt>{pl["finding.m1.disclosure"]}</dt>
          <dd className={disclosed ? "" : "text-critical"}>{disclosed ? pl["finding.m1.disclosed"] : pl["finding.m1.undisclosed"]}</dd>
        </dl>
      </section>
    );
  }
  if (data.module === "m3") {
    const offer = list(d.advisory_offer_evidence);
    const lookalike = d.lookalike_domain as {
      suspected_domain: string;
      mimics_entity: string;
      mimics_domain: string;
      similarity: number;
    } | null;
    return (
      <section className="panel">
        <div className="panel__head">
          <h2>{pl["finding.m3.title"]}</h2>
        </div>
        <dl className="facts">
          <dt>{pl["finding.m3.offer"]}</dt>
          <dd>{offer.length ? offer.map((o) => <code key={o}>{o}</code>) : "-"}</dd>
          <dt>{pl["finding.m3.lookalike"]}</dt>
          <dd>
            {lookalike ? (
              <>
                <code>{lookalike.suspected_domain}</code> {pl["finding.m3.mimics"]} {lookalike.mimics_entity} (
                <code>{lookalike.mimics_domain}</code>, {lookalike.similarity}%)
              </>
            ) : (
              "-"
            )}
          </dd>
          <dt>Wiek domeny</dt>
          <dd>
            {typeof d.domain_age_days === "number"
              ? `${d.domain_age_days} dni (${(d.domain_age_days / 365).toFixed(1).replace(".", ",")} roku)`
              : "brak danych (domena lokalna albo rejestr nie podaje daty rejestracji)"}
          </dd>
        </dl>
      </section>
    );
  }
  return null;
}

export function Entities({ data }: { data: FindingDetail }) {
  return (
    <section className="panel">
      <div className="panel__head">
        <h2>Podmiot z rejestru</h2>
      </div>
      {data.mentions.length === 0 ? (
        <p className="empty">{pl["finding.entities.empty"]}</p>
      ) : (
        data.mentions.map((m) => (
          <div className="entity" key={`${m.entity_id}-${m.role}`}>
            <div className="entity__head">
              <strong>{m.entity_name}</strong>
              {m.authorized === null ? (
                <span className="tag tag--neutral">{pl["finding.entity.unknown"]}</span>
              ) : m.authorized ? (
                <span className="tag tag--ok">{pl["finding.entity.authorized"]}</span>
              ) : (
                <span className="tag tag--critical">{pl["finding.entity.unauthorized"]}</span>
              )}
            </div>
            <dl className="kv">
              <dt>Rola</dt>
              <dd>{m.role ?? "-"}</dd>
            </dl>
          </div>
        ))
      )}
    </section>
  );
}

