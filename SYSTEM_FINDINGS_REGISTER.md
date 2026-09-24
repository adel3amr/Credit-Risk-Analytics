# System-wide findings register

Older and closed findings are preserved in validation_review/FINDINGS_REGISTER.csv and lgd_research/LGD_FINDINGS_REGISTER.md. New records are additive.

| ID | Component / severity | Evidence and root cause | Remediation / retest | Status / residual risk |
|---|---|---|---|---|
| P01 | Integrity / High | Working R2 development exact prefix, 596 lines missing; cause not established | Isolated committed checkout, frozen hash gate, atomic new platform JSON writes | Contained; original workspace preserved; do not assert root cause |
| P02 | LGD / High | H and R2 severe residual bias; research quality features missing | No promotion; registry/API bank block; source/outcome monitoring | OPEN; institution evidence required |
| P03 | Security / High | Legacy role selector lacks backend control | New API credentials/RBAC; denial/revocation/approval tests | Remediated for reference API; legacy demo limitation retained |
| P04 | Lineage / High | CSV-only overwrite lacks calculation history | Immutable snapshots/results and versioned runs; hash/DB tests | Reference implementation validated |
| P05 | Data contract / Moderate | Qualitative family includes fractions/binary/audit ordinal, not all 1..5 | Correct per-field contract from generator; full source ingestion passes | CLOSED by corrected schema; no model method change |
| P06 | EAD rounding / Low | Historical face and EAD rounded independently | Explicit cent conversion and observed per-facility reconciliation bound | Documented residual <=.01; no forcing total equality |
| P07 | Operations / High | PostgreSQL and Docker not runnable here | DDL/migrations/grants/CI provided; local tests use SQLite | OPEN; backend execution/restore required |
| P08 | UI / Moderate | Browser archive truncated by retrieval | Static/HTTP/API checks and JS syntax pass | OPEN; real-browser QA required |
| P09 | Security qualification / High | No institutional identity/TLS/perimeter/pentest | Loopback reference deployment, no production claim | OPEN |
| P10 | Simulation/product / Moderate | No full longitudinal financial/default/workout simulator or external macro feed | Preserve existing conduct/recovery simulators; dated snapshots/movements implemented | OPEN; new assumptions need evidence/governed version |

Classification: P01 DATA/VALIDATION; P02 MODEL RISK; P03 SECURITY; P04 DATA ARCHITECTURE/GOVERNANCE; P05 BUG FIX; P06 MODEL IMPLEMENTATION; P07 INFRASTRUCTURE; P08 UI/UX; P09 SECURITY; P10 DATA/RESEARCH. Owner: reference platform maintainer until an institution assigns accountability. No finding was erased to obtain a pass.
