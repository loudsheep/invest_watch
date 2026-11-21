# InvestWatch

Autonomiczny system nadzoru treści finansowych w sieci. Koncepcja: [docs/CONCEPT.md](docs/CONCEPT.md). Decyzje architektoniczne: [docs/adr/](docs/adr/).

## Wymagania sprzętowe

- Docker + Docker Compose.
- Referencyjnie: MacBook M3 Pro, 36 GB RAM. Minimum: 16 GB RAM, 4 rdzenie (Ollama + Playwright + Postgres razem są ciężkie).
- Dla przyspieszenia LLM na macOS: natywna Ollama na hoście (patrz `.env.example`, `LLM_BASE_URL`), bo Docker na macOS nie ma dostępu do GPU/Metal.

## Quick Start

```bash
cp .env.example .env                              # wpisz LLM_API_KEY (OpenRouter)
docker compose --profile migrate up migrate       # migracje + seed rejestru i użytkowników
docker compose up -d garage
./garage/init.sh                                   # jednorazowo: layout, klucz dostępu, bucket
docker compose up
```

- Dashboard: http://localhost:47173
- API: http://localhost:47800 (health: `/health`)
- Garage (S3 API, ewentualnie do podglądu przez `aws s3 --endpoint-url`): http://localhost:47900
- Domyślni użytkownicy (dev): `analyst` / `admin`, hasło `changeme-dev` (zmień `JWT_SECRET` i hasła poza środowiskiem lokalnym).

## Konfiguracja serwisów

Wszystkie zmienne w `.env` (skopiowane z `.env.example`). Kluczowe:

| Zmienna | Rola |
|---|---|
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | endpoint zgodny z OpenAI: OpenRouter (domyślnie) lub Ollama `/v1` (`--profile ollama`, ADR-0002, ADR-0014) |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET` | dostęp do Garage (dowody: HTML, screenshoty) |
| `PROXY_URLS` | pula proxy dla scrapera (ADR-0015), pusta = połączenie bezpośrednie |
| `JWT_SECRET` | sekret sesji (ADR-0016) |
| `RETENTION_DAYS_NO_FINDING` | retencja dokumentów bez findingu (ADR-0019, RODO) |
| `CLASSIFIER_THRESHOLD_M1/M2/M3` | progi startowe (zmienialne później w panelu Kalibracja) |

Reguły M2 (informacja o ryzyku): `config/m2_rules.yaml`. Taksonomie i zapytania discovery: `config/taxonomies.yaml`. Harmonogram kolektorów: `config/sources.yaml`.

## Struktura repozytorium

Patrz ADR-0013 oraz `docs/CONCEPT.md` sekcja 13.

## Status implementacji i otwarte kwestie

`docker compose up` stawia cały stos (P0 ze specyfikacji). Niejasności i uproszczenia przyjęte podczas implementacji są spisane w [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) i [docs/IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md).
