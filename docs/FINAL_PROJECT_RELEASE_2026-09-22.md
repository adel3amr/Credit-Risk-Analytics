# Final Project Release — 2026-09-22

## Release status
This checkpoint freezes the portfolio architecture, governed PD methodology, EWS separation, collateral/LGD recovery architecture, simplified IFRS 9-style staging/ECL layer, governance controls and Streamlit credit workbench for the final project release.

## Governed model
Logistic Regression is the primary borrower-level 12-month PIT-oriented PD model. Random Forest and Gradient Boosting remain challengers. Model choice is not made dynamically from holdout AUC.

Trajectory features remain in the EWS/monitoring layer rather than being forced into core PD. Qualitative variables remain supplementary.

## Final holdout validation
Untouched holdout: 3,000 borrowers.

| Metric | Final value |
|---|---:|
| ROC-AUC | 0.7599 |
| Gini | 0.5198 |
| KS | 0.3995 |
| Brier | 0.0322 |
| Log Loss | 0.1354 |
| Mean predicted PD | 3.38% |
| Observed default rate | 3.47% |
| Calibration-in-the-large | +0.08 pp |

Fixed reference-threshold classification diagnostics are supplementary operational diagnostics only. They do not redefine the probabilistic PD model and are not optimized on the holdout.

## Final ECL snapshot
| Stage | Borrowers | EAD | ECL | ECL / EAD |
|---|---:|---:|---:|---:|
| Stage 1 | 2,763 | EUR 1.927bn | EUR 20.10m | 1.04% |
| Stage 2 | 227 | EUR 157.93m | EUR 14.83m | 9.39% |
| Stage 3 | 10 | EUR 5.46m | EUR 3.22m | 58.96% |

Total staged ECL: **EUR 38.15m**. Mean PIT-oriented 12-month PD is 3.38%; probability-weighted forward-looking PD is 3.58%. PIT 12-month diagnostic ECL is EUR 24.93m and forward-looking 12-month diagnostic ECL is EUR 26.40m.

## Exposure and recovery architecture
Term-loan EAD is current outstanding. OVD EAD is the approved limit. Trade EAD is nominal issued exposure multiplied by a transparent synthetic CCF. Separate approved-limit fields support direct, indirect and total portfolio utilization reporting without redefining EAD.

Collateral type is generated before collateral value. Synthetic recognition is Cash 100%, Mortgage 80%, Other 65%, Unsecured 0%, capped at EAD. Stage 3 starts from the same recognized-collateral architecture, then applies explicit synthetic workout cost, timing and discount assumptions. These assumptions are not regulatory prescriptions or empirical recovery estimates.

## Portfolio intelligence
The workbench provides portfolio composition, direct/indirect exposure, approved limits and utilization, industry diagnostics, broad predefined risk-pattern monitoring, EWS review, borrower credit files, governed overrides and macro-scenario controls.

Portfolio review prompts are descriptive screening aids. They do not automatically approve, decline, stage or override borrowers. Broad monitoring cuts are intentionally preferred over fitting a decision tree to the holdout.

## Governance and validation controls
- future default is never used for reporting-date staging;
- missing governed PD features fail explicitly;
- maker-checker override controls separate model output from human decisions;
- macro assumptions are separately controlled;
- borrower-level audit identities reconcile EAD, PD, staging and ECL;
- CI regenerates the synthetic portfolio and analytics;
- CI executes a Streamlit runtime smoke test rather than syntax checks alone.

## Interpretation
This is a synthetic methodology project, not a production bank model, regulatory capital engine or accounting opinion. Numerical results are conditional on the frozen synthetic DGP and should not be interpreted as external SME benchmarks. Methodology changes are documented rather than presented as model-performance improvements.
