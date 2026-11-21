# 0017. Local demo-sites sandbox

- Status: Accepted
- Date: 2026-11-21

## Context

Hackathon networks are unreliable and real pages can change overnight. The live demo must not depend on external availability.

## Decision

A `demo-sites` container serves prepared pages of fictional entities: a finfluencer blog with affiliate codes, a broker landing page with a tiny risk disclaimer, an unlicensed family office offering, and a lookalike domain. Only fictional names are used; no real firm is imitated.

These pages serve as:

- a deterministic demo scenario that works offline,
- an end-to-end test suite for collectors and classifiers,
- labeled examples for calibration.

## Consequences

- The demo starts with a real URL and falls back to `demo-sites` seamlessly.
