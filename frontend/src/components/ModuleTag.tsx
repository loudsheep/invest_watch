import type { CSSProperties } from "react";
import { moduleInfo } from "../lib/modules";

export default function ModuleTag({ module }: { module: string }) {
  const info = moduleInfo(module);
  return (
    <span className="tag" style={{ "--accent": info.color } as CSSProperties} title={info.name}>
      {info.short}
    </span>
  );
}
