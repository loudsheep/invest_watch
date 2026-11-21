# 0019. GDPR data handling and observability

- Status: Accepted
- Date: 2026-11-21

## Context

Finfluencers are often private individuals. The system stores their content and screenshots. Operators need visibility into queues, collectors and errors without heavy infrastructure.

## Decision

GDPR:

- data minimization: store only what is needed as evidence,
- configurable TTL for documents without findings (for example 30 days); evidence for confirmed findings is retained,
- raw evidence accessible only to authenticated users and recorded in the audit log,
- a short section in the concept covering legal basis, data scope and retention.

Observability:

- structured JSON logs (`structlog`) with a `trace_id` propagated through the pipeline,
- a "System health" dashboard view: queue lengths, collector status, proxy error rate, last crawl per source,
- Prometheus and Grafana documented as the production path, not included in compose.

## Consequences

- Lightweight compose stack with a credible path to production monitoring and compliance.
