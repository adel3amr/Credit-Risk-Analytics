# Classified change log

| Class | Change | Evidence / scope |
|---|---|---|
| DOCUMENTATION | Baseline reconciliation, architecture, roadmap and full-platform reports | d50d6f8 precedes implementation |
| DATA ARCHITECTURE | Strict canonical dated snapshots and source hashes | domain.py, contracts.py; no historical dataset rewrite |
| DATABASE | Relational schema, migration, constraints, immutable evidence and least-privilege grants | schema.py, migrations/, deployment/grants.sql |
| MODEL IMPLEMENTATION | Trusted artifact build/load and frozen V5 adapter | artifacts.py, risk.py; no new parameters or challenger |
| BUG FIX | Adapter trade EAD rounded to cents; correct contract distinction for concentration fractions, binary key-person flag and audit ordinal | Full shadow and source-generator inspection |
| VALIDATION | Independent ECL arithmetic, LGD metrics/tails/denominators, movements, support, shadow comparisons | validation.py, platform_shadow.py, tests |
| API | Versioned input validation, explicit errors and run idempotency | api.py |
| SECURITY | Expiring hashed credentials, backend RBAC and two-person approvals | security.py, adverse tests |
| GOVERNANCE | Registry, append-only findings, overrides, audit chain and blocked bank gate | governance.py, service.py, audit.py |
| OBSERVABILITY | Readiness, structured request logs, identifiers | api.py, deployment/logging.json |
| UI/UX | Authenticated workflow UI with source/decision inspection | credit_platform/static/; browser QA pending |
| INFRASTRUCTURE | Docker/PostgreSQL composition and CI checks | Not locally deployed or hosted-verified |
| METHODOLOGY | None promoted or changed | Frozen methodology and historical outputs preserved |

The new field contract rejects missing canonical scoring inputs instead of relying on notebook imputation/fill defaults. This is an explicit data-admission control, not a model refit or method change. Historical notebook behavior remains reproducible.

## Continued validation hardening

BUG FIX / VALIDATION: independent reconciliation now rejects invalid stages, non-finite and out-of-range values; only successful runs may be validated. Full output hashes are verified, with canonical Python ordering independent of SQL collation. Six additional adverse cases bring the suite to 93 passing tests.

VALIDATION / DATA: frozen hash gate now includes borrower and conduct inputs. Resume exposed a malformed development database and truncated borrower CSV/figure; damaged copies were preserved, exact source data reproduced by frozen seed, and a new migrated database successfully replayed the full portfolio. No model or generator relationship was changed.

## LGD follow-up — 24 September 2026

- BUG FIX: reject nonfinite and incomplete LGD model output before clipping;
  failed runs write no partial decisions. Preserve approved finite clipping.
- VALIDATION / RESEARCH: fixed-protocol, 4,096-draw conditional-mean diagnostic
  separates simulator expectation from realized severe-outcome selection. No
  model retraining, generator alteration, calibration or challenger promotion.
- DOCUMENTATION: LGD_REMEDIATION_REPORT.md supersedes an undifferentiated reading
  of retrospective tail bias while retaining adverse calibration/support findings.

## Synthetic Bank S1 — 25 September 2026

DATA / DATA ARCHITECTURE: linked whole-platform dataset, separated targets, dated
quality capture, shared borrower recovery shocks and explicit collateral allocation.
RESEARCH / VALIDATION: fixed candidates, chronological disjoint cohorts, single final
evaluation and independent cashflow checks. No incumbent method or artifact changed.
DOCUMENTATION: full results and remaining adverse tail findings in synthetic_bank/README.md.

## Final LGD disposition — 25 September 2026

VALIDATION / RESEARCH: independent S1 conditional-mean integration, borrower-cluster
uncertainty, ex-ante segment calibration, noise floor, current context sensitivity
and shadow ECL impacts. Distinguishes actual 8000-case governed fit from 6000-case
benchmark. One targeted specification experiment (remove industry, add rate), kept
RESEARCH. DOCUMENTATION: category 3 disposition, corrected tail interpretation and
retained current-transfer finding. No active methodology/artifact or source data change.

## Downturn calibration/control decision — 25 September 2026

RESEARCH / VALIDATION: six-mechanism paired DGP attribution, canonical/captured-state
proxies, development-only bounded regime calibration and normal/downturn evaluation.
MODEL IMPLEMENTATION / GOVERNANCE: standalone scenario sensitivity control preserves
base output and rejects booking/production use. This is not an active methodology
change. DOCUMENTATION: explicit NO/category E decision, no invented state feed or
scenario weights. Eleven additional tests; 122 pass; all historical data retained.

Change-control clarification: fractional-logistic regime calibration is a new
METHODOLOGY in RESEARCH ONLY, identified as `s1-regime-calibration-1`. It is not
classified as a coding fix and has not entered the governed scoring path.

## Release closeout and Credit Risk Copilot — 27 September 2026

- API / UI/UX: added borrower, portfolio, credit-review and model-risk Copilot workflows grounded in existing run and validation evidence.
- SECURITY / GOVERNANCE: allowlisted tools only, no generated SQL, inherited RBAC, injection refusal, fail-closed missing evidence, immutable metadata audit, explicit human-review status and external-provider opt-in.
- DATABASE: additive migration `0002` stores request/provider/prompt/tool/source hashes and metadata without raw question/answer retention.
- BUG FIX / DATABASE: replaced the malformed default development database with a clean schema-`0002` initialization; preserved the retired file hash and Git history.
- VALIDATION: six-case benchmark and API tests cover grounding, numerical consistency, attribution, authorization, tool choice, missing evidence and adversarial input.
- DOCUMENTATION: final state, architecture, operating guide, risks/controls, readiness and limitations updated.
- METHODOLOGY: none. No risk model, policy, dataset or booked ECL changed.
