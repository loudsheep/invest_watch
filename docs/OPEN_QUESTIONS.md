# Open questions and known gaps

## Resolved

1. **M2 risk-requirements attachment** - arrived. `config/m2_rules.yaml` implements all 18 criteria (12 split into 12a/12b), each with legal basis; `ref` is the number from the attachment. Visual criteria (4, 5, 6, 8, 13) use DOM computed styles and tablet/phone viewport renders, so they apply to pages fetched by the browser collectors, not to plain-text dataset samples (shown as "n/d").
2. **Dataset format** - see `docs/DATASET.md`: jsonl, json and csv with field aliases and optional per-module labels. Add an alias in `FIELD_ALIASES` if the real export differs.
3. **Labeled reference set** - `data/reference_labels.json` holds ground truth for the demo-sites fixtures; the ai-worker labels findings on those pages on creation, so calibration shows precision/recall from the first scan. Analyst decisions (confirm/dismiss) add to the same `labels` table.
4. **Social collectors** - YouTube and TikTok (public profiles and videos via yt-dlp). Facebook and Instagram are not implemented: they need a logged-in session, which is out of scope for an unauthenticated crawler.

## Still open

- Registry sync pulls the public KNF lists live (investment firms, banks with brokerage, foreign branches, notified foreign firms which is the Polish view of the ESMA passport register, and public warnings) and falls back to `data/registry_knf.json`. Domains exist only for firms curated in `data/registry_seed.json`; the KNF lists carry none. The ESMA register itself is not queried directly.
- Retraining uses all analyst labels; there is no uncertainty sampling.
- Auth is JWT-in-cookie only; there is no OIDC abstraction layer (ADR-0016 describes the intended swap).
- Video transcription (faster-whisper) and frame OCR are not implemented.
- Criteria 9 (comprehensibility) and 11 (comparisons) are heuristic (sentence length, jargon, source present), not LLM-judged.

## Decisions taken without mentor input

- **Risk level buckets:** high >= 0.8 (same as the alert threshold), medium 0.5-0.8, low < 0.5. Not configurable.
- **Source filter:** by document `platform` (web, youtube, tiktok, dataset).
- **Graph "advertiser" node:** document `author` (`<meta name="author">` for web pages).
- **Font comparison:** smallest risk-warning font vs largest profit-claim font, found by keyword hints in the DOM; heuristic, not layout analysis.
- **Proxy errors in health view:** cumulative failure count per proxy plus circuit state, kept in Redis.
- **Re-crawl change detection:** a new snapshot of a known URL whose risk statements disappeared raises the M2 risk score to at least 0.9 and shows the removed sentences.
