# Implementation notes

What exists after the first implementation pass, service by service, and the
non-obvious decisions made while filling gaps the spec left open. Read
alongside `docs/OPEN_QUESTIONS.md` for what's still missing.

## common/

- SQLAlchemy models mirror the data model in CONCEPT.md section 7 exactly, one table per entity.
- Schema lives entirely in Alembic migrations (`common/alembic/versions/`), not in `infra/init.sql` (which now only enables the `vector`/`pg_trgm` extensions). This matches ADR-0013's mention of Alembic better than mixing raw SQL and migrations.
- `0002_seed_data.py` seeds two dev users (`analyst`/`admin`, password `changeme-dev`, Argon2-hashed at migration time) and the entity registry snapshot from `data/registry_seed.json`.
- Pydantic schemas are split into `schemas/pipeline.py` (Celery message payloads between services) and `schemas/api.py` (FastAPI request/response bodies).

## api/

- FastAPI + `python-socketio` mounted as one ASGI app (`app.main:socket_app`).
- Auth: JWT in an httpOnly cookie, Argon2 password hashing, two roles (`analyst`, `admin`) via `Depends(get_current_user)` / `Depends(require_admin)`.
- A background task (`pubsub_bridge.py`) bridges two Redis pub/sub channels - `findings:high_risk` (ai-worker) and `scan:stages` (scraper/ai-worker) - onto Socket.io events, so the dashboard never talks to Redis directly.
- Calibration metrics are computed on the fly from the `labels` table at request time (no precomputation/caching) since the hackathon dataset is small; revisit if this gets slow.
- `/api/scan` and the calibration `/retrain` endpoint dispatch Celery tasks by name string (`celery_app.send_task`) rather than importing worker code, keeping the api image free of Playwright/sentence-transformers dependencies.

## scraper-worker/

- `Collector` is the only extension point (ADR-0003): `discover() -> Iterator[str]`, `fetch(candidate) -> RawDocument | None`. Four collectors exist: `dataset`, `demo_sites`, `open_web` (Playwright + SearXNG), `youtube` (yt-dlp).
- `open_web.py` also extracts computed CSS (font-size/color) for any element whose text matches risk-warning keywords, feeding the M2 `risk_prominence` criterion - this is the only collector that populates `Document.computed_styles`.
- `ProxyPool` (ADR-0015) does sticky-per-domain round robin with a simple failure-count circuit breaker; an empty `PROXY_URLS` disables it transparently (direct connection).
- Dedup happens here, not in ai-worker: `normalize_text` + SHA-256 before anything is written to Postgres, so duplicate content never reaches the AI pipeline.
- The `dataset` source has `schedule_seconds: null` in `config/sources.yaml` (run once, not recurring); the scraper-worker container kicks it off itself via Celery's `worker_ready` signal rather than waiting on scheduler, since a one-off task doesn't fit a cron beat schedule.

## ai-worker/

- Pipeline per document: embed (multilingual-e5-base) -> per-module rule signal + classifier-head score -> if combined score clears `LLM_CANDIDATE_THRESHOLD` (0.6), call Ollama with structured JSON output, cached by `content_hash + model + prompt_version` in Redis.
- The classifier head (`classifiers/head.py`) is a `LogisticRegression` + isotonic `CalibratedClassifierCV`, trained from the `labels` table via the "Przetrenuj model" button. Before any training has happened (cold start, empty `labels` table), it falls back to a contrast score from `config/taxonomies.yaml`: `sigmoid(60 * (best cosine to the module's topic phrases - best cosine to the shared `negative_phrases`))`. e5 cosines sit around 0.83 for any Polish text, so a raw cosine (the previous fallback) scored everything ~0.92; measured now: off-topic text 0.00-0.17, on-topic 0.65-0.93. Modules overlap semantically (a promo text also scores 0.5-0.8 on the other modules), rules and LLM decide the rest - so M1/M2/M3 produce *some* signal from the first document onward instead of needing labeled data to start.
- M2 is pure rule-evaluation against `config/m2_rules.yaml` (ADR-0009) - no embedding classifier involved for the pass/fail criteria, only for the general "is this even relevant to M2" gating score.
- Entity resolution (`entity_resolution.py`) tries exact domain match first, then fuzzy alias match (rapidfuzz, threshold 85) cached in Redis per the `wzmianka -> entity_id` strategy in ADR-0005.
- Cases are auto-aggregated: the first finding for an entity creates a `Case`, subsequent findings for the same primary entity append to `finding_ids`. No manual case management UI yet.

## scheduler/

- Celery Beat schedule is built from `config/sources.yaml` at startup (one entry per source with a non-null `schedule_seconds`), plus two fixed jobs: `registry-sync` (6h) and `retention-cleanup` (24h).
- `registry_sync` currently re-reads the local `data/registry_seed.json` snapshot (upsert by name) rather than calling live KNF/ESMA endpoints, since no such endpoint was specified - see open question 1 in `docs/CONCEPT.md` section 19 (not directly answerable without mentor input on real registry access).

## frontend/

- Plain React + Vite + TypeScript + hand-written CSS (ADR-0021). Views: Przegląd, Findingi (filters, text search, status change with note), Case'y (list, graph, PDF report), Zdrowie systemu, Kalibracja, Skanuj URL (live stages over Socket.io).
- ESLint configured with `no-console` per AGENTS.md.

