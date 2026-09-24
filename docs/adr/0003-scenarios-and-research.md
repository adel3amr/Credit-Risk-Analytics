# ADR 0003 — Preserve scenario and model methodology

## Context

R2 research improves aggregate LGD error but lacks live feature availability and robust tail resolution. Existing macro relationships are synthetic assumptions.

## Alternatives

Promote the best RMSE challenger; add a tail uplift; redesign scenarios; or retain reference methods with explicit blockers.

## Decision

Retain V5 logistic PD, GB LGD, staging/EWS/rating, CCF and ECL conventions. Snapshot the frozen scenario CSV and sensitivities into each run. Do not repeat completed challenger work without a new hypothesis/information source. Research remains separate and blocked in registry.

## Consequences

The platform improves traceability and controls without implying empirical bank validity. Longitudinal ingestion and movement analysis are available; new economic simulator relationships and external macro calibration require a separately evidenced governed version.
