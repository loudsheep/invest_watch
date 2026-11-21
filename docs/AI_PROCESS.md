# Proces wytwarzania z asystentami AI

Projekt powstał w całości z asystentem kodowania (Claude Code) według stałego, opisanego procesu. Decyzje: [ADR-0012](adr/0012-ai-assisted-development-process.md).

## Zasady

1. **Spec-driven.** [`CONCEPT.md`](CONCEPT.md) jest źródłem prawdy, a każda istotna decyzja trafia do ADR ([`adr/`](adr/), format MADR). Agent nie zmienia zaakceptowanego ADR - proponuje nowy, który go zastępuje (np. [ADR-0021](adr/0021-frontend-styling-and-default-llm.md)).
2. **Instrukcje dla agenta w repozytorium.** `AGENTS.md` / `CLAUDE.md` w katalogu głównym i w każdym serwisie opisują konwencje, granice modułu, komendy i standard commitów (Conventional Commits).
3. **Grilling przed kodem.** Kluczowe decyzje architektoniczne były wymuszane serią pytań doprecyzowujących, a wynik zapisywany jako ADR zanim powstał kod.
4. **Cykl pracy:** specyfikacja lub issue -> implementacja przez AI -> testy -> review AI (zgodność ze standardami i ze specyfikacją) -> review człowieka -> merge.
5. **Reguły jako konfiguracja.** Kryteria M2, taksonomie, źródła i harmonogramy są w YAML (`config/`), więc zmiana wymagań (np. nowy załącznik od UKNF) nie wymaga zmian w kodzie.
6. **Prompty LLM jako kod.** Wersjonowane (`prompt_version`), wynik walidowany schematem Pydantic.

## Bramki jakości (CI, `.github/workflows/ci.yml`)

| Bramka | Narzędzie |
|---|---|
| Styl i błędy | `ruff`, `eslint` (`no-console`) |
| Testy | `pytest` |
| Podatności zależności | `pip-audit`, `npm audit` (build pada przy podatnościach) |
| Podatności repozytorium i obrazów | Trivy |
| Sekrety | gitleaks, sekrety wyłącznie w `.env` |

## Granice zaufania do AI

- Nic nie jest commitowane ani wypychane bez decyzji człowieka.
- Każdy ADR i zmiana kontraktu między serwisami przechodzi review człowieka.
- Rekomendacje systemu (findingi) są oceną dla analityka, nie decyzją: status zmienia człowiek, a decyzje trafiają do audit logu i zbioru etykiet.
