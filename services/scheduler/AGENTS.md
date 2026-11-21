# AGENTS.md - scheduler service

Read the root [AGENTS.md](../../AGENTS.md) first. Rules here are specific to this service.

- Scope: change only `services/scheduler` (plus `common/` and `config/` when a contract changes). Do not import code from other services; talk through Celery task names and Redis (ADR-0013).
- Lint: `ruff check .`. Tests: `pytest tests` (add tests next to behavior you change).
- Config and rules live in YAML under `config/`; do not hard-code them here.
- Log with `investwatch_common.logging.get_logger`; no `print`.
