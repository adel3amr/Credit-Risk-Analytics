# Requirement-to-evidence register

| Requirement | Methodology / implementation | Independent evidence | Findings / disposition |
|---|---|---|---|
| Newest baseline first | ae9942a → d50d6f8 reconciliation | platform_evidence/independent_reconciliation.json, research_recalculated.json | P01, P02 |
| Preserve frozen risk | src/ unchanged; artifacts.py/risk.py adapter | 5172 facility shadow, original tests | P06 rounding disclosed |
| Canonical data and feature availability | domain.py/contracts.py + generated JSON contract | Missing/outcome/future/orphan/duplicate tests | P05 corrected; P02 remains |
| Persistence and lineage | schema/migration + immutable traces | Database mutation, terminal run, backup tests | P04 remediated; P07 open |
| Role enforcement and audit | security.py/audit.py | Auth/RBAC/expiry/revocation/chain tests | P03 remediated; P09 open |
| Overrides | Separate original/proposal/approval | Same-person/duplicate/role rejection tests | Controlled reference only |
| Validation and monitoring | Independent validation.py | ECL/outcome/movement/tail-denominator tests | Synthetic-only limitation |
| Reproducibility | pinned lock + scripts/run_v5.py + platform_shadow.py | 93 tests; HTTP startup; legacy AppTest | PostgreSQL/browser pending |
| Deployment | compose, Dockerfile, platform workflow | Source/config inspection; no actual hosted platform success | P07–P09 open |
