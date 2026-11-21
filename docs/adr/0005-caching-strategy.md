# 0005. Content-hash based layered caching

- Status: Accepted
- Date: 2026-11-21

## Context

Crawling, embedding and LLM inference are expensive, and repeated requests increase the risk of being blocked. The specification also requires deduplication.

## Decision

Use the SHA-256 of normalized content as the base cache key across layers:

| Layer | Key | Store |
|---|---|---|
| Fetch | canonical URL, `ETag` / `Last-Modified`, content hash (also deduplication) | Postgres |
| Registry | alias to entity index, rebuilt on `registry-sync` | Redis |
| Entity resolution | mention to entity or null | Redis |
| Embeddings | content hash + model | Postgres (pgvector) |
| LLM | content hash + model + prompt version | Redis |
| Threshold | raw scores persisted; threshold change is an SQL filter | Postgres |

Redis (already used for the queue) is the hot cache. Postgres is the durable source of truth.

## Consequences

- Nothing is fetched, embedded or sent to the LLM twice for the same content.
- Changing a prompt version or model invalidates only the affected entries.
