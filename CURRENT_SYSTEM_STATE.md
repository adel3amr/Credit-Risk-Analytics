# Current system state — final red-team release candidate

Baseline: `33d3ad4670bd7c5cfad31ac5d6b54f8f42224180`. Review branch:
`review/final-red-team-release`. This document is the current navigation point;
historical reports retain their original populations, dates and conclusions.

| Component | Current status | Governing evidence |
|---|---|---|
| V5 logistic PD and facility gradient-boosting LGD | ACTIVE REFERENCE, institution BLOCKED | `credit_platform/artifacts.py`, source/artifact hash manifest |
| V5 staging, internal nine-month EWS policy, ratings, EAD and ECL | ACTIVE REFERENCE | `src/`, `credit_platform/risk.py`, versioned run traces |
| R2 two-stage tail research | HISTORICAL RESEARCH, not promoted | `lgd_research/` |
| S1 synthetic bank and conditional-mean diagnosis | HISTORICAL RESEARCH | `synthetic_bank/`, `research_diagnostics/` |
| Hidden-state oracle and blanket downturn sensitivity | RESEARCH ONLY; prohibited for booked results | `LGD_DOWNTURN_FINAL_DECISION.md` |
| Economic S2 successor | HISTORICAL CHALLENGER, not promoted | `economic_lgd/DECISION.md` |
| `s2-r1-monotone-gb-1` | CHALLENGER_NOT_PROMOTED | `s2_remediation/DECISION.md` |
| Continuous post-R1 calibration | REJECTED | `lgd_hardening/DECISION.md` |
| Recovery evidence capture/domain/release checks | IMPLEMENTED; required operational observations absent | `lgd_hardening/capture.py`, `domain.py`, `release.py` |
| API, SQLite persistence, audit and deterministic Copilot | REFERENCE; qualified within tested scope | `final_red_team_evidence/`, tests |
| External LLM provider | OPTIONAL, disabled by default; NOT QUALIFIED | `GENAI_RISK_AND_CONTROLS.md`, findings RT-11 |
| Institutional deployment | BLOCKED | `FINAL_RELEASE_READINESS.md` |

## Chronology and interpretation

V5 -> independent validation -> tail research -> conditional-mean clarification ->
S1 -> economic S2 -> S2-R1 -> post-R1 hardening -> software red-team review.
The final review changes software controls and evidence, not model parameters,
methodology, datasets, promotion decisions or frozen tolerances.

Retrospectively selecting realized LGD above 75% selects positive outcome noise;
its negative realized bias is not by itself an unbiased test of conditional-mean
calibration. It is still reported. R1 has independent additional failings:
predicted 80–100% band overprediction, guarantee/segment uncertainty, scenario
equivalence failures, and 327/6,000 downside support violations in the retired
promotion population. These remain material even though scenario reversals are zero.
The new review recalculates already-known prediction exports; it is not a fresh
holdout or external model-validation team.

PD reference H population: 3,000 borrowers, 102 defaults, observed rate 3.40%,
AUC 0.759455, Gini 0.518911, KS 0.408497, Brier 0.030003, log loss 0.128562.
These values supersede prompt approximations for this exact population only.

Reference EAD uses drawn term loans, full OVD limits and 20%/50%/100% trade CCFs.
The project backstops are **>=30 DPD Stage 2** and **>=90 DPD Stage 3**, with Stage 3
precedence. Internal Watchlist is distinct from SICR; nine-month persistent
multi-signal deterioration creates Stage 2 under project policy. No external
regulatory attribution is made. Stage 3 ECL uses facility LGD times EAD; collateral
is represented through LGD, not deducted a second time. V5 averages scenario PD
before its lifetime transform; S2 shadow scenario ordering remains separately labelled.

## Operational scope

The API implements one shared institutional workspace: a permitted read role can
read all records there. It does not implement per-user ownership or multiple tenants.
Copilot refusal text is not a tenant boundary. Do not deploy for confidential
multiple-tenant use. The deterministic provider retrieves governed outputs; the
external provider has not demonstrated equivalent safety/grounding.

Hosted baseline evidence changed: on 1 October GitHub run 36838731071 passed
PostgreSQL migrations/full shadow/audit and Docker build for the exact baseline.
This is evidence for that commit, not final-branch Compose runtime, restore, browser,
performance, penetration testing, or institutional approval. The separate V5 job
36838731545 failed because it installed only V5 dependencies while collecting
platform tests. The review fixes its dependency and artifact-preparation order.
