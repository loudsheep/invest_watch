# 0003. Pluggable collectors and data source strategy

- Status: Accepted
- Date: 2026-11-21

## Context

The jury evaluates scraping correctness live. Facebook, Instagram and TikTok aggressively block bots. Sample data is delivered on a USB drive during the hackathon in an unknown format.

## Considered options

1. Only the provided dataset. Scraping would be effectively absent.
2. Everything live from the web and social media. A single block during the demo is fatal.
3. Pluggable collectors behind a common interface, mixing live sources and the dataset.

## Decision

Option 3. Every source implements `Collector -> RawDocument` and is registered in configuration with its own schedule:

- open web: Playwright and httpx, with SearXNG for discovery,
- social media: YouTube first (yt-dlp: descriptions and transcripts), then TikTok or Instagram public profiles via Playwright,
- `dataset`: ingests the provided samples through the same pipeline,
- `demo-sites`: local fictional pages (see ADR-0017).

## Consequences

- Adding a source means adding one collector and one config entry.
- The dataset guarantees volume for charts and acts as a fallback when live sources fail.
