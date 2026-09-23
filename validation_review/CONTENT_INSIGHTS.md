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
| Tests and interface are runnable | Python 3.12 clean frozen snapshot | 27 frozen pytest + 22 review cases; 30 release; 25 AppTest source comparisons | Remote CI and live browser manual inspection not separately established. |

## Classification and evidence hierarchy

Facts derived from committed source or Git history are labeled **source-inspected**. Rerun outputs are **reproduced**; independent formulas provide **recalculated** support. The explanation of outcome-conditioned underprediction is an **inference**, not a causal experiment establishing that no model weakness exists. Proposed distributional LGD changes are **METHODOLOGICAL CHANGE** and were not implemented.

## Review package contents

- `RESEARCH_REPORT.md` / `.pdf`: executive summary, lineage, assumptions, outcomes, validation, findings and external references.
- `figures/`: seven history, PD, stage/ECL and LGD analytical plots.
- `evidence/`: commit, branch, PR, phase, capability, test, hash, historical rerun, independent segment, calibration, ECL trace and reconciliation data.
- `tools/`: evidence generators and independent read-only calculator.
- `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, `DATA_DICTIONARY.md`, `MODEL_INVENTORY.md`, `VERSION_EVOLUTION_MATRIX.md`, `TRACEABILITY.md`, `FINDINGS_REGISTER.csv` and `ARTIFACT_INVENTORY.md`: governance and navigation.

No model artifact or raw synthetic portfolio is checked into this review package. Generate the latter from the frozen source.

## Technical story candidates for a three-to-four-post series

These are research notes for future writing, **not published LinkedIn posts**. Every number is from reproducible synthetic runs. The strongest story is an adverse validation finding, not a performance boast.

### Candidate 1 — From PD cutoffs to a decisioning system

- **Topic/problem:** A single PD score in the first commit drove both stage labels and scaled ECL; those roles require separate reporting concepts.
- **Initially expected:** A relatively simple PD→ECL demonstration could serve as a portfolio prototype.
- **Validation revealed:** Initial stage assignment was tied to PD thresholds; historical default share was 10.54%, versus 3.39% in the final generator. Numbers between those vintages do not compare as evidence of PD improvement.
- **Technical explanation:** V2 separated prospective 12-month default for PD testing from reporting-date impairment/deterioration and from monitoring. V4 later attached facility maturity, LGD and EAD to ECL.
- **Solution and result:** Frozen V5 sums 5,172 facilities to 3,000 scored borrowers; total synthetic EAD 2,091,914,076.05 and ECL 45,265,972.05 independently reconcile.
- **Chart/table:** `figures/history.png`, `VERSION_EVOLUTION_MATRIX.md`, `independent_facility_traces.csv`.
- **Lesson:** A risk score, a watchlist state and an accounting stage answer different questions; show the chain and its assumptions explicitly.

### Candidate 2 — AUC, calibration and challenger discipline

- **Topic/problem:** Choosing the highest AUC on a holdout can make an educational score look more settled than it is.
- **Initially expected:** More elaborate features and scorecard transformations might automatically win.
- **Validation revealed:** The final governed logistic PD scored AUC .759455, Gini .518911 and Brier .0300025 on 3,000 synthetic holdouts, with mean PD 3.4388% and observed default 3.4000%. Separate main-based WOE experiment AUC .741035 versus governed .759914 on that experiment's population; the PCA challenger reported .754635. These are diagnostic branch findings, not V5 contenders on identical final data.
- **Technical explanation:** AUC ranks, Brier/calibration assess probability quality, and paired intervals quantify single-holdout uncertainty. The historical 2,000-resample bootstrap gave main-based AUC interval [.7161, .8038], not a final-V5 multi-vintage guarantee.
- **Solution and result:** Keep the governed logistic champion fixed and expose calibration, Brier, log loss and challenger provenance without optimizing on the holdout.
- **Chart/table:** `historical_experiments.csv`, PD table in the research report.
- **Lesson:** Never label a metric change a methodological improvement when the generator, target or holdout changed.

### Candidate 3 — The LGD tail that a near-zero aggregate bias concealed

- **Topic/problem:** Synthetic facility workout LGD appears nearly unbiased in aggregate, yet severe realized workouts are underpredicted.
- **Initially expected:** Adding 8,000 realistic resolved facility workouts and collateral/guarantee/lien/recovery data might resolve the high-loss problem.
- **Validation revealed:** Overall holdout bias −0.31 pp and MAE 11.40 pp; realized >75% losses n=327 have bias −15.59 pp. In the top 10% **predicted** risk cohort n=200, bias is −2.53 pp. Cure cases have +27.45 pp error; non-cures −5.63 pp. V4-early and final use different recovery targets: early realized >75% bias −15.46 pp (n=308), final −15.59 pp (n=327), so there is no justified claim that the tail was fixed.
- **Technical explanation:** Observed cure and recoveries are not known pre-workout; selecting on realized loss also selects large negative residuals. Neither observation excuses failing to disclose severe-loss risk.
- **Solution and result:** Checked raw cashflow discounting, splits, joins, clipping and segments; retained the approved champion, published tail diagnostics and an open high-severity finding.
- **Chart/table:** `figures/lgd_tail_bias.png`, `figures/lgd_calibration.png`, `historical_lgd_tails.csv`, `FINDINGS_REGISTER.csv`.
- **Lesson:** Always report the bias sign and specify whether a tail cohort is defined by forecasts or realized outcomes.

### Candidate 4 — Software failures are part of model risk

- **Topic/problem:** A passing CI badge or an advanced dashboard can conceal circular validation and weak historical test coverage.
- **Initially expected:** V5's 30 release checks and interface tests appeared to settle reproducibility.
- **Validation revealed:** CI invariants had been removed in earlier commits and later restored. The frozen release script imports production functions for some metric comparisons; that alone is not independent validation. A clean rebuild requires the declared Streamlit dependency. Watchlist rating 7 covers 287 borrowers versus 221 Stage 2 cases, a distinction the UI must preserve.
- **Technical explanation:** Recalculate outputs independently; run source archives; test stage thresholds and transitions with expected outcomes; reconcile facility and borrower amounts; separate demo roles from real authorization.
- **Solution and result:** Independent review reproduced PD, workout target and ECL identities; 49 tests (27 frozen + 22 new cases), 30 frozen release checks, 25 dashboard source comparisons and five demo role views pass locally. This does not prove production security or real-bank performance.
- **Chart/table:** `TRACEABILITY.md`, `FINDINGS_REGISTER.csv`, `independent_facility_traces.csv`.
- **Lesson:** Reproducible arithmetic and credible limits are valuable even when the answer is imperfect.
