# Marginal Interest LGD experiment — MI-1

## 1. Executive conclusion
**No robust incremental benefit from Marginal Interest was demonstrated.** This is disposition5 for historical feasibility and an inconclusive/negative incremental-value result for the new hypothetical experiment. M4 improved final RMSE versus M0 by0.264pp, but adding MI beyond age changed RMSE by+0.0033pp and adding it beyond compact workout controls changed RMSE by−0.0104pp; both paired95% intervals include zero. The broader observed workout state appears useful within this chosen simulator, while a distinct contribution from MI is not established. No positive empirical/bank claim follows. **CHALLENGER_NOT_PROMOTED; institutional production BLOCKED.**

## 2. Research question
Does observation-time suspended contractual interest contain robust incremental information about remaining impaired-facility recovery severity? The prespecified comparisons and stopping rule in PROTOCOL.md were committed before generation/fitting. No tuning followed validation or final results.

## 3–4. Definition and accounting/EAD treatment
MI is the cumulative memorandum interest balance from opening monthly principal×rate/12 through observation. No compounding, interest payments or capitalization; principal payments reduce later accrual. It is neither IFRS interest revenue nor an additional loss. EAD is remaining principal. MI is only a predictor. The target is remaining discounted principal-recovery loss at observation; it is deliberately a new research target and cannot silently replace historical default-date LGD. See FEATURE_CONTRACTS.md and EXTERNAL_EVIDENCE.md.

## 5–7. Observation-time availability, lineage and leakage
Source static facilities -> fixed borrower split -> default date and monthly principal-payment/accrual ledger -> observation snapshot -> independent future recovery draws -> resolved outcome. Future outcomes never construct predictors. Allowlist excludes final LGD,cure,writeoff/future cashflows,latent willingness/security quality/guarantor strength and oracle means. Perturbation tests and independent ledger arithmetic pass. Final outcomes were generated and hash-frozen but not evaluated until model lock. Reading bytes for hash/integrity verification is not outcome inspection. The final target is now opened engineering evidence and must never be reused as a fresh holdout. Frozen R1 transfer diagnostic saw source development covariates historically; it is not an independent matched-training benchmark.

## 8. Dataset/DGP changes
Historical data unchanged. New hypothetical MI-1 release,12,000 borrowers/20,747 facilities; split counts below. Pre-observation willingness and quarter shocks influence payments and future capacity; coefficients are hypotheses,not empirical estimates. Irreducible future recovery/cure noise retained. No outcome balancing. The extra full-payoff cure path is hypothetical and reported cure labels do not enumerate the original simulator's hidden cure channel.

An initial metadata/API defect stopped generation before outcomes. Later two truncated archives were detected before fitting. Deterministic recovery preserved exact prefix bytes; the final-outcome file matches its original frozen hash. The ledger was truncated before hashing,so its repaired hash was recorded before fitting with the old manifest preserved. No alternative seeds/distributions were selected. See GENERATION_LOG.md and recovery_verification.json; original damaged evidence retained.

## 9. Development/validation/final design
Development7,200 borrowers/12,416 facilities; validation2,400/4,170; final2,400/4,161. Borrower and facility IDs disjoint. Hypothetical observation vintages are temporally ordered; all facilities from each borrower stay together. Source covariates are reused from known historical development; macro values are not actual historical observations for these new dates. No claim of institution-level temporal representativeness. Seeds and outcomes frozen before model fitting.

## 10. Candidates and controls
Same retained S2-R1 histogram boosting settings for every newly fitted candidate:350 iterations,.05 rate,31 leaves,minleaf80,L2=5,seed94001,original monotonic signs,no search. M0 refits retained feature specification on new target; M1 adds age; M2 adds MI amount/ratio; M3 adds age+MI; M4 adds compact observed recovery/restructuring/default-principal controls. M4_without_mi is a prespecified diagnostic ablation,not an extra selected model. Validation chose M4 among M1–M4; the ablation was slightly better on validation and is transparently retained. Balance,rate,products,protection and financial-risk proxies are controlled. Actual PD/rating are absent and were not invented; a fully PD/rating-controlled conclusion remains untested. MI/EAD is identical to MI/principal and excluded as redundant.

## 11. Final baseline-scenario performance
Errors,bias and meanLGD in percentage points/percent; R² unitless. N=4,161 for all. Frozen_R1_transfer is an old-target transfer diagnostic,not comparable historical published RMSE.

