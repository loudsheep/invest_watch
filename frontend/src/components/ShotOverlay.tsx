import { useState } from "react";

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface StyledElement {
  fontSize?: string;
  rect?: Rect;
}

interface Props {
  src: string;
  styles: Record<string, unknown> | null;
}

function boxes(styles: Record<string, unknown> | null, key: string): StyledElement[] {
  const list = styles?.[key];
  return Array.isArray(list) ? (list as StyledElement[]).filter((el) => el.rect && el.rect.w > 0 && el.rect.h > 0) : [];
}

function Marked({ el, scale, tone }: { el: StyledElement; scale: number; tone: "risk" | "profit" }) {
  const rect = el.rect as Rect;
  return (
    <span
      className={`shot-box shot-box--${tone}`}
      style={{ left: rect.x * scale, top: rect.y * scale, width: rect.w * scale, height: rect.h * scale }}
    >
      <span className="shot-box__label">{tone === "risk" ? "ryzyko" : "zysk"} {el.fontSize}</span>
    </span>
  );
}

export default function ShotOverlay({ src, styles }: Props) {
  const [scale, setScale] = useState(0);
  const [enabled, setEnabled] = useState(true);
  const risk = boxes(styles, "risk_warning_elements");
  const profit = boxes(styles, "profit_claim_elements");
  const canMark = risk.length + profit.length > 0;

  return (
    <div>
      {canMark && (
        <label className="shot-toggle">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> Porównanie czcionek na zrzucie
        </label>
      )}
      <div className="shot-wrap">
        <img
          className="shot"
          src={src}
          alt="Zrzut ekranu zapisany jako dowód"
          onLoad={(e) => setScale(e.currentTarget.clientWidth / e.currentTarget.naturalWidth)}
        />
        {enabled && scale > 0 && (
          <>
            {profit.map((el, i) => (
              <Marked key={`p${i}`} el={el} scale={scale} tone="profit" />
            ))}
            {risk.map((el, i) => (
              <Marked key={`r${i}`} el={el} scale={scale} tone="risk" />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
