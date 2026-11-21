# 0015. Configurable proxy pool and user agent rotation

- Status: Accepted
- Date: 2026-11-21

## Context

The specification requires user agent and proxy rotation. Paid services are excluded; free public proxies are unreliable and unsafe; Tor exit nodes are widely blocked and inappropriate for a regulator.

## Decision

- A `ProxyPool` abstraction configured by `PROXY_URLS` in `.env`, with round-robin and sticky-per-domain strategies, a circuit breaker and health checks. An empty list means direct connections.
- Two local proxy containers in compose demonstrate rotation during the demo.
- User agent rotation uses realistic current agents with consistent headers (`Accept-Language: pl-PL`, `sec-ch-ua`) and a matching Playwright fingerprint.
- Logs and the system health view show which proxy and user agent served each request.

## Consequences

- UKNF can plug in its own legal proxy infrastructure without code changes.
