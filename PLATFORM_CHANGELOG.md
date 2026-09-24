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
