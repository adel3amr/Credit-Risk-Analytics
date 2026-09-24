# Executive architecture summary

The project now has an additive reference-platform implementation on `platform/production-foundation`, rooted in the newest completed research at ae9942a. Frozen V5 and research history remain unchanged.

Implemented: dated canonical borrower/facility snapshots, data-quality checks and feature contracts; PostgreSQL-compatible schema/migrations; governed model loading; source/model/policy/run hashes; PD→EWS/staging→LGD→EAD→ECL decision traces; portfolio concentrations and movements; registry/findings/validation; controlled overrides; audit chain; authenticated API and workflow UI; operational health/logging; container and CI configuration.

Validation: 93 passing tests, successful legacy dashboard checks, actual API HTTP startup, a 5,172-facility shadow run with identical stages and numerically identical PD/LGD, independently reconciled ECL, and a disclosed one-cent EAD source-rounding bound. A dependency scan found no known vulnerabilities at scan time.

LGD remains unresolved for institutional use. R2 two-stage RMSE improves to 15.69 percentage points, but realized >75% bias remains −12.05 points over 536 cases and required quality inputs are unavailable. The registry and API retain blocked production status.

PostgreSQL/container execution and new browser QA could not be completed under this environment. TLS/SSO/MFA, institution data capture, real recovery validation and independent operational/security approval remain qualification work. This is an implemented and tested production-oriented **reference foundation**, not a certified bank system or a completed institutional deployment.

Start with REPRODUCIBILITY.md, then FINAL_INDEPENDENT_VALIDATION_REPORT.md and FINAL_PRODUCTION_READINESS.md. Full trace examples are in platform_evidence/worked_cases.json.
