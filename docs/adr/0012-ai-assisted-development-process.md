# 0012. AI-assisted development process and CI gates

- Status: Accepted
- Date: 2026-11-21

## Context

20% of the score is for a development process based on existing standards and a described, standardized way of building software with AI assistants. Library security is also evaluated.

## Decision

- Spec-driven development: `docs/CONCEPT.md` is the source of truth, ADRs record decisions.
- `AGENTS.md` (and `CLAUDE.md` pointing to it) in the root and in each service: conventions, commands, module boundaries, commit standard.
- Commits follow Conventional Commits: `type(scope): short imperative description`, types `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`, `build`.
- Workflow: spec or issue -> AI implementation -> tests -> AI review (standards and spec compliance) -> human review -> merge.
- CI on GitHub Actions: `ruff`, `eslint` (`no-console`), `pytest`, `vitest`, `pip-audit`, `npm audit`, Snyk or Trivy (including images), gitleaks.
- LLM prompts are versioned in the repository with a small evaluation test set.
- The process is described in `docs/AI_PROCESS.md` and on one presentation slide.

## Consequences

- The process is visible in the repository, not only claimed in the presentation.
- CI gates double as evidence for the library security criterion.
