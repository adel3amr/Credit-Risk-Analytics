# Platform gap assessment

| Priority | Domain | Verified gap | Required action / acceptance |
|---|---|---|---|
| P0 | Evidence integrity | Local research CSV truncated | Use committed hashes; reject mismatches before fitting; atomic new artifacts |
| P0 | Model use | Synthetic-only validation; severe-loss weakness; absent research inputs | Reference-only model registry; fail closed for bank use; retain adverse findings |
| P0 | Security | UI role picker has no backend enforcement | API credential authentication and backend permissions; no public borrower data |
| P1 | Data | Flat files; no immutable history or source contract | Canonical dated borrower/facility snapshots with source and hashes; DQ failures recorded |
| P1 | Persistence | No migrations or database | PostgreSQL-compatible relational schema, migration, transaction tests and restore guide |
| P1 | Run lineage | Rebuild overwrites output files | Append-only result history, input/model/config hashes and run IDs |
| P1 | Service | No API | Strict request schema; explicit errors; limited payloads; auth tests |
| P2 | Models | Notebook training; unsafe unrestricted pickle loader | Trusted local artifact manifest verification; frozen reference adapter |
| P2 | Validation | Strong offline research, little operational reuse | Independent reconciliation and reusable outcome metrics; visible support alerts |
| P3 | Governance | Findings/docs exist without operational records | Versioned registry, findings events, two-person overrides and audit trail |
| P3 | Observability | No service health or structured logs | Correlation IDs, latency/status logs, readiness and audit verification |
| P4 | Deployment/UI | Local Streamlit only | Authenticated workflow UI, container/API/PostgreSQL composition, CI service tests |

No evidence supports new LGD research without new information. Institution onboarding, empirical validation, real data capture, TLS/identity integration and independent security review remain deployment gates, not tasks that synthetic generation can satisfy.
