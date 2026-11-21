import { useState } from "react";
import { API_URL, type FindingDetail } from "../lib/api";
import type { Quote } from "../lib/quotes";
import ShotOverlay from "./ShotOverlay";

const DEVICE_LABELS: Record<string, string> = { tablet: "Tablet", telefon: "Telefon" };
const DEVICE_MAX_WIDTH: Record<string, number> = { tablet: 820, telefon: 400 };

interface Props {
  finding: FindingDetail;
  quotes: Quote[];
  preview?: { maxHeight: number; fullHref: string };
}

export default function ScreenshotViewer({ finding, quotes, preview }: Props) {
  const [variant, setVariant] = useState("desktop");
  const variants = ["desktop", ...finding.device_screenshots];
  const base = finding.screenshot_url
    ? finding.screenshot_url.startsWith("http")
      ? finding.screenshot_url
      : `${API_URL}${finding.screenshot_url}`
    : null;
  if (!base) return null;

  const isDesktop = variant === "desktop";
  const viewports = (finding.computed_styles?.viewports ?? {}) as Record<string, Record<string, unknown>>;
  const styles = isDesktop ? finding.computed_styles : (viewports[variant] ?? null);
  const src = isDesktop ? base : `${base}?variant=${encodeURIComponent(variant)}`;

  return (
    <div>
      {variants.length > 1 && (
        <div className="shot-tabs" role="tablist" aria-label="Urządzenie">
          {variants.map((name) => (
            <button
              key={name}
              role="tab"
              aria-selected={variant === name}
              className={`btn btn--small ${variant === name ? "btn--primary" : "btn--secondary"}`}
              onClick={() => setVariant(name)}
            >
              {name === "desktop" ? "Komputer" : (DEVICE_LABELS[name] ?? name)}
            </button>
          ))}
        </div>
      )}
      <div style={{ maxWidth: isDesktop ? undefined : DEVICE_MAX_WIDTH[variant] }}>
        <ShotOverlay key={variant} src={src} styles={styles} quotes={isDesktop ? quotes : []} preview={preview} />
      </div>
    </div>
  );
}
