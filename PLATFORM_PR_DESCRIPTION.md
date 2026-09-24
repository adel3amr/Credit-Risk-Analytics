# Governed Credit Risk reference platform foundation

The existing project has substantial validated model research, but its flat-file execution and demonstration role selector do not provide persistent decision lineage or backend access control. This change adds a modular reference platform around the preserved V5 methods.

It introduces canonical dated data, DQ and feature contracts, PostgreSQL-compatible migrations, trusted model loading, versioned runs and full facility traces, independent validation, portfolio movements/concentrations, registry/findings, separate override approval, audit evidence, an authenticated API and workflow UI, and deployment/CI configuration.

Frozen V5 and research methods/data remain unchanged. Institutional bank use is blocked, and research challengers are not promoted. The newest baseline was independently reconciled before implementation.

Validation: 93 tests pass locally; existing Streamlit role/filter checks pass; actual API HTTP startup succeeds; 5,172-facility shadow scoring matches PD/LGD numerically and stages exactly. The disclosed maximum EAD rounding difference is one cent per facility. Dependency audit reported no known vulnerabilities at scan time. Source hashes and corrupted-input rejection were exercised during workspace recovery.

Remaining qualification: PostgreSQL/container execution, hosted platform CI, real-browser QA, institution data/feature availability, independent model approval and deployed security controls. Do not describe this change as a bank-certified or institution-production-ready release.
