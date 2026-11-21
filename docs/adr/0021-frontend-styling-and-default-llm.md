# 0021. Hand-written frontend styling and Ollama as default LLM endpoint

- Status: Accepted
- Date: 2026-11-22
- Supersedes: the shadcn/ui and Tailwind part of ADR-0007

## Context

The dashboard was redesigned from a Figma specification. The resulting components use a small hand-written stylesheet with design tokens; shadcn/ui and Tailwind were never adopted. Separately, the task forbids external paid APIs, while the first implementation defaulted to OpenRouter.

## Decision

- Frontend styling is plain CSS with tokens in `frontend/src/styles.css`. React, Vite, TypeScript, Recharts, TanStack Query/Table and socket.io-client from ADR-0007 stay.
- The default `LLM_BASE_URL` is the Ollama service in `docker-compose.yml` (`http://ollama:11434/v1`, model `gemma3:4b`), pulled by `ollama-init`. Any other OpenAI-compatible endpoint is a configuration change.
- `docker compose up` runs `migrate`, `garage-init` and `ollama-init` as one-shot services, so no manual bootstrap step exists.

## Consequences

- Fewer frontend dependencies, smaller audit surface.
- The default stack makes no calls to paid external services.
- First start downloads the Ollama image and model.
