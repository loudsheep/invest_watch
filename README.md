# InvestWatch

Autonomiczny system nadzoru treści finansowych w sieci. Koncepcja: [docs/CONCEPT.md](docs/CONCEPT.md). Decyzje architektoniczne: [docs/adr/](docs/adr/).

## Wymagania sprzętowe

- Docker + Docker Compose.
- Referencyjnie: MacBook M3 Pro, 36 GB RAM. Minimum: 16 GB RAM, 4 rdzenie (Ollama + Playwright + Postgres razem są ciężkie).
- Dla przyspieszenia LLM na macOS: natywna Ollama na hoście (patrz `.env.example`, `LLM_BASE_URL`), bo Docker na macOS nie ma dostępu do GPU/Metal.
- Proxy do demonstracji rotacji: `docker compose --profile proxy up -d`, potem `PROXY_URLS=http://proxy-1:8118,http://proxy-2:8118`.

## Quick Start

```bash
cp .env.example .env
docker compose up
```

Jedna komenda: migracje i seed rejestru (`migrate`), bootstrap storage'u (`garage-init`) oraz pobranie modelu LLM (`ollama-init`) uruchamiają się automatycznie. Pierwszy start pobiera obrazy i model (kilka GB).

- Dashboard: http://localhost:47173
- API: http://localhost:47800 (health: `/health`)
- Garage (S3 API, ewentualnie do podglądu przez `aws s3 --endpoint-url`): http://localhost:47900
- Użytkownicy: `analyst` / `admin`, hasła z `ANALYST_PASSWORD` / `ADMIN_PASSWORD` w `.env`.
- Wszystkie sekrety są tylko w `.env`; brak zmiennej zatrzymuje `docker compose` z błędem. Wartości z `.env.example` służą wyłącznie do lokalnego demo - poza nim wygeneruj nowe (`openssl rand -hex 32`).
- Porty infrastruktury (Postgres, Redis, Garage, Ollama, SearXNG) są wystawione tylko na `127.0.0.1`.

## Konfiguracja serwisów

Wszystkie zmienne w `.env` (skopiowane z `.env.example`). Kluczowe:

| Zmienna | Rola |
|---|---|
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | endpoint zgodny z OpenAI; domyślnie Ollama z compose (ADR-0002, ADR-0014) |
| `POSTGRES_PASSWORD`, `REDIS_PASSWORD` | hasła bazy i kolejki |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET` | dostęp do Garage (dowody: HTML, screenshoty) |
| `GARAGE_RPC_SECRET`, `GARAGE_ADMIN_TOKEN`, `SEARXNG_SECRET` | sekrety Garage i SearXNG |
| `PROXY_URLS` | pula proxy dla scrapera, także kolektorów YouTube/TikTok (ADR-0015), pusta = połączenie bezpośrednie |
| `FETCH_ALLOWED_PRIVATE_HOSTS` | jedyne hosty w sieci prywatnej, które crawler może pobrać (sandbox demo); reszta musi być publiczna (ochrona SSRF) |
| `JWT_SECRET`, `ANALYST_PASSWORD`, `ADMIN_PASSWORD` | sekret sesji i hasła kont startowych (ADR-0016) |
| `CORS_ORIGINS` | originy dopuszczone do API i Socket.io |
| `RETENTION_DAYS_NO_FINDING` | retencja dokumentów bez findingu (ADR-0019, RODO) |
| `CLASSIFIER_THRESHOLD_M1/M2/M3` | progi startowe (zmienialne później w panelu Kalibracja) |

Reguły M2 (informacja o ryzyku): `config/m2_rules.yaml`. Taksonomie i zapytania discovery: `config/taxonomies.yaml`. Harmonogram kolektorów: `config/sources.yaml`.

## Testy

```bash
cd frontend && npm test                                   # testy jednostkowe (vitest)
cd frontend && npx playwright install chromium && npm run test:e2e   # E2E na działającym stosie (docker compose up)
```

E2E loguje się kontem `admin`, skanuje stronę demo i sprawdza, że konsola przeglądarki pozostaje czysta. Testy Pythona: `pytest services/<serwis>/tests`.

## Struktura repozytorium

Patrz ADR-0013 oraz `docs/CONCEPT.md` sekcja 13.

## Status implementacji i otwarte kwestie

`docker compose up` stawia cały stos (P0 ze specyfikacji). Niejasności i uproszczenia przyjęte podczas implementacji są spisane w [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) i [docs/IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md).
