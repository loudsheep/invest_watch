# AGENTS.md - frontend

Read the root [AGENTS.md](../AGENTS.md) first.

- React + Vite + TypeScript, props-based components, data via TanStack Query (`src/lib/api.ts`).
- UI strings in Polish, in `src/i18n/pl.json` where shared.
- `npm run lint` must pass; `no-console` is an error. No placeholder UI: ship a feature wired to the API or leave it out.
- Styling: tokens and classes in `src/styles.css` (ADR-0021).
