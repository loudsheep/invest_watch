# 0022. Production deployment on Coolify with an external LLM endpoint

- Status: Accepted
- Date: 2026-11-22

## Context

The demo instance runs on a shared Coolify v4 server. An Ollama server with GPU (`gemma4:12b` and other models) already runs in the same network and is used by other applications. The local `docker-compose.yml` is built for development: it runs Ollama on CPU, starts the Vite dev server, publishes ports on the host and reads configuration through relative bind mounts, which Coolify resolves against its own application directory instead of the cloned repository.

## Considered options

1. A separate `docker-compose.coolify.yml` used only by Coolify.
2. One compose file with profiles for the Ollama services.
3. A compose file edited by hand in the Coolify UI.

## Decision

Option 1.

- No `ollama` / `ollama-init` services. `LLM_BASE_URL` points to the shared Ollama (`http://10.21.36.10:11434/v1`, model `gemma4:12b`), as allowed by ADR-0002. Embeddings stay local in `ai-worker` (ADR-0014).
- No bind mounts. `config/` and `data/` are copied into the service images. Postgres, Garage, `garage-init` and SearXNG get small Dockerfiles in `infra/docker/` that add their configuration files. Local development still overrides the copies with bind mounts.
- The frontend is built once by `frontend/Dockerfile.prod` with `VITE_API_URL` as a build argument and served by nginx with a SPA fallback.
- No published ports. Coolify routes `investwatch.b.solvro.pl` to the frontend, `investwatch-api.b.solvro.pl` to the API and `investwatch-demo.b.solvro.pl` to the demo sites. Two subdomains on one level fit the existing `*.b.solvro.pl` wildcard and need no code change.
- Deploys are manual from the public repository's `main` branch; there is no auto-deploy on push.

The step-by-step guide is `docs/DEPLOY.md`.

## Consequences

- Two compose files must be kept in sync when services or environment variables change.
- Configuration changes need an image rebuild and redeploy.
- LLM latency depends on the shared Ollama load. Document data stays inside the organisation's network.
- The proxy pool profile (ADR-0015) is not part of the production stack.
