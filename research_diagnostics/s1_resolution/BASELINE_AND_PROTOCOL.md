# LGD resolution: repository reconstruction and targeted protocol

Baseline HEAD 3539e36, branch platform/production-foundation, 25 September 2026.
No dataset regeneration, no new model or calibration before the decomposition.

| State | Evidence | Disposition |
|---|---|---|
| DONE / STILL VALID | S1 data freeze; 65k borrowers, 113012 facilities, 2.34m conduct rows, 107 tests | Preserve and verify hashes; no regeneration |
| DONE / STILL VALID | V5 0dfe4c8; R2 ae9942a; original, two-stage, component, quantile, oracle, ablation/stress evidence | No repeated broad research |
| DONE / STILL VALID | S1 1933 development workouts, 1055 selection, 1017 final; 168 final >75 cases | Final already viewed; diagnostic only, not a fresh selection test |
| SUPERSEDED INTERPRETATION | Treating realized >75 bias alone as expected-loss defect | Must separate model versus expectation from realization |
| UNRESOLVED | R2 conditional mean evidence has not been reproduced for S1 recovery equations | Immediate experiment |
| UNRESOLVED | S1 enhanced aggregate fit versus conditional calibration | Evaluate all three fixed candidates, no refit |
| UNRESOLVED | S1 comparison benchmark is H-trained 6000-case V5; actual reference platform artifact trained on all 8000 | Include actual governed artifact as a fourth row; do not conflate |
| STILL OPEN | Institutional data/feature qualification, PostgreSQL/container/hosted CI/browser/TLS/SSO gates | Separate from LGD diagnosis |

The mandate's prose decomposition contains a minus-sign typo; its displayed
identity is correct: total = model-minus-conditional + conditional-minus-actual.
All calculations use the additive identity, bias = prediction minus actual.

## Predeclared diagnostic

Use existing S1 final, selection, development resolved facilities and current
facilities. Integrate the **S1**, not R2, recovery process: known borrower interest
rate, shared borrower future shocks and known quality/context. Independently
transcribe marginal equations, verify exact outcome replay against the generator
on a controlled fixture. Simulate 4096 draws per facility, seed 2026092501;
independent Monte Carlo streams across facilities estimate marginal means/variance.
This does not estimate joint portfolio loss tails; original outcomes are clustered
by borrower. Outcomes are not inputs. No changed generator coefficient.

Keep final >60/>75/>90 realized cohorts and low loss. Ex-ante groups: predicted and
conditional-mean bands of width .20; security, lien, product, industry; guarantee
zero/partial/full; collateral coverage [0,.5,1,inf); EAD [0,100k,500k,inf); conditional
mean >.60 and >.75. Recovery costs and time are future and prohibited as groups.
Report all counts, unique borrowers, MAE/RMSE, model/realization decomposition,
conditional model RMSE, MC standard errors, and approximate 95% cluster-robust
mean-bias intervals. Mark fewer than 30 borrower clusters as small sample; this is
an uncertainty warning, not a promotion threshold. No significance-only promotion.
Compare squared model-to-mean error with conditional outcome variance; report both
realized RMSE and model-implied expected RMSE. Conditional expectation is an estimate
under synthetic assumptions, not observed truth at a bank.

Use fixed candidate artifacts, protected by prior lock hash, and separately hash
actual governed artifact. All final evaluation is retrospective. If a new correction
is justified, existing final cannot become an untouched promotion holdout again.
Current-cohort ECL impact uses unchanged PD/stage/EAD and counterfactual LGD only;
no replacement of governed outputs. Re-run current reference reconciliation.
