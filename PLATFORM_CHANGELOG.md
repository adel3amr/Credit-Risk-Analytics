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
