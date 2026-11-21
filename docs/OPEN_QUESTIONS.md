# Open questions (unchanged from CONCEPT.md section 19, tracked here for implementation impact)

1. **M2 risk-requirements attachment** - not available while building. `config/m2_rules.yaml` encodes a best-effort reading of MiFID II art. 24(3), delegated reg. 2017/565 art. 44, and the ESMA CFD warning. Once the real attachment arrives, only that YAML file needs editing - no code changes.
2. **Dataset format/labels from the USB drive** - unknown at build time. `services/scraper/app/collectors/dataset.py` accepts either a `documents.jsonl` file or one `*.json` file per document in `data/dataset/`, each with `url/platform/author/title/published_at/content/html` fields and an optional `label`. Adjust `_to_raw_document` if the real format differs.
3. **Whether one social collector is enough for demo** - built only YouTube (yt-dlp) for now; TikTok/Instagram are not implemented. Adding one means a new `Collector` subclass in `services/scraper/app/collectors/` plus a `sources` row.
4. **Labeled reference set for FP/FN** - none exists yet. The calibration panel computes precision/recall from analyst-confirmed/dismissed findings (the `labels` table), which starts empty. Expect the PR curve to be meaningless until a few dozen findings are triaged (or seed `labels` manually for demo).

# Implementation gaps vs. CONCEPT.md (by priority)

These are known shortfalls against the full spec, left for later passes - see `docs/IMPLEMENTATION_NOTES.md` for what *is* in place and why these were cut for time.

- TikTok / Instagram collectors (P1): not started.
- WHOIS domain-age signal for M3 clone-firm detection (P1): only string-similarity lookalike-domain check is implemented, no WHOIS lookup.
- Evidence chain-of-custody "change detection on re-crawl" (P2): content-hash dedup exists, but no diff/alert when a disclaimer disappears between crawls.
- Campaign clustering via pgvector similarity search, "find similar" (P2): embeddings + pgvector index exist; no UI or endpoint for cluster/similarity search yet.
- PDF case report (P2): not started.
- "Przetrenuj model" button exists end-to-end, but active-learning / sample-selection strategy is just "all analyst labels so far" - no uncertainty sampling.
- Video transcription (faster-whisper) / frame OCR (P3): not started.
- Dashboard uses hand-rolled CSS, not shadcn/ui + Tailwind (deviation from ADR-0007, chosen to save setup time under the deadline). Functionally equivalent views exist; restyling later is low-risk since components are already isolated per page.
- OIDC-ready auth interface (ADR-0016 mentions swapping to Keycloak later): current auth is JWT-in-cookie only, no abstraction layer added yet since there is a single IdP today.
