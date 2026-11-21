# 0007. Frontend stack

- Status: Accepted
- Date: 2026-11-21

## Context

The specification requires React, Vue or Angular, Chart.js or Recharts, Socket.io, props-based architecture and allows open source UI libraries. The jury evaluates library security and browser console cleanliness.

## Decision

- React, Vite, TypeScript.
- shadcn/ui (Radix and Tailwind): components are copied into the repository, which keeps the dependency tree small.
- Recharts for trends and the precision-recall chart.
- TanStack Query for data fetching and client cache, TanStack Table for filtering.
- socket.io-client for alerts.
- ESLint with `no-console` and React error boundaries.

Mantine and MUI were rejected as heavier in dependencies and more generic visually.

## Consequences

- Smaller `npm audit` and Snyk surface.
- A clean console is enforced by lint rather than by discipline.
