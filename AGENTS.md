# AGENTS.md

Guidance for AI coding agents and humans working in this repository.

## Source of truth

- `docs/CONCEPT.md` - solution concept (Polish).
- `docs/adr/` - architecture decisions (MADR). Do not contradict an accepted ADR; propose a new ADR that supersedes it instead.

## Working rules

- Stay within one service per change where possible; respect service boundaries described in ADR-0013.
- Secrets only in `.env`; never commit real secrets. Keep `.env.example` up to date.
- Prefer dependencies licensed MIT, Apache 2.0 or BSD. Do not add GPL or AGPL dependencies.
- No `console.log` left in frontend code (ESLint `no-console`).
- Code, comments and commit messages in English. UI strings in Polish via i18n files.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short imperative description
```

- Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
- Scope: service or area, for example `api`, `scraper`, `ai`, `scheduler`, `frontend`, `common`, `infra`, `config`, `docs`.
- Description: lowercase, imperative mood, no trailing period, max ~72 characters.
- Breaking changes: `type(scope)!: ...` and a `BREAKING CHANGE:` footer.

Examples:

```
feat(scraper): add youtube collector
fix(ai): handle empty llm response
docs(adr): add proxy pool decision
```
