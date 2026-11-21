# 0010. Per-module discovery and focused crawling

- Status: Accepted
- Date: 2026-11-21

## Context

A scraper needs to know where to look. Each module targets different content and publishers.

## Decision

- M2: crawl official domains of registered firms from the registry.
- M1: SearXNG queries built from `firm alias x advertising phrase`, hashtags, and a seed list of finfluencer channels.
- M3: queries from a phrase taxonomy (investment advice, family office, wealth management, signals, guaranteed profit, model portfolio) and domains from the KNF warnings list as seeds.
- Focused crawling: the URL frontier is prioritized by embedding similarity between link context and module topics.
- Hygiene: per-domain limits and rate limiting, depth limit, `robots.txt` respected by default and configurable.

Taxonomies, seeds and sources are YAML in `config/`.

## Consequences

- Crawl budget goes to likely-relevant pages.
- Analysts can extend discovery without code changes.
