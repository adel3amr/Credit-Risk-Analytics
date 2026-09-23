# Methodology → source → test → result → report

| Approved relationship | Frozen source | Regression/independent check | Result | Paper section |
|---|---|---|---|---|
| Fixed logistic PD and approved inputs | `src/data_preparation.py`, `src/pd_model.py`, `notebooks/credit_risk_pipeline.py` | `independent_recalculation.py` rank-based AUC, Brier/log loss; output split manifest | 0.759455 AUC; 102/3,000 future defaults | 5, 10 |
| Macro PD weights and odds changes | `src/ecl.py`, `config/macro_scenarios.csv` | `independent_recalculation.py` computes scenario odds directly | Max difference 1.7e−16 | 3, 11 |
| EWS/9-month SICR and Stage 3 precedence | `src/early_warning.py`, `src/ecl.py` | `tests/test_review_policy_edges.py`; 3k independent reconstructed labels | 22 policy cases passed; zero label mismatches | 3, 5, 11 |
| Internal rating/watchlist distinct from stage | `src/scorecard.py` | Review migration test and 3k label counts | 287 rating-7 vs 221 Stage-2 borrowers | 5, 11 |
| Discounted recovery LGD target | `scripts/generate_lgd_workout_history.py` | `independent_recalculation.py` discounted raw cashflow PV | Max target discrepancy 1.55e−5 from stored rounding | 4, 12 |
| Frozen GB LGD | `src/lgd_model.py`, `notebooks/lgd_model_pipeline.py` | Facility-ID split and independent segments | 2k workout MAE .113965; >75% bias −.155928 | 4, 12 |
| Loan/OVD/trade EAD | Generator and `src/lgd_model.py` | `audit_frozen_data.py`, review product mapping test | 15/15 data checks; product amounts and 5,172 facility links reconcile | 5, 13 |
| Stage-specific facility ECL | `src/facility_ecl.py` | Numeric review oracle and `independent_recalculation.py` | Max individual difference 3.5e−10; borrower aggregate 1.2e−10 | 5, 13 |
| Current dashboard/workflow | `app.py`, `scripts/test_dashboard.py`, `.github/workflows/` | AppTest smoke, 25 independent dashboard source comparisons, local 49 tests and 30 release checks | Five demo role views, three filters, headline totals and one facility drill-down reconciled | 6, 14 |

Section numbers refer to `RESEARCH_REPORT.md`. Passing an identity test establishes conformity to the approved source logic; it is not a claim that the source methodology is institutionally optimal.
