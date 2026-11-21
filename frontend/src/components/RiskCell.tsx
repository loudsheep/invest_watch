import { riskBand } from "../lib/modules";

export default function RiskCell({ score }: { score: number }) {
  return <span className={`risk-cell risk-cell--${riskBand(score)}`}>{score.toFixed(2)}</span>;
}
