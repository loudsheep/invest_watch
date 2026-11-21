# 0020. Object storage: Garage instead of MinIO

- Status: Accepted
- Date: 2026-11-21

## Context

CONCEPT.md's architecture diagram names MinIO for evidence storage (raw HTML, screenshots). MinIO's AGPLv3 licensing and the removal of its open-source web console make it a poor fit for a submission that must avoid copyleft dependencies and hand over a clean toolchain to UKNF (AGENTS.md, CONCEPT.md section 2).

## Decision

Use [Garage](https://garagehq.deuxfleurs.fr/) (AGPLv3-free, Apache-2.0) as the S3-compatible object store instead. It speaks the same S3 API, so the existing `minio` Python client library (an S3 client despite its name) keeps working against it unchanged - only endpoint/credentials move from `MINIO_*` to `S3_*` env vars.

Setup mirrors another in-house project's pattern: `garage/garage.toml` for node config, `garage/init.sh` run once on the host (`docker compose exec garage ...`) to assign the storage layout, import a dev access key, and create the `investwatch-evidence` bucket.

## Consequences

- One fewer copyleft-adjacent dependency; licensing to document for UKNF handover stays simpler.
- No web console out of the box (Garage has none); evidence access goes exclusively through the authenticated `/api/documents/{id}/screenshot` and `/html` endpoints, which was already the design (audit-logged access, ADR-0016/0019) - no functionality lost.
- `garage/init.sh` must be run once after first `docker compose up -d garage`, unlike MinIO which created its bucket automatically; documented in README Quick Start.