## demo-sites/

- Plain Node `http` server (no framework) serving three static fixture pages matching the three paths `OpenWebCollector`/`DemoSitesCollector` expect: `/finfluencer-aurum` (M1: undisclosed affiliate link + promo code), `/landing-aurum-cfd` (M2: big profit claim, tiny risk disclaimer), `/shadow-advisory-pwm` (M3: advisory-service language from an unauthorized fictional entity). All entity/domain names are fictional per ADR-0017.

## Dashboard views from the spec (done)

- **Case graph:** `CaseGraph` (hand-rolled SVG, no graph dependency) draws advertiser -> firm -> document -> promo code / domain from `/api/cases/{id}/graph`. Case list shows the entity name.
- **System health:** `GET /api/system/health` + `/system` page (refresh every 5 s): Celery queue lengths (Redis `LLEN`), collectors with last crawl / schedule / document count, proxies with failure count and circuit state. `ProxyPool` writes failures to Redis (`proxy:failures`, `proxy:circuit_open_until`) because it lives in the scraper process.
- **M2 finding:** criteria with legal basis plus risk-warning vs profit-claim font comparison. `OpenWebCollector` now also extracts `profit_claim_elements`; `m2.font_comparison` compares the smallest warning font with the largest profit font and feeds `risk_prominence` (`min_font_ratio`). `demo-sites` collector now subclasses `OpenWebCollector` so fixtures get screenshots and computed styles.
- **M1 / M3 findings:** promo code, affiliate evidence, disclosure flag, lookalike domain and registry entities (with `authorized`) shown as fields. `FindingDetail` returns `mentions`. Registry entities are also found in document text (whole-word alias match), not only by domain/author.
- **Findings filters:** risk level (high >= 0.8, medium 0.5-0.8, low < 0.5, via `min_score`/new `max_score`), source platform, date range.
- **Roles:** threshold slider and retrain are admin-only in the UI (API already enforced it).
- M1 now analyses raw content (normalization replaced URLs, so `?ref=` was never detected) and the promo-code regex skips the word "promocyjnym".
- Scraper kicks off `dataset` and `demo-sites` once at worker start.

## Relevance gating (ai-worker)

- A module only creates a finding when the classifier score is >= `RELEVANCE_THRESHOLD` (0.5); rules measure how bad a relevant document is, they do not decide relevance. Before this, M2 scored 1.00 for any page without a risk warning (e.g. a sports article). Score is still `max(rule, classifier)` after the gate: a product would cap demo findings below the 0.8 alert level (cold-start classifier tops out around 0.7).
- M2 criteria can carry `applies_when` (regex) in `config/m2_rules.yaml`; criteria whose subject the text never mentions (CFD, past performance, forecasts) are skipped, not weighted, and shown as "n/d" in the UI.

## Known rough edges worth a second pass

- Test coverage is thin: `services/ai/tests` covers the M2 rules, `services/scraper/tests` the re-crawl change detection. No frontend tests.
- Trained classifier heads persist in the `ai_models` named volume.

## LLM via OpenAI-compatible API

The LLM client calls `/chat/completions` instead of Ollama's native `/api/generate`. Default endpoint is the Ollama service in compose (`http://ollama:11434/v1`, `gemma3:4b`, pulled by `ollama-init`); any other OpenAI-compatible endpoint is a configuration change (ADR-0002, ADR-0021).

## Evidence, reports and discovery

- `GET /api/documents/{id}/evidence` and `evidence.zip`: SHA-256 manifest and a package (HTML, screenshot, computed styles, `manifest.json`). Every access is audit-logged.
- `GET /api/cases/{id}/report.pdf`: supervisory note (ReportLab, DejaVu Sans for Polish glyphs) with failed M2 criteria, legal bases and evidence hashes.
- `GET /api/findings/{id}/similar`: nearest documents by pgvector cosine distance (campaign clusters).
- Collectors get discovery config from `config/taxonomies.yaml` and the authorized registry domains (`services/scraper/app/discovery.py`), so open-web and social sources crawl without hand-maintained query lists.
- M3 adds an RDAP domain-age signal; a lookalike domain younger than a year scores 0.9.

## Evidence integrity, device screenshots and tests

- Every captured document stores a `custody` manifest: SHA-256 of the HTML, screenshots and computed styles, sealed with a manifest hash and capture time (`common/investwatch_common/custody.py`). The evidence endpoint recomputes the hashes from Garage and reports `verified`, per-file status (`ok`, `modified`, `missing`); older documents have no manifest.
- Tablet and phone full-page screenshots are stored next to the desktop one (`documents.device_screenshots`) and shown as tabs, with the risk-warning boxes measured at that viewport.
- `GET /api/calibration/{module}/uncertain` returns unlabeled findings nearest to the threshold; deciding on them from the Kalibracja page creates labels.
- `/api/auth/me` answers 200 with `null` for anonymous visitors so the login screen produces no console errors.
- Tests: vitest (`frontend/src/**/*.test.ts`), Playwright E2E (`frontend/e2e`), pytest per service.