| model | n | mae | rmse | bias | r2 | predicted_mean | realized_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | 4161 | 17.4461 | 22.1715 | -0.5541 | 0.3276 | 41.3808 | 41.9349 |
| M1 | 4161 | 17.4776 | 22.2033 | -0.613 | 0.3257 | 41.3219 | 41.9349 |
| M2 | 4161 | 17.5642 | 22.282 | -0.6376 | 0.3209 | 41.2973 | 41.9349 |
| M3 | 4161 | 17.4946 | 22.2065 | -0.6559 | 0.3255 | 41.279 | 41.9349 |
| M4 | 4161 | 17.2759 | 21.9075 | -0.7823 | 0.3435 | 41.1526 | 41.9349 |
| M4_without_mi | 4161 | 17.2587 | 21.918 | -0.7034 | 0.3429 | 41.2315 | 41.9349 |
| frozen_R1_transfer | 4161 | 16.0286 | 22.57 | 5.4734 | 0.3032 | 47.4083 | 41.9349 |

## 12. Predicted-band calibration
Fixed bands declared before results; all uncertainty here is400-draw paired borrower bootstrap. Outcome-selected cohorts below are separate diagnostics. Small samples are not evidence of precise calibration.

| model | segment | n | predicted_mean | realized_mean | bias | bias_low | bias_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | predicted:0-0.1 | 139 | 5.903 | 8.437 | -2.533 | -3.591 | -1.439 |
| M0 | predicted:0.1-0.25 | 573 | 18.541 | 19.848 | -1.307 | -2.19 | -0.363 |
| M0 | predicted:0.25-0.5 | 2188 | 38.638 | 39.916 | -1.278 | -2.153 | -0.468 |
| M0 | predicted:0.5-0.75 | 1158 | 58.677 | 57.603 | 1.074 | -0.52 | 2.635 |
| M0 | predicted:0.75-1 | 103 | 80.119 | 76.75 | 3.369 | -2.484 | 8.914 |
| M4 | predicted:0-0.1 | 147 | 5.908 | 9.147 | -3.239 | -4.644 | -2.096 |
| M4 | predicted:0.1-0.25 | 573 | 18.423 | 19.82 | -1.396 | -2.317 | -0.537 |
| M4 | predicted:0.25-0.5 | 2243 | 38.625 | 39.96 | -1.335 | -2.252 | -0.597 |
| M4 | predicted:0.5-0.75 | 1094 | 59.218 | 58.344 | 0.873 | -0.619 | 2.415 |
| M4 | predicted:0.75-1 | 104 | 80.673 | 80.1 | 0.574 | -4.126 | 5.312 |

## 13–14. Severe loss,low loss and cure
Bias intervals in pp; >90% cohort has only92 observations and is insufficient for strong claims. Explicit full-payoff cure is a future outcome label,not an input; large retrospective cure bias does not establish forecast miscalibration on an observable cohort.

| model | segment | n | bias | bias_low | bias_high |
| --- | --- | --- | --- | --- | --- |
| M0 | realized_gt60 | 1323 | -18.931 | -19.627 | -18.357 |
| M0 | realized_gt75 | 536 | -21.748 | -22.791 | -20.819 |
| M0 | realized_ge90 | 92 | -26.065 | -28.546 | -23.675 |
| M0 | low_le10 | 731 | 29.978 | 28.311 | 31.636 |
| M0 | cure | 580 | 36.366 | 34.953 | 37.998 |
| M0 | guarantee:full | 172 | -0.513 | -2.326 | 1.574 |
| M4 | realized_gt60 | 1323 | -18.855 | -19.476 | -18.267 |
| M4 | realized_gt75 | 536 | -21.242 | -22.318 | -20.089 |
| M4 | realized_ge90 | 92 | -24.546 | -27.21 | -21.94 |
| M4 | low_le10 | 731 | 29.107 | 27.53 | 30.868 |
| M4 | cure | 580 | 35.15 | 33.824 | 36.686 |
| M4 | guarantee:full | 172 | 0.225 | -1.537 | 2.282 |

## 15–16. Support and stability
Existing joint macro×collateral×guarantee support rules unchanged. All scenarios and all new feature ranges checked; unsupported predictions are diagnostic-only and cannot be deployed. Additional-feature joint density is not certified. feature_stability.csv reports missingness,KS and ranges; temporal_stability.csv reports yearly error/bias. Current platform has no captured MI ledger: live missingness/distribution cannot be estimated. Source/current population comparability is therefore unproven.

| split | scenario | n | supported | new_feature_outside | rejected |
| --- | --- | --- | --- | --- | --- |
| final | baseline | 4161 | 4156 | 1 | 5 |
| final | downside | 4161 | 3685 | 1 | 476 |
| final | upside | 4161 | 4021 | 1 | 140 |
| validation | baseline | 4170 | 4165 | 2 | 5 |
| validation | downside | 4170 | 3629 | 2 | 541 |
| validation | upside | 4170 | 4060 | 2 | 110 |

