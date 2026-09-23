# Content insights: source-to-claim register

This register maps the main report's claims to inspectable evidence. The 15 historical reruns are representative checkpoints, not an exhaustive execution of 299 commits. All V5 figures refer to frozen commit `0dfe4c8` and a clean source rebuild.

| Claim | Primary source | Independent evidence | Important qualification |
|---|---|---|---|
| Main predates V4/V5, and PR 22 was unmerged | Git ancestry and GitHub PR metadata | `evidence/branches.csv`, `pull_requests.json`, `phases.csv` | Branch names alone do not establish ancestry. |
| V4-final and V5-frozen have the same governed metrics and ECL | Clean archives and generated outputs | `evidence/historical_reproduction.csv` | Same seed and generator; not independent vintages. |
| Logistic PD AUC 0.759455 and observed default 3.4% | `outputs/borrower_audit_trace.csv` | `evidence/independent_reconciliation.json` | 102 synthetic holdout defaults. |
| LGD holdout MAE 11.3965 pp, mean bias −0.3052 pp | Workout history and holdout predictions | `evidence/independent_lgd_segments.csv` | Resolved synthetic default facilities only. |
| LGD >75% actual cohort n=327 and bias −15.5928 pp | Same frozen holdout | `evidence/independent_lgd_segments.csv` | Retrospective outcome-selected group; cannot use realized label at prediction time. |
| Predicted top-decile bias −2.5344 pp | Same frozen holdout | `evidence/independent_lgd_segments.csv` | Predicted cohort can be operationally identified before workout. |
| Cure mixture is material | Raw cure flag on holdout | `evidence/independent_lgd_segments.csv` | Cure known ex post, not a valid pre-workout predictor. |
| Discounted net cash recovery reconstructs workout target | `data/raw/lgd_workout_history.csv` | `independent_reconciliation.json` max absolute error | Recorded cashflows and EAD rounded. |
| Zero stage and EWS mismatches | Source policy and borrower trace | `tools/independent_recalculation.py`; `independent_reconciliation.json` | Checks exact established policy, not regulatory adequacy. |
| EAD 2.0919bn and ECL 45.266m reconcile | Borrower/facility generated traces | `independent_reconciliation.json`, `independent_facility_traces.csv` | Monetary units are synthetic. |
| Tests and interface are runnable | Python 3.12 clean frozen snapshot | 27 pytest, 30 release and AppTest outputs documented in report | Remote CI and live browser manual inspection not separately established. |

## Classification and evidence hierarchy

Facts derived from committed source or Git history are labeled **source-inspected**. Rerun outputs are **reproduced**; independent formulas provide **recalculated** support. The explanation of outcome-conditioned underprediction is an **inference**, not a causal experiment establishing that no model weakness exists. Proposed distributional LGD changes are **METHODOLOGICAL CHANGE** and were not implemented.

## Review package contents

- `RESEARCH_REPORT.md` / `.pdf`: executive summary, lineage, assumptions, outcomes, validation, findings and external references.
- `figures/`: history, LGD calibration, tail bias and residuals.
- `evidence/`: commit, branch, PR, phase, capability, test, hash, historical rerun, independent segment, calibration, ECL trace and reconciliation data.
- `tools/`: evidence generators and independent read-only calculator.
- `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, `DATA_DICTIONARY.md` and `ARTIFACT_INVENTORY.md`: governance and navigation.

No model artifact or raw synthetic portfolio is checked into this review package. Generate the latter from the frozen source.
