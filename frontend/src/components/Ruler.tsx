import type { CSSProperties } from "react";
import { HIGH_RISK, moduleInfo } from "../lib/modules";

interface RulerProps {
  score: number;
  module: string;
}

export default function Ruler({ score, module }: RulerProps) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  const style = { "--accent": moduleInfo(module).color } as CSSProperties;
  return (
    <div className="ruler" style={style} role="img" aria-label={`Ryzyko ${score.toFixed(2)} na skali do 1`}>
      <span className="ruler__fill" style={{ width: `${pct}%` }} />
      <span className="ruler__limit" style={{ left: `${HIGH_RISK * 100}%` }} />
    </div>
  );
}