## 17–19. Incremental value,age controls and uncertainty
Paired changes in RMSE,pp; negative means lower error.400 borrower and400 sector/observation-quarter bootstrap replicates; both reported,no selection of the narrower interval. No tuning or post-result feature search. M4-vs-M0 shows a small improvement within this DGP; the two MI-specific tests are inconclusive. MI is algebraically determined by balance history,rate and age,so it cannot add new information relative to the complete ledger; finite-model approximation benefits would not change that fact. Partial observability and an assumed common cause are part of this simulator,not empirical proof. Confidence intervals do not cover DGP misspecification,coefficient uncertainty or institutional transfer.

| model | control | grouping | delta_rmse | delta_rmse_low | delta_rmse_high |
| --- | --- | --- | --- | --- | --- |
| M3 | M1 | customer_id | 0.0033 | -0.1017 | 0.1125 |
| M3 | M1 | cluster | 0.0033 | -0.1016 | 0.1048 |
| M4 | M0 | customer_id | -0.264 | -0.4555 | -0.0703 |
| M4 | M0 | cluster | -0.264 | -0.4604 | -0.0652 |
| M4 | M4_without_mi | customer_id | -0.0104 | -0.1063 | 0.086 |
| M4 | M4_without_mi | cluster | -0.0104 | -0.0882 | 0.0658 |

## 20. Scenarios
Upside/baseline/downside reuse the existing economic-coordinate mapping with preregistered scenario values. Every new candidate and the fixed ablation had zero reversals across validation and final. No prediction sorting or overlays. Source support nevertheless fails most materially under downside. MI's causal effect is not constrained or established by these macro monotonicity checks.

## 21. Feature availability
New ledger fields are RESEARCH ONLY/REQUIRES NEW DATA CAPTURE. No live operational integration,accounting reconciliation or as-of posting-delay validation exists. Marginal ratios use positive remaining principal; invalid/missing values fail closed. No Stage1/2 imputation. Source snapshots may be stale; no true PD/rating control. Production gate remains blocked independently of numerical performance.

## 22. Controlled ECL bridge
Validation-selected M4 locked before final ECL calculation. Identical4,161 facilities,borrowers,Stage3,PD1,EAD and scenario weights. Only LGD changes. Scenario-weighted **M0 ECL=676,483,805.10**, **M4 ECL=672,423,199.25**, difference **-4,060,605.85 (-0.6003%)**, unspecified currency units. Stage1/2=N/A because this is impaired-only research. All impact is Stage3. Sector contributions in ecl_sector_bridge.csv. This is unbooked impact,not a model selection criterion; this reduction is not attributable solely to MI.

## 23. Promotion gates
Historical230 numerical checks independently recomputed with agreement; historical19 evidence hashes verified. Existing historical adverse gate decisions retained. New target conditional-mean gates cannot be passed using a latent-state oracle masquerading as observable conditional expectation. Original-S2 same-target acceptance and current live feature-availability gates are not available and remain blocked. Existing1pp overall/regime and2pp segment tolerances were NOT weakened; realized clustered calibration intervals were additionally assessed,with68 failed/insufficient final checks. This supplement is not claimed to replace the original conditional-equivalence framework. Joint support FAIL; zero scenario reversals PASS; engineering/test evidence separately recorded. All requirements must pass for promotion; they do not.

## 24–25. Disposition and remaining limitations
CHALLENGER_NOT_PROMOTED; institutional production BLOCKED. Historical question is not retrospectively answerable. Hypothetical experiment does not demonstrate MI's robust incremental value. Data-capture/PD-rating controls,complete cure labels,macro support,prediction calibration,independent institutional validation and deployment qualification remain unresolved. No modelling search should continue on this opened final set. Next legitimate evidence would be a governed real observation-time ledger or a separately justified hypothesis,not repeated synthetic tuning.

## 26. Tests,reconciliation and release track
Full suite: **200 passed, 1 upstream deprecation warning**, verified at closeout on 2026-10-07; full log in results/full_tests.txt. Independent cashflow recomputation,equal ECL inputs and portfolio aggregation are saved in reconciliation.json/independent_ecl.json; historical files unchanged. Release branch remains7773beb86df8480d964daaaf62199cedc15d356a. GitHub publication/authentication is blocked; final reviewed-commit CI not run; rendered browser verification outstanding. These do not alter research findings. No production model was changed or promoted.

Reproduce/check: install requirements-platform-lock.txt; run `python -m pytest -q`; inspect LOCK.json and FINAL_OPENED.json; run `python -m marginal_interest.audit` and `python -m marginal_interest.make_report` to recalculate reports from known outputs. Generator/fit/final evaluator refuse overwrite/reopening. Do not delete lock evidence to rerun a favourable experiment. Model prediction artifacts and fixed datasets are committed for reproducibility.
