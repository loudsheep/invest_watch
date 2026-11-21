# 0002. LLM inference deployment and two-tier AI pipeline

- Status: Accepted
- Date: 2026-11-21

## Context

The whole stack must start with `docker compose up` and use only free, on-premise models. The reference machine is a MacBook M3 Pro with 36 GB RAM. Docker on macOS has no access to the Metal GPU, so an LLM inside a container runs on CPU only and is several times slower.

## Considered options

1. Ollama in compose on CPU only.
2. Native Ollama on the host, reached via `host.docker.internal`. Breaks the one-command requirement.
3. Hybrid: Ollama in compose by default, overridable with `LLM_BASE_URL` in `.env`.

## Decision

Option 3, plus a GPU compose profile for Linux with NVIDIA.

The AI pipeline has two tiers:

1. A fast classifier (multilingual embeddings plus a lightweight head per module) scores every document in milliseconds on CPU. This score drives the calibration threshold.
2. The LLM runs only for candidates above a pre-filter threshold and produces structured explanations and extraction (entities, profit claims, risk statements, verdict, rationale).

## Consequences

- Compose works everywhere out of the box; the demo switches to Metal for speed.
- Threshold changes never trigger LLM calls, so calibration is instant.
- LLM load is bounded by the number of candidates, not by crawl volume.
