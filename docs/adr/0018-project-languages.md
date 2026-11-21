# 0018. Project languages

- Status: Accepted
- Date: 2026-11-21

## Decision

- Polish: dashboard UI (via i18n files such as `pl.json`), README, `docs/CONCEPT.md`, `docs/AI_PROCESS.md`, presentation.
- English: code, comments, commit messages, ADRs, `AGENTS.md` / `CLAUDE.md`.
- LLM prompts: instructions in English, analyzed content in Polish, evidence quotes kept in the original language.

## Consequences

- Jury and UKNF analysts read Polish; engineering artifacts follow industry convention and work best with AI assistants.
