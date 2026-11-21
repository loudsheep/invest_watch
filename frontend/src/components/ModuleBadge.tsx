import { moduleInfo } from "../lib/modules";

export default function ModuleBadge({ module }: { module: string }) {
  const info = moduleInfo(module);
  return (
    <span className="module-badge" title={info.name}>
      <svg width="11" height="10" viewBox="0 0 11 10" aria-hidden="true">
        {info.id === "m1" && <circle cx="5" cy="5" r="5" fill={info.color} />}
        {info.id === "m2" && <rect x="1" y="1" width="9" height="9" rx="1" fill={info.color} />}
        {info.id === "m3" && <polygon points="5.5,0 11,8 0,8" fill={info.color} />}
      </svg>
      {info.short}
    </span>
  );
}
