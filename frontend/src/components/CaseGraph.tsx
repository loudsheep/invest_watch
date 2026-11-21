import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import { api, type GraphNode } from "../lib/api";
import Loading from "./Loading";
import QueryError from "./QueryError";

type NodeType = GraphNode["type"];

const COLUMNS: { key: string; title: string; types: NodeType[] }[] = [
  { key: "who", title: "Podmioty", types: ["entity", "advertiser"] },
  { key: "content", title: "Treści", types: ["document"] },
  { key: "evidence", title: "Dowody", types: ["promo_code", "domain"] },
];
const NODE_W = 250;
const NODE_H = 40;
const COL_GAP = 130;
const ROW_GAP = 16;
const TOP = 32;
const labels = pl as Record<string, string>;

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export default function CaseGraph({ caseId }: { caseId: number }) {
  const [active, setActive] = useState<string | null>(null);
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ["case-graph", caseId],
    queryFn: () => api.getCaseGraph(caseId),
  });

  if (isPending) return <Loading />;
  if (isError) return <QueryError onRetry={() => refetch()} />;
  if (data.nodes.length <= 1) return <p className="empty">{pl["cases.graph.empty"]}</p>;

  const neighbours = new Map<string, Set<string>>();
  data.edges.forEach((e) => {
    neighbours.set(e.source, (neighbours.get(e.source) ?? new Set()).add(e.target));
    neighbours.set(e.target, (neighbours.get(e.target) ?? new Set()).add(e.source));
  });

  // Order each column by the mean position of its neighbours in the previous one, to keep edges short.
  const byType = (types: NodeType[]) => data.nodes.filter((n) => types.includes(n.type));
  const who = byType(COLUMNS[0].types).sort((a, b) => COLUMNS[0].types.indexOf(a.type) - COLUMNS[0].types.indexOf(b.type) || a.label.localeCompare(b.label));
  const index = new Map(who.map((n, i) => [n.id, i]));
  const mean = (node: GraphNode, order: Map<string, number>) => {
    const values = [...(neighbours.get(node.id) ?? [])].flatMap((id) => (order.has(id) ? [order.get(id) as number] : []));
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  };
  const content = byType(COLUMNS[1].types).sort((a, b) => mean(a, index) - mean(b, index));
  const contentIndex = new Map(content.map((n, i) => [n.id, i]));
  const evidence = byType(COLUMNS[2].types).sort(
    (a, b) => COLUMNS[2].types.indexOf(a.type) - COLUMNS[2].types.indexOf(b.type) || mean(a, contentIndex) - mean(b, contentIndex),
  );
  const columns = [who, content, evidence];

  const tallest = Math.max(...columns.map((c) => c.length));
  const height = TOP + tallest * (NODE_H + ROW_GAP);
  const width = 3 * NODE_W + 2 * COL_GAP;
  const position = new Map<string, { x: number; y: number }>();
  columns.forEach((nodes, col) => {
    const offset = ((tallest - nodes.length) * (NODE_H + ROW_GAP)) / 2;
    nodes.forEach((n, row) => position.set(n.id, { x: col * (NODE_W + COL_GAP), y: TOP + offset + row * (NODE_H + ROW_GAP) }));
  });

  const connected = (id: string) => active === null || id === active || neighbours.get(active)?.has(id);
  const types = [...new Set(data.nodes.map((n) => n.type))];

  return (
    <div className="graph">
      <ul className="graph__legend">
        {types.map((type) => (
          <li key={type}>
            <span className={`graph__swatch graph__swatch--${type}`} />
            {labels[`graph.${type}`]}
          </li>
        ))}
        <li className="graph__hint">Najedź na element, aby zobaczyć jego powiązania</li>
      </ul>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label={pl["cases.graph"]}>
        {COLUMNS.map((col, i) => (
          <text key={col.key} x={i * (NODE_W + COL_GAP)} y={14} className="graph__column">
            {col.title}
          </text>
        ))}
        {data.edges.map((e) => {
          const from = position.get(e.source);
          const to = position.get(e.target);
          if (!from || !to) return null;
          const forward = from.x < to.x;
          const [a, b] = forward ? [from, to] : [to, from];
          const x1 = a.x + NODE_W;
          const x2 = b.x;
          const y1 = a.y + NODE_H / 2;
          const y2 = b.y + NODE_H / 2;
          const mid = (x1 + x2) / 2;
          const on = active !== null && (e.source === active || e.target === active);
          return (
            <path
              key={`${e.source}-${e.target}-${e.label}`}
              d={`M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`}
              className={`graph__edge${on ? " graph__edge--on" : active !== null ? " graph__edge--dim" : ""}`}
            />
          );
        })}
        {data.nodes.map((n) => {
          const p = position.get(n.id);
          if (!p) return null;
          return (
            <g
              key={n.id}
              className={`graph__item${connected(n.id) ? "" : " graph__item--dim"}`}
              onMouseEnter={() => setActive(n.id)}
              onMouseLeave={() => setActive(null)}
            >
              <title>{n.label}</title>
              <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx={n.type === "advertiser" ? NODE_H / 2 : 4} className={`graph__node graph__node--${n.type}`} />
              <text x={p.x + 14} y={p.y + NODE_H / 2 + 4} className={`graph__label graph__label--${n.type}`}>
                {truncate(n.label, n.type === "document" ? 33 : 31)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
