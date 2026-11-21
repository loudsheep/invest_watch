# 0009. M2 risk disclosure rules as YAML configuration

- Status: Accepted
- Date: 2026-11-21

## Context

The task references an attachment with risk disclosure requirements that was not provided. The criteria must be usable now and replaceable later without code changes.

## Decision

Base the initial rule set on MiFID II art. 24(3) and Commission Delegated Regulation (EU) 2017/565 art. 44 (fair, clear and not misleading information; prominent indication of risks when referencing benefits; risk warning font size at least equal to the predominant font size; past performance and forecast disclaimers), plus the ESMA mandatory CFD risk warning.

Rules live in YAML under `config/`. Each criterion (`risk_warning_present`, `risk_prominence`, `profit_risk_balance`, `past_performance_disclaimer`, `forecast_disclaimer`, `cfd_esma_warning`, and more) defines:

- a detector type: regex, classifier, LLM or visual,
- a weight in the M2 score,
- a legal basis reference shown in the UI.

## Consequences

- When the official attachment arrives, only the YAML changes.
- Analysts see which criterion failed and why.
