# Executive validation summary — synthetic V5 system

**Frozen V5 benchmark:** `0dfe4c883a8314704394c49fa096dfb45525096c`. Review is on separate branch; production methodology was not changed. The repository evolved from a PD/ECL prototype through V2 EWS/staging, V3 workbench and V4 facility workout LGD/ECL to V5 release diagnostics; see [full lifecycle paper](RESEARCH_REPORT.md).

## Decision

**Fit for an educational, reproducible synthetic demonstration and technical portfolio; not validated for live bank provisioning.** The synthetic engine runs and its stored risk numbers reconcile to source rules. Realized severe LGD remains materially underpredicted, and the evidence does not justify modifying an approved model to improve a score.

| Gate | Independently verified result | Decision |
|---|---|---|
| Data | 12,000 synthetic borrowers, 8,000 resolved workouts; 15/15 direct integrity checks | Structural `trade_type` nulls are confined to 7,659 zero-trade accounts. |
| PD | 3,000 holdout, 102 future defaults; AUC .759455, Gini .518911, KS .408497, Brier .0300025, log loss .128562 | Internally consistent synthetic discrimination/calibration. |
| LGD | 2,000 workout holdout: MAE 11.40 pp, RMSE 16.58 pp, mean error −0.31 pp | Overall mean masks adverse segments. |
| Severe LGD | 327 realized >75%: −15.59 pp bias; top 200 by **predicted** LGD: −2.53 pp | High-severity issue open; do not equate outcome-selected and prospective cohorts. |
| Stage/watchlist | 0 mismatches in 3,000 borrowers; 22 source-policy boundary cases pass | Internal nine-month EWS policy preserved; rating 7 and Stage 2 differ. |
| EAD/ECL | 5,172 facilities; EAD 2,091,914,076.05; ECL 45,265,972.05 synthetic units | Facility and borrower reconciliations pass to stored rounding. |
| Software/UI | 49/49 tests, 30/30 release checks, 25/25 dashboard source checks and original five-role smoke test pass locally | Real authentication, out-of-time data and remote CI are outside this review. |

The full findings register contains 13 tracked items. Four important open risks are severe-LGD residuals, stochastic cure/recovery, demo-only identity control and absent real multi-vintage validation. An early V4-to-final V4 aggregate MAE improvement coexists with persistent high-loss bias on **changed workout targets**; it is not proof that the tail was fixed. The V4-final and V5-frozen governed numerical outputs reproduce identically; V5 contributed diagnostics, testing and reproducibility.

**Use:** show the pipeline, explain model-risk decisions and known limitations, and link the paper and evidence. **Do not describe it as a certified IFRS 9 engine or real-bank calibrated model.** No external publication or GitHub merge is implied by this local review package.
