# Publication readiness and validation map

Status: **READY FOR PUBLIC RESEARCH RELEASE**  
Review date: **22 October 2026**

This is the front-door map for reviewers who want to understand what is current, what is historical, how to run the project, and where the model challenges and validation evidence live.

## Current system

The consolidated platform covers:

```text
borrower/facility data
→ PD and internal rating
→ EWS / Watchlist / SICR
→ IFRS 9-style staging
→ facility LGD + EAD
→ scenario-aware ECL
→ portfolio / concentration analytics
→ validation and model-risk evidence
→ governance / audit / overrides
→ governed Risk Copilot
```

Public/default branch: `main`  
Integration lineage: `release/final-institutional-platform`  
Verified full-workflow qualification: `502b1e8c37d9397c6df8e9ed8efbb3e7c085e658` (22 October 2026, before public-launcher change)

The publication branch preserves the histories of the reviewed red-team release, Marginal Interest research, WN-1 workout engine and the Streamlit/Copilot interface. No historical research branch was flattened or deleted.

## Reproducibility evidence

The clean hosted workflow at the functional baseline reported:

- **240 passed, 1 upstream warning**;
- V5 release checks **30/30**;
- **5,172** reference facilities reconciled;
- EAD **2,091,914,075.83**;
- ECL **45,265,972.04**;
- **0** stage mismatches;
- audit chain **VERIFIED**;
- fresh PostgreSQL migrations and shadow calculation **PASS**;
- WN-1 relational PostgreSQL persistence **VERIFIED**;
- Streamlit headless startup **PASS**;
- Docker image build **PASS**.

A fresh runner regenerates ignored reference CSV/output/model artifacts before testing; the repository is not dependent on files from the author's workstation.

## Challenge and validation history

| Phase | What was challenged | Outcome | Primary evidence |
|---|---|---|---|
| V5 reference | PD/LGD/EWS/staging/EAD/ECL implementation and release integrity | Reference implementation frozen | `docs/V5_*.md`, `MODEL_INVENTORY.md` |
| Whole-repository independent review | arithmetic, reconciliation, historical evolution, dashboard consistency, LGD tails/support | implementation validated with observations; LGD issues retained | `validation_review/`, `FINAL_INDEPENDENT_VALIDATION_REPORT.md` |
| LGD tail programme / R2 | severe-loss bias, guarantee support, data vs model limitations, challengers/oracle diagnostics | challenger improved RMSE but did not clear promotion | `lgd_research/` |
| S1 linked synthetic bank | borrower/facility/workout linkage and population-transfer diagnosis | genuine context/transfer issue identified; no shortcut promoted | `synthetic_bank/`, `LGD_FINAL_RESOLUTION.md` |
| Downturn resolution | hidden-state/context mechanism and deployable proxies | oracle information diagnostic only; blanket overlay rejected | `research_diagnostics/downturn_resolution/`, `LGD_DOWNTURN_FINAL_DECISION.md` |
| Observable-economic S2 | explicit prediction-time economics and scenario LGD | aggregate improvement, residual scenario/support issues; not promoted | `economic_lgd/` |
| S2-R1 | constrained challenger, scenario order, support/domain gates | retained challenger but promotion gates still failed | `s2_remediation/` |
| Post-R1 hardening | calibration, data lineage, domain boundaries, precision/support | proposed continuous calibration rejected; no final holdout reopened | `lgd_hardening/` |
| Marginal Interest | incremental value of impaired-facility accrued/suspended interest | interest-specific incremental value inconclusive | `marginal_interest/` |
| WN-1 workout engine | dated component recovery architecture, cure/recovery/security/cost/macro evidence | component challenger blocked by calibration/support/selection findings | `workout_vnext/`, `WORKOUT_PLATFORM_CLOSEOUT.md` |
| Final red-team / platform consolidation | software controls, schema, lineage, input handling, Copilot, PostgreSQL/Docker/UI qualification | defects fixed; evidence preserved; final reference workflows green | `FINAL_RED_TEAM_REPORT.md`, `FINAL_INSTITUTIONAL_PLATFORM.md` |
| Full-context Risk Copilot | borrower drivers, customer/industry concentration, LLM grounding and known narrative errors | exact analytics deterministic; Ollama gets richer governed context; regression guards added | `GENAI_COPILOT_GUIDE.md`, `tests/platform/test_final_integration.py` |

## Current reference vs research-only

The frozen V5/reference scoring path remains the controlled baseline for the integrated reference calculation. Research challengers are **not silently substituted** into it. Rejected/blocked models remain in the repository with their actual results.

This distinction is deliberate:

- **REFERENCE** = used by the governed reference calculation;
- **RESEARCH / CHALLENGER** = studied, preserved, not promoted;
- **ORACLE / DIAGNOSTIC** = intentionally non-deployable information used to diagnose limitations;
- **BLOCKED / REJECTED** = failed one or more promotion/transfer/support/calibration gates.

See [MODEL_INVENTORY.md](MODEL_INVENTORY.md) for model-by-model status.

## How to run

For a clean workstation follow [REPRODUCIBILITY.md](REPRODUCIBILITY.md). The shortest Windows demo sequence is also in [README.md](README.md).

No paid LLM is needed. The default Copilot is deterministic; local Ollama can be enabled for richer narrative reasoning.

## Documentation map

### Platform / engineering
- [README.md](README.md)
- [FINAL_INSTITUTIONAL_PLATFORM.md](FINAL_INSTITUTIONAL_PLATFORM.md)
- [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [DEPLOYMENT_OPERATIONS.md](DEPLOYMENT_OPERATIONS.md)

### Models / risk methodology
- [MODEL_INVENTORY.md](MODEL_INVENTORY.md)
- [MODEL_FEATURE_CONTRACTS.md](MODEL_FEATURE_CONTRACTS.md)
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- [LIMITATIONS.md](LIMITATIONS.md)

### Validation / challenge
- [FINAL_INDEPENDENT_VALIDATION_REPORT.md](FINAL_INDEPENDENT_VALIDATION_REPORT.md)
- [FINAL_RED_TEAM_REPORT.md](FINAL_RED_TEAM_REPORT.md)
- [SYSTEM_FINDINGS_REGISTER.md](SYSTEM_FINDINGS_REGISTER.md)
- [validation_review/PROJECT_WIDE_DECISION.md](validation_review/PROJECT_WIDE_DECISION.md)
- [lgd_research/EXECUTIVE_RESEARCH_SUMMARY.md](lgd_research/EXECUTIVE_RESEARCH_SUMMARY.md)
- [LGD_FINAL_RESOLUTION.md](LGD_FINAL_RESOLUTION.md)
- [LGD_DOWNTURN_FINAL_DECISION.md](LGD_DOWNTURN_FINAL_DECISION.md)
- [WORKOUT_PLATFORM_CLOSEOUT.md](WORKOUT_PLATFORM_CLOSEOUT.md)

### GenAI
- [GENAI_COPILOT_GUIDE.md](GENAI_COPILOT_GUIDE.md)
- [GENAI_ARCHITECTURE.md](GENAI_ARCHITECTURE.md)
- [GENAI_RISK_AND_CONTROLS.md](GENAI_RISK_AND_CONTROLS.md)

## Publication claim

A precise public description is:

> A full-stack Credit Risk research platform integrating borrower/facility analytics, PD/rating, EWS/Watchlist/SICR, IFRS 9-style staging and ECL, LGD/EAD, portfolio monitoring, independent validation, governance/audit and a grounded local Risk Copilot, with the complete challenger and remediation history preserved.

The project uses synthetic/publicly informed data and is intended for research, learning and professional demonstration.
