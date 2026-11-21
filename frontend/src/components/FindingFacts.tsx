import pl from "../i18n/pl.json";
import type { FindingDetail } from "../lib/api";

interface Criterion {
  id: string;
  description: string;
  legal_basis: string;
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

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

export function quotesFor(data: FindingDetail): string[] {
  const d = data.details as Details;
  const llm = (d.llm ?? {}) as Details;
  return [...list(d.affiliate_evidence), ...list(d.advisory_offer_evidence), ...list(llm.profit_claims), ...list(llm.risk_statements)];
}

function Entities({ data }: { data: FindingDetail }) {
  return (
    <section>
      <h2 className="section__title">{pl["finding.entities"]}</h2>
      {data.mentions.length === 0 ? (
        <p className="empty">{pl["finding.entities.empty"]}</p>
      ) : (
        <ul className="facts">
          {data.mentions.map((m) => (
            <li key={`${m.entity_id}-${m.role}`}>
              <strong>{m.entity_name}</strong>
              <span className="facts__meta">
                {m.role}, {m.authorized === null ? pl["finding.entity.unknown"] : m.authorized ? pl["finding.entity.authorized"] : pl["finding.entity.unauthorized"]}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function M1({ data }: { data: FindingDetail }) {
  const d = data.details as Details;
  const disclosed = Boolean(d.has_cooperation_disclosure);
  const affiliate = list(d.affiliate_evidence);
  return (
    <>
      <section>
        <h2 className="section__title">{pl["finding.m1.title"]}</h2>
        <dl className="facts facts--grid">
          <dt>{pl["finding.m1.promo"]}</dt>
          <dd>{d.promo_code ? <code>{String(d.promo_code)}</code> : "-"}</dd>
          <dt>{pl["finding.m1.affiliate"]}</dt>
          <dd>{affiliate.length ? affiliate.map((a) => <code key={a}>{a}</code>) : "-"}</dd>
          <dt>{pl["finding.m1.disclosure"]}</dt>
          <dd className={disclosed ? "" : "facts__bad"}>{disclosed ? pl["finding.m1.disclosed"] : pl["finding.m1.undisclosed"]}</dd>
        </dl>
      </section>
      <Entities data={data} />
    </>
  );
}

function M2({ data }: { data: FindingDetail }) {
  const d = data.details as Details;
  const criteria = (d.criteria as Criterion[] | undefined) ?? [];
  const fonts = d.font_comparison as FontComparison | null | undefined;
  return (
    <>
      {fonts && (
        <section>
          <h2 className="section__title">{pl["finding.m2.fonts"]}</h2>
          <div className="fonts">
            <div className="fonts__box">
              <span className="fonts__label">{pl["finding.m2.profitFont"]}</span>
              {fonts.profit_px ? (
                <span className="fonts__sample" style={{ fontSize: Math.min(fonts.profit_px, 64) }}>
                  {fonts.profit_text ?? "Zysk"} <small>{fonts.profit_px}px</small>
                </span>
              ) : (
                <span className="empty">{pl["finding.m2.noProfit"]}</span>
              )}
            </div>
            <div className="fonts__box">
              <span className="fonts__label">{pl["finding.m2.riskFont"]}</span>
              <span className="fonts__sample" style={{ fontSize: Math.min(fonts.risk_px, 64) }}>
                {fonts.risk_text ?? "Ryzyko"} <small>{fonts.risk_px}px</small>
              </span>
            </div>
          </div>
          {fonts.ratio !== undefined && (
            <p className={fonts.ratio < 0.8 ? "facts__bad" : ""}>
              {pl["finding.m2.ratio"]}: {fonts.ratio}
            </p>
          )}
        </section>
      )}
      <section>
        <h2 className="section__title">{pl["finding.m2.title"]}</h2>
        <ul className="criteria">
          {criteria.map((c) => (
            <li key={c.id} className={c.score >= 0.5 ? "criteria__ok" : "criteria__fail"}>
              <span className="criteria__score">{Math.round(c.score * 100)}%</span>
              <span className="criteria__body">
                <strong>{c.description}</strong>
                <span className="facts__meta">
                  {pl["finding.m2.legalBasis"]}: {c.legal_basis}
                </span>
                {c.evidence && <code>{c.evidence}</code>}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

function M3({ data }: { data: FindingDetail }) {
  const d = data.details as Details;
  const offer = list(d.advisory_offer_evidence);
  const lookalike = d.lookalike_domain as { suspected_domain: string; mimics_entity: string; mimics_domain: string; similarity: number } | null;
  return (
    <>
      <section>
        <h2 className="section__title">{pl["finding.m3.title"]}</h2>
        <dl className="facts facts--grid">
          <dt>{pl["finding.m3.offer"]}</dt>
          <dd>{offer.length ? offer.map((o) => <code key={o}>{o}</code>) : "-"}</dd>
          <dt>{pl["finding.m3.lookalike"]}</dt>
          <dd>
            {lookalike ? (
              <>
                <code>{lookalike.suspected_domain}</code> {pl["finding.m3.mimics"]} {lookalike.mimics_entity} (<code>{lookalike.mimics_domain}</code>, {lookalike.similarity}%)
              </>
            ) : (
              "-"
            )}
          </dd>
        </dl>
      </section>
      <Entities data={data} />
    </>
  );
}

export default function FindingFacts({ data }: { data: FindingDetail }) {
  if (data.module === "m1") return <M1 data={data} />;
  if (data.module === "m2") return <M2 data={data} />;
  if (data.module === "m3") return <M3 data={data} />;
  return null;
}
