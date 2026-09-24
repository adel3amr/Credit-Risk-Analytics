# Controlled platform roadmap

This programme implements reference deployment capability; it does not grant bank provisioning approval.

| Release | Scope | Dependencies | Acceptance | Recovery / risk |
|---|---|---|---|---|
| Foundation 0.1 | Canonical snapshots, migrations, hashes, DQ, contracts, frozen risk adapters and run tracing | Reconciled ae9942a baseline | Reproduced metrics; snapshot/run identity; strict invalid-input tests; independent facility arithmetic | Additive tables; restore verified backup; historical source untouched |
| Service 0.2 | API, credential/RBAC, findings, two-person overrides, audit, registry, validation/monitoring | Foundation | Unauthorized access denied; roles enforced; failures persisted; no production bypass | Revoke credentials; disable writes; restore prior app with compatible schema |
| Reference deployment 0.3 | Workflow UI, Docker/PostgreSQL composition, CI, health/logs, reproduction and worked cases | Service | API/UI tests, migration/restore checks, reference portfolio reconciliation | Backups and schema checks before upgrade; deployment infrastructure availability remains explicit |
| Institution qualification | Real source mapping, capture of security/guarantor quality, approved policies, time-split bank validation, TLS/SSO, independent security review | Institution data, infrastructure and governance | Data/model/feature/security/operational gates supported by institution evidence | Remains BLOCKED; cannot be satisfied by generated evidence |

No automatic model promotion, unvalidated macro calibration, forced LGD winner, distributed queues or microservices. Longitudinal support first stores independently dated canonical snapshots and transition history; economic generator expansion requires a separate justified hypothesis. Existing longitudinal conduct and recovery generators remain reference sources.

## Implementation status after local validation

Foundation 0.1 and Service 0.2 have implemented reference code, with 93 tests passing. Reference deployment 0.3 has configuration, actual local HTTP startup and shadow evidence; hosted PostgreSQL/container and real-browser qualification remain open. Institution qualification is BLOCKED. This status supersedes any implication that the entire roadmap is complete.
