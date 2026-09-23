# Final Project Release — reviewed 2026-09-23

## Release status
This release incorporates the independent code review completed after the 2026-09-22 project freeze. The review confirmed the core architecture while identifying stale generated artifacts and several methodology/robustness seams. Those findings are remediated in the current release.

## Portfolio and sample design
The synthetic portfolio contains **12,000 SME borrowers** and **432,000 borrower-month observations** (36 months per borrower). The model-development split is **9,000 training borrowers + 3,000 untouched holdout borrowers**. The 3,000-borrower figure is therefore the final validation sample, not the total portfolio.

Generated raw/processed CSVs and validation outputs are no longer version-controlled. They are regenerated from the deterministic generator and pipeline so committed artifacts cannot drift away from the current code.

## Governed PD model
Logistic Regression remains the primary borrower-level 12-month PIT-oriented PD model. Random Forest and Gradient Boosting remain challengers. The primary model is fixed by governance rather than selected dynamically from holdout AUC.

Current holdout validation:
| Metric | Value |
|---|---:|
| ROC-AUC | 0.7599 |
| Gini | 0.5198 |
| KS | 0.3995 |
| Brier | 0.0322 |
| Log Loss | 0.1354 |
| Mean predicted PD | 3.38% |
| Observed default rate | 3.47% |
| Calibration-in-the-large | +0.08 pp |

The information-set experiment now compares only financial, current-behaviour and trajectory layers. Synthetic qualitative re-encodings of baseline variables were removed from the comparison. Current behaviour adds material out-of-sample discrimination (AUC 0.7147 -> 0.7599); trajectory does not add convincing incremental discrimination (0.7599 -> 0.7587; paired bootstrap mean difference -0.0012, 95% interval -0.0082 to +0.0059).

## EAD, LGD and ECL
Term-loan EAD is current outstanding. OVD EAD is the approved limit. Trade EAD is nominal issued exposure multiplied by a transparent synthetic CCF.

Stage 2 no longer applies one borrower-level contractual term to all products. Lifetime PD/ECL uses facility-specific synthetic remaining-life horizons:
- term loan: explicit reporting-date remaining months;
- OVD: 12-month annual-review horizon;
- trade: instrument-specific synthetic remaining life.

Stage 3 no longer assumes an implicit 100% loss on unsecured exposure. The workout combines:
1. collateral timing/realization-cost loss on recognized collateral; and
2. unsecured EAD multiplied by the synthetic unsecured loss-severity assumption.

Current holdout ECL snapshot:
| Stage | Borrowers | EAD | ECL | ECL / EAD |
|---|---:|---:|---:|---:|
| Stage 1 | 2,763 | EUR 1.927bn | EUR 20.10m | 1.04% |
| Stage 2 | 227 | EUR 157.93m | EUR 8.11m | 5.14% |
| Stage 3 | 10 | EUR 5.46m | EUR 2.36m | 43.23% |

Total staged ECL is approximately **EUR 30.58m**. PIT 12-month diagnostic ECL is approximately **EUR 24.93m** and forward-looking 12-month diagnostic ECL is approximately **EUR 26.40m**.

## Risk rating and EWS
Risk Rating 1 is reserved for non-Stage-3 borrowers with full eligible cash coverage. Ratings 2-6 are performing PD grades, Rating 7 is an explicit Stage-1 operational watchlist grade, and Ratings 8-10 are Stage-3 severity grades. The rating implementation now uses the explicit post-staging watchlist flag rather than silently broadening Rating 7 to all deteriorating borrowers.

EWS remains separate from PD and from accounting stage. A fixed nine-month persistence rule is retained as a synthetic policy assumption, not an IFRS 9 requirement.

## Governance and robustness
The reviewed release:
- fixes override audit baselines for every override type;
- gives the Risk Management workspace its own borrower selector rather than reusing cross-tab state;
- uses fixed demo identities so maker-checker cannot be bypassed by typing a different username;
- fails closed on duplicate role configurations;
- rejects null PDs before risk-rating conversion;
- removes the superseded duplicate Streamlit app;
- uses label-safe borrower selection in the pipeline;
- adds independent tests for score monotonicity, rating reachability, Stage-2 lifetime ECL, Stage-3 unsecured severity and governance failure modes;
- keeps CI runtime smoke testing for the Streamlit application.

## Interpretation
This remains an educational synthetic methodology project, not a production bank model, regulatory capital engine or accounting opinion. Aggregate LGD is still borrower-level; production workout LGD would require facility-level collateral allocation, seniority, enforceability, recovery cash-flow timing, workout costs and empirical recovery calibration.
