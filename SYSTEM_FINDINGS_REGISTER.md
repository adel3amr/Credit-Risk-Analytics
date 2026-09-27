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

## Downturn decision follow-up

| ID | Finding | Evidence / decision | Status |
|---|---|---|---|
| P22 | True-state calibration works but state is not operationally identified | Current oracle bias +0.55 pp; canonical no-industry state AUC .5001; industry shortcut AUC .2274 | OPEN feature identification/transfer limitation |
| P23 | Blanket downturn adjustment harms normal-state calibration | Current normal bias +16.85 pp and final aggregate +14.42 pp | REJECTED as expected LGD; sensitivity-only control implemented |
# S2 additive findings — 27 September 2026

| ID | Component | Severity | Classification | Evidence / root cause | Remediation / retest | Status / residual risk |
|---|---|---|---|---|---|---|
| S2-01 | Economic feature architecture | High | DATA ARCHITECTURE / METHODOLOGY | S1 direct latent shifts lacked observables | Versioned observable recovery channels; S2 conditional current bias -6.33 → -0.26 pp | Implemented for S2; S1 finding not retrospectively closed |
| S2-02 | Scenario shape | Moderate | MODEL IMPLEMENTATION | 78 facility reversals, max .9342 pp | No final-set tuning or forced sorting; promotion blocked | OPEN |
| S2-03 | Downside support/calibration | High | DATA / VALIDATION | -2.32 pp downside bias; activity/unemployment outside development ranges | Require support-qualified future validation, not another broad algorithm search | OPEN |
| S2-04 | Guarantee calibration | High | VALIDATION | Final full-guarantee +4.65 pp bias, n=135 | Require segment validation before promotion | OPEN |
| S2-05 | Evidence independence | Moderate | VALIDATION | Seven current economic clusters; synthetic fixtures only | Macro-cluster SE reported; no institutional inference | OPEN |

## S2-R1 finding events — 27 September 2026

These events supersede disposition for the new candidate only; original S2
findings and numerical evidence above are preserved. Owner remains the reference
platform maintainer pending institutional assignment.

| ID | Severity / classification | Retest and evidence | Current disposition / residual risk |
|---|---|---|---|
| S2-02 / R1 | Moderate / METHODOLOGY–MODEL IMPLEMENTATION | Constrained response; zero reversals on 8,695 current and 6,000 new promotion facilities, independent invariants | CLOSED for R1; original S2 still has 78 |
| S2-03 / R1 calibration | High / VALIDATION | Current downside −0.47 pp, equivalence bound 1.15 > 1 pp; upside bound 1.17 | OPEN; mean improvement is insufficient evidence of equivalence |
| S2-03 / R1 support | High / DATA–GOVERNANCE | Current scenarios all supported; new final 35/81/327 baseline/upside/downside rejections | OPEN release scope; explicit rejection control implemented |
| S2-04 / R1 | High / VALIDATION | Waterfall caps/continuity pass; fresh full guarantee +1.35 pp, bound 2.06; current partial downside bound 2.90 | OPEN; no target mechanics defect demonstrated, no cosmetic adjustment |
| S2-05 / R1 | Moderate / VALIDATION | Fresh borrower-disjoint holdout; macro and borrower uncertainty; seven current macro clusters remain | OPEN institutional/sampling limitation |
| R1-06 | High / MODEL IMPLEMENTATION–VALIDATION | Current baseline predicted 80–100% band +3.62 pp conditional bias; fresh +2.63 pp | OPEN prediction-band calibration defect; blocks general-performance gate |
| R1-07 | Moderate / DATA | Short generated audit histories omitted cycle phases in first pre-fit attempt | CLOSED before fitting; rejected generator/data preserved, complete phase coverage tested |
| R1-08 | Low / API–GOVERNANCE | Copilot default could emphasize old S1 evidence; first-row selection could choose upside | CLOSED; latest integrity-checked decision and explicit baseline selection tested |

Final decision: `s2_remediation/results/decision.json`; 29 failed individual
acceptance checks span four failed promotion gates. Full test suite: 151 passed.
