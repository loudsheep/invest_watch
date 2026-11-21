import { useQuery } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import { api, type GraphNode } from "../lib/api";
import Loading from "./Loading";
import QueryError from "./QueryError";

const COLUMNS: GraphNode["type"][] = ["advertiser", "entity", "document", "promo_code", "domain"];
const COL_WIDTH = 170;
const ROW_HEIGHT = 44;
const NODE_W = 150;
const NODE_H = 30;
const labels = pl as Record<string, string>;

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export default function CaseGraph({ caseId }: { caseId: number }) {
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ["case-graph", caseId],
    queryFn: () => api.getCaseGraph(caseId),
  });

  if (isPending) return <Loading />;
  if (isError) return <QueryError onRetry={() => refetch()} />;
  if (data.nodes.length <= 1) return <p className="empty">{pl["cases.graph.empty"]}</p>;

  const columns = COLUMNS.filter((type) => data.nodes.some((n) => n.type === type));
  const position = new Map<string, { x: number; y: number }>();
  columns.forEach((type, col) => {
    data.nodes
      .filter((n) => n.type === type)
      .forEach((n, row) => position.set(n.id, { x: col * COL_WIDTH + 10, y: row * ROW_HEIGHT + 30 }));
  });
  const rows = Math.max(...columns.map((type) => data.nodes.filter((n) => n.type === type).length));
  const width = columns.length * COL_WIDTH;
  const height = rows * ROW_HEIGHT + 40;

  return (
    <div className="graph">
      <ul className="graph__legend">
        {columns.map((type) => (
          <li key={type}>
            <span className={`graph__swatch graph__swatch--${type}`} />
            {labels[`graph.${type}`]}
          </li>
        ))}
      </ul>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label={pl["cases.graph"]}>
        {columns.map((type, col) => (
          <text key={type} x={col * COL_WIDTH + 10} y={16} className="graph__column">
            {labels[`graph.${type}`]}
          </text>
        ))}
        {data.edges.map((e) => {
          const from = position.get(e.source);
          const to = position.get(e.target);
          if (!from || !to) return null;
          return (
            <line
              key={`${e.source}-${e.target}-${e.label}`}
              x1={from.x + NODE_W}
              y1={from.y + NODE_H / 2}
              x2={to.x}
              y2={to.y + NODE_H / 2}
              className="graph__edge"
            />
          );
        })}
        {data.nodes.map((n) => {
          const p = position.get(n.id);
          if (!p) return null;
          return (
            <g key={n.id}>
              <title>{n.label}</title>
              <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx={n.type === "advertiser" ? NODE_H / 2 : 3} className={`graph__node graph__node--${n.type}`} />
              <text x={p.x + 10} y={p.y + 19} className={`graph__label graph__label--${n.type}`}>
                {truncate(n.label, 22)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
