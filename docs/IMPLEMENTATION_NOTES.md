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
- The classifier head (`classifiers/head.py`) is a `LogisticRegression` + isotonic `CalibratedClassifierCV`, trained from the `labels` table via the "Przetrenuj model" button. Before any training has happened (cold start, empty `labels` table), it falls back to cosine similarity against a topic-phrase centroid from `config/taxonomies.yaml` - so M1/M2/M3 produce *some* signal from the first document onward instead of needing labeled data to start.
- M2 is pure rule-evaluation against `config/m2_rules.yaml` (ADR-0009) - no embedding classifier involved for the pass/fail criteria, only for the general "is this even relevant to M2" gating score.
- Entity resolution (`entity_resolution.py`) tries exact domain match first, then fuzzy alias match (rapidfuzz, threshold 85) cached in Redis per the `wzmianka -> entity_id` strategy in ADR-0005.
- Cases are auto-aggregated: the first finding for an entity creates a `Case`, subsequent findings for the same primary entity append to `finding_ids`. No manual case management UI yet.

## scheduler/

- Celery Beat schedule is built from `config/sources.yaml` at startup (one entry per source with a non-null `schedule_seconds`), plus two fixed jobs: `registry-sync` (6h) and `retention-cleanup` (24h).
- `registry_sync` currently re-reads the local `data/registry_seed.json` snapshot (upsert by name) rather than calling live KNF/ESMA endpoints, since no such endpoint was specified - see open question 1 in `docs/CONCEPT.md` section 19 (not directly answerable without mentor input on real registry access).

## frontend/

- Plain React + Vite + TypeScript + hand-written CSS, not shadcn/ui/Tailwind as ADR-0007 specifies - a scope cut to get all P0 views working before the deadline. Views: Przegląd, Findingi (filterable, status change), Case'y (list only, no graph view wired into UI yet though the `/api/cases/{id}/graph` endpoint exists), Kalibracja (slider + PR curve + retrain), Skanuj URL (live pipeline stages via Socket.io room per scan).
- ESLint configured with `no-console` per AGENTS.md.

## demo-sites/

- Plain Node `http` server (no framework) serving three static fixture pages matching the three paths `OpenWebCollector`/`DemoSitesCollector` expect: `/finfluencer-aurum` (M1: undisclosed affiliate link + promo code), `/landing-aurum-cfd` (M2: big profit claim, tiny risk disclaimer), `/shadow-advisory-pwm` (M3: advisory-service language from an unauthorized fictional entity). All entity/domain names are fictional per ADR-0017.

## Known rough edges worth a second pass

- No automated tests yet (pytest/vitest wired into CI but no test files exist). Given the deadline, correctness was prioritized over test coverage for this first pass - add tests before relying on this for anything beyond the demo.
- `services/ai/app/classifiers/head.py` persists trained models to a local `/app/models` volume inside the container - this is lost on container recreation unless a volume is mounted. Fine for a single demo run; add a named volume if retraining needs to survive restarts.
