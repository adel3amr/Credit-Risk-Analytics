# Auditable repository timeline

This is an analytical timeline of selected committed milestones. Full commit timestamps, parents and subjects appear in `evidence/commit_history.csv`. Ref lineage matters more than a guessed “V1 to V5” release label; no Git tags were present in the inspected refs.

| Order | Commit / PR group | Problem and contribution | Verification / remainder |
|---:|---|---|---|
| 1 | Initial `4d91d1e` | Demonstrate PD and borrower ECL from supplied 22-field portfolio | Pipeline reruns; PD-cutoff stage and scaled lifetime ECL are historical limitations. |
| 2 | Hybrid generator `fda0edb`, predictor separation `d9a37dd` | Produce lower synthetic default frequency and isolate current information from future outcome | Early qualitative derivation and CI guards still needed correction. |
| 3 | CI reduction `4833e84`, `03c1db0` | Smoke test simplification removed substantive guards | Regression recorded; later tests/restored checks matter. |
| 4 | V2 `29ede62`, PR 1 | 36-month EWS, nine-month internal policy, current-state staging and macro scenarios | Clean archive reproduces logistic AUC .76729 under V2 data. |
| 5 | V3 `a78bfe9`, workbench `4a6bac7`, PRs 2–3 | Role demonstration and borrower decision workspace | App exists; demo identities are not authentication. |
| 6 | EWS correction `969df72`, collateral `a3c46b4`, PRs 4–5 | Clarify consecutive deterioration; security-type recovery | Reproducible but data generator changed; metrics not directly comparable. |
| 7 | Limits, rating, intelligence through main `b93a459`, PRs 9–17 | Product limits, trade CCF and internal rating | Main is earlier than facility LGD branch. |
| 8 | Separate PCA/WOE/bootstrap/stress PRs 18–21 | Diagnostic and challenger research | Rerun separately; no component was promoted into frozen V5. |
| 9 | Broader remediation `cfce69a`, PR 22 | Alternative generator and ECL/feature repairs | Closed unmerged; not V5 ancestor. |
| 10 | Code-only remediation `a90db85`, PR 23 | Ordering/state guards with approved method | Actual base of V4. |
| 11 | Early facility V4 `c85cdab` | Separate 8k workout LGD and facility remaining-term ECL | Tail underprediction n=308 realized >75%; synthetic data later revised. |
| 12 | Final V4 `4f87d21`, PR 24 | Cash-recovery friction and detailed LGD diagnostics | Overall LGD error improved; realized tail remains open with new target set. |
| 13 | V5 `33c60ee` to `0dfe4c8`, PR 25 | Common-cohort tails, release checks, dashboard and complete build | Numerical champions unchanged; original 27 tests and 30 checks pass. |
| 14 | This review `review/independent-system-validation` | 15 snapshot profiles, independent recalculation, full paper, 22 policy cases | 49 tests; seven figures; findings transparent; review branch local only until publication explicitly authorized. |

The full 21-phase machine-readable timeline is `evidence/phases.csv`. “Rerun” means executing a representative checkout with current Python dependencies, not reconstituting the exact historical runtime or proving all past CI jobs succeeded.
