# 0001. Record architecture decisions

- Status: Accepted
- Date: 2026-11-21

## Context

The project is built in 24 hours with heavy use of AI coding assistants. Assistants and humans need a single, durable source of truth for why the system looks the way it does. The jury also scores how standardized the AI-assisted development process is.

## Decision

Record every significant decision as an ADR in `docs/adr/` using the MADR format. `docs/CONCEPT.md` holds the overall solution concept and links to ADRs for detail.

## Consequences

- Assistants get stable context and do not re-litigate settled decisions.
- Changing a decision means adding a new ADR that supersedes the old one.
