import { useState } from "react";
import { Link } from "react-router-dom";
import { blocksFor, type Quote } from "../lib/quotes";

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface StyledElement {
  fontSize?: string;
  text?: string;
  rect?: Rect;
}

interface Props {
  src: string;
  styles: Record<string, unknown> | null;
  quotes?: Quote[];
  preview?: { maxHeight: number; fullHref: string };
}

function elements(styles: Record<string, unknown> | null, key: string): StyledElement[] {
  const list = styles?.[key];
  return Array.isArray(list) ? (list as StyledElement[]).filter((el) => el.rect && el.rect.w > 0 && el.rect.h > 0) : [];
}

function Marked({ rect, scale, className, label }: { rect: Rect; scale: number; className: string; label: string }) {
  return (
    <span
      className={`shot-box ${className}`}
      style={{ left: rect.x * scale, top: rect.y * scale, width: rect.w * scale, height: rect.h * scale }}
    >
      <span className="shot-box__label">{label}</span>
    </span>
  );
}

export default function ShotOverlay({ src, styles, quotes = [], preview }: Props) {
  const [size, setSize] = useState({ scale: 0, height: 0 });
  const [enabled, setEnabled] = useState(true);
  const risk = elements(styles, "risk_warning_elements");
  const profit = elements(styles, "profit_claim_elements");
  const blocks = elements(styles, "text_blocks");
  const quoted = quotes.flatMap((quote) => blocksFor(quote, blocks).map((block) => ({ quote, block })));
  const canMark = risk.length + profit.length + quoted.length > 0;

  const firstY = Math.min(...[...risk, ...profit, ...quoted.map((q) => q.block)].map((el) => (el.rect as Rect).y), Infinity);
  const cropped = preview !== undefined && size.height > preview.maxHeight;
  const offset = cropped && Number.isFinite(firstY) ? Math.min(Math.max(0, firstY * size.scale - 70), size.height - preview.maxHeight) : 0;

  return (
    <div>
      {canMark && (
        <div className="shot-controls">
          <label className="shot-toggle">
            <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> Zaznacz na zrzucie
          </label>
          {enabled && (
            <span className="shot-legend">
              {profit.length > 0 && <span className="shot-legend__item shot-legend__item--profit">zysk (czcionka)</span>}
              {risk.length > 0 && <span className="shot-legend__item shot-legend__item--risk">ryzyko (czcionka)</span>}
              {quoted.some((q) => q.quote.tone === "claim") && <span className="shot-legend__item shot-legend__item--claim">cytat: obietnica / oferta</span>}
              {quoted.some((q) => q.quote.tone === "warning") && <span className="shot-legend__item shot-legend__item--warning">cytat: ostrzeżenie</span>}
            </span>
          )}
        </div>
      )}
      <div className="shot-frame" style={cropped ? { maxHeight: preview.maxHeight } : undefined}>
        <div className="shot-wrap" style={{ marginTop: -offset }}>
          <img
            className="shot"
            src={src}
            alt="Zrzut ekranu zapisany jako dowód"
            onLoad={(e) =>
              setSize({ scale: e.currentTarget.clientWidth / e.currentTarget.naturalWidth, height: e.currentTarget.clientHeight })
            }
          />
          {enabled && size.scale > 0 && (
            <>
              {profit.map((el, i) => (
                <Marked key={`p${i}`} rect={el.rect as Rect} scale={size.scale} className="shot-box--profit" label={`zysk ${el.fontSize}`} />
              ))}
              {risk.map((el, i) => (
                <Marked key={`r${i}`} rect={el.rect as Rect} scale={size.scale} className="shot-box--risk" label={`ryzyko ${el.fontSize}`} />
              ))}
              {quoted.map(({ quote, block }, i) => (
                <Marked key={`q${i}`} rect={block.rect as Rect} scale={size.scale} className={`shot-box--${quote.tone}`} label={quote.label} />
              ))}
            </>
          )}
        </div>
        {cropped && (
          <div className="shot-fade">
            <Link className="btn btn--secondary" to={preview.fullHref}>
              Pokaż cały zrzut
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
