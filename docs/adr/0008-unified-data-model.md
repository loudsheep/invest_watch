# 0008. Unified finding model, cases and analyst feedback loop

- Status: Accepted
- Date: 2026-11-21

## Context

The specification requires an aggregator that merges results of modules 1, 2 and 3 into unified objects, and the ability to change record status. The calibration panel must show the effect of the threshold on false positives and false negatives, which needs ground truth.

## Decision

Core entities: `source`, `document`, `entity`, `entity_alias`, `mention` (roles: `advertised_firm`, `advertiser`, `publisher`, `offering_party`), `finding`, `case`, `label`, `audit_log`, `user`.

- `finding` is a single type for all modules: `module`, `score`, `model_version`, `prompt_version`, `evidence` (quotes with offsets), `explanation`, `details` (JSONB for module-specific fields), `status`.
- `case` aggregates findings from multiple modules and documents around one entity.
- Status flow: `new -> in_review -> confirmed | dismissed -> escalated`.
- Analyst decisions (`confirmed`, `dismissed`) are stored as labels and used as ground truth for live precision, recall and FP/FN in the calibration panel, and as training data for retraining.

## Consequences

- One API and one UI component set serve all modules.
- Calibration reflects real analyst decisions instead of synthetic numbers.
