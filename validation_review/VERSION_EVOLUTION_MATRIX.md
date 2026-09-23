# Version evolution matrix

The columns are historical *milestones*, not a claim of five linear releases. See `evidence/phases.csv` for 21 material intermediate/alternative phases, `capability_matrix.csv` for source-derived phase rows and `branches.csv` for ancestry. V1 is the initial upload; V2, V3, V4 and V5 identify representative commits below. “Experimental” never means promoted to final production.

| Capability | Initial/V1 `4d91d1e` | V2 `29ede62` | V3/main `b93a459` | V4 `4f87d21` | V5 `0dfe4c8` |
|---|---|---|---|---|---|
| Borrower data | Supplied 12k, 22 fields, 10.54% defaults | Reproducibly generated 12k, 38 fields, 3.35% defaults | 12k, 51 fields, 3.48% defaults | 12k, 65 fields, 3.39% defaults; independently sampled qualitative fields | Same seeded source as V4 |
| Behavioral history | Current observations | 36 monthly observations per borrower | Retained | Retained | Retained |
| PD | Balanced candidates, select largest holdout AUC | Governed logistic, explicit predictors | Governed logistic; rating support | Governed logistic plus qualitative candidates | Unchanged governed logistic; stronger release evidence |
| WOE/IV | Absent | Absent | Main absent; WOE challenger on separate PR 20 | Not promoted | Not promoted; no governed IV scorecard |
| PIT/LR/score | PD score tied to prototype | PIT-oriented annual PD and scenario odds; no empirical LR/TTC calibration | Score/rating presentation | Same core framework | Same core framework |
| SICR/staging | PD threshold labels | Reporting-state Stage 3 and Stage 2 deterioration triggers | Distinction retained and displayed | Retained | Checked independently; Stage 1/2/3 separate from future default |
| Watchlist | Absent | Internal nine-consecutive-month EWS policy | Operational rating 7 and monitoring workspace | Retained | Watchlist/rating distinguished from SICR |
| EWS | Absent | Trajectory, utilization, limit breach | Workbench monitoring | Retained | Mismatch-free independent flag recalculation |
| LGD | Simple borrower collateral proxy | Borrower collateral proxy | Collateral type recovery refinements | Resolved facility workout model, 8k history | Same governed model; tail/legacy diagnostics |
| EAD | Borrower/product approximation | Loan outstanding/OVD/trade CCF | Direct and indirect limit architecture | Facility expansion and borrower sum | Facility reconciliation checks |
| ECL | Borrower PD×LGD×EAD and multipliers | Stage-dependent macro 12m/lifetime borrower approximation | Rating and dashboard views | Facility maturity-specific stage ECL | Same facility ECL, per-stage trace/release checks |
| Portfolio analytics | Basic view | Generated monitoring and scenario outputs | Industry/limits/rating concentration workbench | Facility and borrower reporting | Model-validation workspace and improved presentation |
| Model validation | AUC-focused | Calibration, KS/Brier/log loss and experiments | Dashboards, baseline diagnostics | LGD MAE/RMSE/bias, segments and challengers | Common-cohort tails, realized bands, legacy comparison, stability and independent review |
| Dashboard | Initial dashboard script | Source outputs | Root Streamlit workbench | Facility drill-down | Five role AppTest smoke and filters |
| Automated tests | None in first commit | Limited tests/invariants restored after reduction | Some governance tests | Facility model/ECL tests | 27 frozen tests + 22 methodology-neutral review policy cases |
| CI/workflows | None in first commit | Generator and analytical pipeline | Interface workflow | Facility LGD/ECL jobs | Two workflows; V5 push trigger and local release rerun |
| Documentation | Prototype README | Generator and policy explanation | User/workbench notes | LGD decision and recovery diagnostics | README, change log, limitations and independent lifecycle paper |

**Comparability:** V4-final and V5-frozen use identical seeded borrower/workout data and governed model specification. V4-early and V4-final workout target data hashes differ, so their LGD errors cannot be interpreted as a controlled head-to-head improvement. V1 through V3 PD target distributions and feature sets also change. The source row “12k borrowers” does not imply that all 12k were held out: the final validation samples 3k borrowers and 2k workouts.
