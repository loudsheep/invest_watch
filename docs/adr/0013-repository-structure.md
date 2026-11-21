# 0013. Single repository without monorepo tooling

- Status: Accepted
- Date: 2026-11-21

## Context

The task asks to avoid heavy monorepo structures in favor of a clear split, while a single code repository is submitted.

## Decision

One repository, no monorepo tooling (no Nx, Turborepo, workspaces or Bazel). Each service is self-contained with its own Dockerfile and dependencies:

```
services/{api,scraper,ai,scheduler}/
frontend/
common/        # Pydantic schemas, DB models, Alembic migrations, Redis client
config/        # YAML rules, taxonomies, seeds, sources
data/          # registry snapshot, samples
demo-sites/
infra/         # docker-compose.yml, init SQL, SearXNG / MinIO / proxy config
docs/
```

Python uses `uv` with one `pyproject.toml` per service; `common` is a path dependency. Database migrations use Alembic and run in a one-off `migrate` container.

## Consequences

- Clear service boundaries and per-service dependency scanning.
- Polyrepo was rejected as pure overhead for a single submission.
