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

## Continued validation findings

| ID | Finding | Correction and evidence | Status |
|---|---|---|---|
| P11 | Independent reconciliation accepted invalid stages/non-finite inputs and an empty blocked run could be validated | Strict independent input checks; successful-run prerequisite; six adverse regression cases | CLOSED; 93-test suite passes |
| P12 | On workspace resume, historical PNG was truncated and development SQLite file was malformed | Preserved damaged evidence; recovered exact Git image; new migrated database and canonical reload | Contained; no claim of production storage reliability |
| P13 | Whole-run integrity previously relied on row hashes and DB sort order | Full output hash verification; Python canonical ordering independent of DB collation | CLOSED; full shadow replay verifies |

## LGD remediation follow-up

| ID | Finding | Correction and evidence | Status |
|---|---|---|---|
| P14 | LGD clipping could disguise infinity and prediction cardinality was unchecked | Validate finite one-dimensional output length before approved clipping; unit and failed-run/no-decisions integration tests | CLOSED for platform adapter; frozen historical implementation preserved |
| P15 | Severe realized-cohort bias was not separated from outcome selection under conditional expectation | Independent R2 conditional simulation: expected-loss tail bias -12.5017 pp versus V5 -12.7421 pp; see LGD_REMEDIATION_REPORT.md | DIAGNOSED for R2 only; P02 calibration/support/feature and institutional validation blockers remain OPEN |

## S1 findings — 25 September 2026

| ID | Finding | Evidence / decision | Status |
|---|---|---|---|
| P16 | Original workout/live guarantee discontinuity | S1 shared source generation: all cohorts approximately 80% zero guarantee; borrower/FK/cashflow/source checks pass | REMEDIATED for S1 source design only; original incumbent remains unsupported |
| P17 | Better aggregate fit does not establish tail improvement | New final 1,017 facilities: enhanced RMSE 17.08 pp versus V5 18.13 pp, severe bias -15.31 versus -10.42 pp (168 facilities) | OPEN; no promotion |
| P18 | Natural defaults yield fewer development workouts than standalone R2 | 1,933 development facilities; correlated within borrower, changing observed sector states | Sampling/transfer limitation retained; no favorable reseeding |

## Final LGD disposition findings

| ID | Finding | Evidence / decision | Status |
|---|---|---|---|
| P19 | Realized severe bias conflated with conditional underprediction | S1 governed total -12.1078 = +2.4830 -14.5908 pp; supersedes tail-only interpretation of P02/P17, preserves statistics | INTERPRETATION CORRECTED; not a bank-use waiver |
| P20 | Governed S1 current conditional mean shortfall under regime transfer | -12.65 pp overall, -10.92 pp in conditional >75% group; 82.38% current downturn context omitted from incumbent | OPEN model/support deficiency; reference only |
| P21 | Narrow context/rate candidate does not clear promotion | Known rate added, industry proxy removed; current high-conditional bias -4.91 pp versus existing enhanced -4.55 pp; no untouched promotion test | RESEARCH COMPLETE / NOT PROMOTED |
