# 0016. Authentication, roles and audit log

- Status: Accepted
- Date: 2026-11-21

## Context

The dashboard handles evidence and status changes in a supervisory context. Security is evaluated. A full identity provider is too heavy and risky for the demo.

## Decision

- JWT in an httpOnly cookie.
- Roles: `analyst` (review, status changes) and `admin` (threshold, retraining, source configuration).
- Users seeded from `.env`, passwords hashed with Argon2.
- Authentication behind an interface so it can be replaced with OIDC (for example Keycloak) during deployment at UKNF.
- An audit log records who changed what and when: statuses, thresholds, retraining, access to raw evidence.

## Consequences

- Clear deployment path to the regulator's identity infrastructure.
- Every supervisory action is traceable.
