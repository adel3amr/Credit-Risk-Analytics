# Credit Risk Analytics & IFRS 9 Decisioning System — V5

## Executive summary
V5 finalizes the implementation and validation of the approved synthetic framework. Logistic Regression remains the PD model; Gradient Boosting remains the facility workout LGD model. Staging, ratings, the 9-month EWS treatment, EAD and ECL assumptions are unchanged. The fixed 3,000-borrower portfolio has **€2,091,914,076.05 EAD** and **€45,265,972.05 staged ECL**.

**High-loss LGD underprediction is not solved.** No coding defect explaining it was established. The investigation now distinguishes predicted-risk tails from realized-loss tails. Random cure/recovery outcomes and the frozen model's point predictions leave material loss uncertainty. No challenger promotion, tail uplift, new predictor or favorable resampling was introduced.

## PD validation
| Metric | Governed Logistic Regression |
| --- | ---: |
| ROC-AUC | 0.759455 |
| Gini | 0.518911 |
| KS | 0.408497 |
| Brier | 0.030003 |
| Log loss | 0.128562 |
| Observed default rate | 3.4000% |
| Mean predicted PD | 3.4388% |
| Observed minus predicted | -0.0388 pp |

LR means Logistic Regression, an algorithm; PIT describes the time orientation of PD. The approved LR output is a reporting-date 12-month PIT-oriented estimate. The macro overlay produces a separate forward-looking PD. No true origination-reference PD or governed WOE/IV scorecard is implemented in this release.

## LGD validation
The 8,000 resolved synthetic facilities are split into 6,000 training and 2,000 validation records. Predictors exclude realized cash flows, cure/write-off outcome, costs and timing. The fixed champion is refitted on all 8,000 records for current-portfolio application after validation; that refit is not used to report holdout accuracy.

| Population | N | Actual mean | Predicted mean | MAE (pp) | RMSE (pp) | Bias (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All holdout | 2,000 | 45.43% | 45.13% | 11.40 | 16.58 | -0.31 |
| Realized LGD >60% | 652 | 76.28% | 64.02% | 12.70 | 14.70 | -12.27 |
| Realized LGD >75% | 327 | 85.07% | 69.48% | 15.62 | 17.17 | -15.59 |
| Realized LGD >=90% | 89 | 94.77% | 74.34% | 20.43 | 21.32 | -20.43 |
| Realized LGD >=97% | 25 | 99.38% | 77.52% | 21.87 | 22.63 | -21.87 |
| Realized LGD <=10% | 158 | 5.72% | 18.60% | 14.00 | 23.87 | +12.88 |

Bias is predicted minus realized LGD. The diagnostic cuts are reported together without selecting the best-looking threshold. Realized-loss membership is retrospective and unavailable at scoring time. Even a correct conditional-mean estimate can show bias in outcome-selected extremes. Narrow-band R² can be very negative because target variance is small; sample count and error magnitude are more informative.

The champion's highest **predicted** 10% has EAD-weighted bias -4.41 pp; highest predicted 5% has -6.48 pp. These earlier figures refer to different populations from the table above. On identical champion-selected facilities, Huber changes those biases to +1.77 and -0.70 pp, but its whole-holdout EAD-weighted bias is +2.42 pp and RMSE is slightly worse. The [decision record](../docs/V5_LGD_VALIDATION_DECISION.md) retains the champion.

## Investigation findings
- **Coverage:** training contains 1,916 facilities above 60%, 980 above 75%, 257 at/above 90% and 102 at/above 97%. Tail absence does not explain the weakness. The holdout's 25 near-total-loss cases still create sampling uncertainty.
- **Recoveries:** discounted net cash flows reconstruct LGD with maximum error 0.00155 pp, explained by stored rounding. Collateral coverage reconciles. Costs are already negative net cash flows and are not deducted twice in the prediction pipeline.
- **Clipping:** one raw prediction is -0.004 and is floored to zero for a low-loss case. No upper-bound clipping occurred in this holdout.
- **Outcome uncertainty:** mean bias is +27.45 pp on 322 cures and -5.63 pp on 1,678 non-cures. Random outcomes unavailable at scoring time are consistent with overprediction of low losses and underprediction of high losses. This is diagnostic evidence, not a causal experiment isolating every error source.
- **Software:** predictor allowlists, training-only transforms, disjoint IDs and mappings pass. The approved model is unweighted; EAD weighting is diagnostic/reporting, not an omitted training weight. No post-holdout calibration was introduced.

## Simple LGD versus facility LGD
The current-portfolio bridge compares the original borrower proxy and facility model on identical borrowers, but has no realized workout outcomes. It cannot support MAE/RMSE claims. ECL is €39.31m for legacy LGD/legacy term, €56.19m for workout LGD/legacy term, and €45.27m for workout LGD/facility remaining maturity.

A separate diagnostic reapplies the frozen simple collateral formula to the resolved-workout holdout, using a fixed seed for its original synthetic unsecured-severity residual. This is a transferred formula benchmark, not a historical forecast or fitted challenger.

| Metric | Facility model | Reapplied simple proxy |
| --- | ---: | ---: |
| Overall MAE | 11.40 pp | 21.14 pp |
| Overall RMSE | 16.58 pp | 25.33 pp |
| Overall bias | -0.31 pp | -11.32 pp |
| Realized LGD >75% bias | -15.59 pp | -24.91 pp |

The simple proxy lacks facility product, lien, guarantee and workout structure; full-cash results can approach zero while workout LGD retains recovery friction. The richer workout generator is also the facility model's development environment. Better synthetic metrics do not establish superiority on real bank data. Calibration, collateral/product/lien segments and the loss tails are exported for both approaches.

## EAD, ECL and staging reconciliation
Every facility and borrower is checked. Selected independently recomputed examples:

| Facility | Stage | Applicable PD | LGD | EAD | ECL |
| --- | --- | ---: | ---: | ---: | ---: |
| SME08035-000001 | 1 | 2.252607% | 36.981509% | €1,191,213.33 | €9,923.38 |
| SME10174-000003 | 2 | 0.982598% lifetime | 46.779612% | €2,423,870.25 | €11,141.45 |
| SME06066-002223 | 3 | 100% | 73.910506% | €168,483.27 | €124,526.84 |

The Stage 2 example has one month remaining: lifetime PD is `1 - (1 - 0.1117436385)^(1/12)`. Under the existing methodology its ECL can be lower than the annualized 12-month diagnostic. Stage 3 uses LGD × EAD. Facility totals reconcile to borrower EAD/ECL within €0.02; example unrounded differences are near floating-point precision.

Stage 2 triggers, Stage 3 precedence and the nine-month EWS rule reconcile. Tests exercise months 8 and 9. Stage 2 defaults to Rating 7; watchlist/rating and accounting stage remain distinct. Cash Rating 1 requires Stage 1; write-off Rating 10 is distinct from DPD severity.

## Release evidence and boundaries
The complete local build passed **30 release checks and 27 unit/regression tests**. Streamlit tests passed five role views, three filter modes, literal-special-character search and borrower drill-down. Workflows retain CSV evidence and environment/data hashes. The README provides a complete rebuild command; generated data and model binaries remain outside Git to prevent stale results.

The system is a presentation-ready synthetic architecture demonstration, not production banking software or regulatory validation. See [known limitations and unimplemented recommendations](../docs/MODEL_LIMITATIONS.md) and [classified changes](../docs/V5_CHANGELOG.md).
