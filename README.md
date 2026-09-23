# Credit Risk Analytics & SME PD Modeling

## Overview
End-to-end synthetic SME credit-risk platform covering borrower PD, independent qualitative underwriting information, early-warning monitoring, internal risk rating, facility-level EAD, workout-LGD modelling, simplified IFRS 9-style staging/ECL, model validation and governed human intervention.

> **Data note:** All customer and behavioural data are synthetic. Results demonstrate methodology under the stated data-generating assumptions; they are not estimates of a real bank portfolio.

## Architecture
```text
Financials + current behaviour + independent qualitative underwriting -> 12M PD
36-month behavioural history                                      -> EWS / monitoring
Reporting-date deterioration                                      -> simplified SICR / stage
Resolved historical default/workout facilities                    -> workout LGD model
Current facilities + collateral + product + seniority             -> facility LGD
Facility EAD + remaining maturity + borrower PD/stage + LGD        -> facility ECL
Facility ECL                                                       -> borrower / portfolio ECL
Macro scenarios                                                    -> forward-looking PD overlay
Policy + human override                                            -> governed internal rating
```

Logistic Regression is the governed primary PD model because interpretability and probability calibration are central to the use case. Random Forest and Gradient Boosting are challengers; the primary model is not selected by whichever algorithm happens to achieve the highest holdout AUC.

## Synthetic portfolio
- **12,000 SME borrowers in total.**
- **9,000 borrowers are used for model development/training.**
- **3,000 borrowers (25%) are kept untouched for final out-of-sample validation.**
- 36 monthly behavioural observations per borrower (432,000 borrower-months).

The 3,000-borrower holdout is part of the 12,000-borrower portfolio; it is not an additional sample.
- Term loans, overdrafts (OVD) and trade-finance facilities.
- Chronological utilization history generated forward from M-35 to reporting date M0.
- Future 12-month default is generated only after reporting-date borrower information is constructed.

### EAD policy
For this project:
- **Term-loan EAD = 100% of current withdrawn/outstanding amount.**
- **OVD EAD = 100% of approved total limit.**
- Trade-finance EAD = instrument amount x transparent synthetic CCF.
- Total borrower EAD = sum of product EADs.

Trade CCFs and other portfolio-generation parameters are synthetic methodology assumptions, not regulatory prescriptions.

### LGD
The governed LGD layer is now a separate **facility-level workout model** trained on a synthetic history of resolved defaulted facilities. The workout history contains EAD at default, product type, collateral, lien rank, guarantee coverage, borrower condition, recovery cash flows, workout costs and recovery timing.

Economic LGD is defined from discounted net recoveries relative to EAD at default. Post-default outcomes such as realized recovery cash flows, workout timing, cure outcome and write-off outcome are retained for target construction and audit but are excluded from the predictive feature set. A Gradient Boosting regression is fixed ex ante as the governed non-linear LGD model and Ridge is retained as an interpretable challenger.

For the current portfolio, each borrower is expanded into its live term-loan, OVD and trade facilities. Facility LGDs are predicted separately and then EAD-weighted back to borrower level for reporting.

## PD model
The governed PD feature set uses current financial, behavioural **and genuinely additional qualitative underwriting information**:
- EBITDA margin
- leverage ratio
- current ratio
- debt-to-income
- collateral coverage
- years in business
- current credit utilization
- delinquencies in the last 12 months
- previous defaults
- days past due
- industry
- management quality
- governance quality
- financial reporting quality
- market position
- sponsor/support strength
- customer concentration
- supplier concentration
- key-person dependency
- audit quality

The qualitative fields are generated independently of the financial ratios and account behaviour. They therefore test genuinely incremental underwriting information rather than re-encoding variables the model has already seen. Trajectory variables are still evaluated separately and remain primarily an EWS/monitoring layer unless they demonstrate robust incremental value.

Validation includes ROC-AUC, Gini, KS, Brier score, log loss, calibration-in-the-large and calibration by holdout decile.

## Operational Risk Rating
The continuous PD-derived credit score is retained as a model-risk measure, while the workbench also exposes a bank-style **1-10 internal Risk Rating**:

- **1:** reserved for non-Stage-3 borrowers with full eligible cash coverage (recognized cash collateral coverage at least 99.9% of EAD).
- **2-6:** performing grades, ordered from strongest to weakest using transparent PD bands.
- **7:** Watchlist / enhanced monitoring. Stage 2 maps to Rating 7 by default, but Rating 7 does **not** itself create Stage 2. A rare Stage-2 Rating-6 case is a documented human override rather than an automatic rule.
- **8:** defaulted / Stage 3 exposure.
- **9:** severe NPL / advanced delinquency.
- **10:** explicit write-off status. Rating 10 is not created by DPD alone.
- Full cash security does **not** cure Stage 2/Stage 3 status; Rating 1 applies only to Stage 1 full eligible cash cover.

Risk Rating 1 is therefore not a low-PD grade: a low-PD borrower without full cash coverage starts at Rating 2. The PD grade cut points are transparent synthetic policy assumptions and are not optimized on the holdout.

## Early-warning system
The EWS is a separate monitoring layer using:
- six-month utilization increase,
- persistent high utilization,
- limit breaches.

Two or more signals produce an EWS **Deteriorating** status; one produces **Watch**. Thresholds are transparent synthetic monitoring assumptions, not empirically calibrated production triggers.

A predefined internal synthetic policy moves a currently deteriorating borrower to Stage 2 after **9 consecutive months** satisfying the EWS deterioration rule. `consecutive_ews_months` measures rule persistence, not literal operational watchlist tenure. Nine months is **not an IFRS 9 requirement** and is not optimized on the holdout sample.

## Simplified IFRS 9-style staging and ECL
This repository is not a production IFRS 9 accounting engine.

- **Stage 3:** current credit-impaired flag or DPD >= 90.
- **Stage 2:** simplified SICR proxies including DPD/conduct/history triggers and the fixed 9-month EWS-persistence policy.
- **Stage 1:** exposures not meeting Stage 2 or Stage 3 conditions.

ECL is calculated at **facility level** and then aggregated to the borrower. Stage 1 uses 12-month forward-looking PD × facility LGD × facility EAD. Stage 2 uses a constant-hazard lifetime-PD approximation based on each facility's **reporting-date remaining maturity**, rather than applying one borrower-level term to the whole exposure. Stage 3 uses the governed workout-LGD estimate with PD effectively equal to 100%; the older direct collateral cash-shortfall calculation is retained only as a challenger/diagnostic.

The ECL layer applies explicit upside, baseline and downside macroeconomic scenarios using GDP growth, unemployment, policy-rate and inflation shocks. These feed a fixed synthetic log-odds sensitivity mapping and are probability-weighted. The macro paths and sensitivities are methodology assumptions, not official forecasts or empirically estimated elasticities.

Important limitations remain: no true origination/reference PD for a full IFRS 9 SICR comparison, no empirically estimated macro-credit satellite model, synthetic rather than observed workout history, and simplified facility maturity/CCF assumptions. The architecture is designed to resemble real bank risk systems; the numerical calibration is not represented as production-ready or regulatory-approved.

## Incremental-information experiment
Logistic Regression is held constant while four nested information sets are compared:

1. Financial only.
2. Financial + current behaviour.
3. Financial + current behaviour + trajectory.
4. Full hybrid + **independent qualitative underwriting information**.

The purpose is to measure incremental information content rather than maximize AUC through feature accumulation. The qualitative layer is no longer built from quantiles or transformations of the financial/behavioural variables. All fields exist before the train/holdout split, eliminating the earlier full-sample quantile contamination. Paired bootstrap resampling is used for AUC differences.

## Collateral, recovery and workout-LGD methodology

The recovery layer generates collateral type before collateral value so that security is conditional on the exposure rather than assuming that every SME is heavily collateralised. The synthetic portfolio mix is 35% unsecured, 10% cash collateral, 35% mortgage and 20% other collateral. Nominal collateral coverage is generated from type-specific distributions.

For ECL recovery purposes, eligible cash collateral is recognized at 100% of nominal value (capped at EAD), mortgage collateral receives a 20% haircut, and other collateral receives a 35% haircut. Residual exposure after recognized collateral is treated as unsecured and carries the synthetic unsecured loss-severity assumption. These collateral shares, coverage distributions, haircuts and unsecured-LGD parameters are transparent project assumptions: they are not IFRS 9 minimums, regulatory haircuts, official benchmarks or empirically calibrated recovery rates.

The architecture is intentionally layered: facility EAD → facility security/product/seniority → workout-LGD estimate → stage-specific facility ECL → borrower aggregation. The original deterministic collateral proxy remains available as a challenger/diagnostic but is no longer the governed LGD input to ECL.

## Current governed validation
The final frozen workflow uses a 3,000-borrower untouched holdout. These figures are generated by the current repository release rather than carried forward from earlier DGP versions:

- governed Logistic Regression ROC-AUC: **0.7599**, Gini: **0.5198**, KS: **0.3995**;
- Brier score: **0.0322**; Log Loss: **0.1354**;
- holdout observed default rate: **3.47%**;
- mean predicted PD: **3.38%**; calibration-in-the-large (observed minus predicted): **+0.08 percentage points**;
- Stage 1: **2,763 borrowers**, EAD **EUR 1.927bn**, ECL **EUR 20.10m**, ECL/EAD **1.04%**;
- Stage 2: **227 borrowers**, EAD **EUR 157.93m**, ECL **EUR 14.83m**, ECL/EAD **9.39%**;
- Stage 3: **10 borrowers**, EAD **EUR 5.46m**, ECL **EUR 3.22m**, ECL/EAD **58.96%**;
- total holdout EAD: approximately **EUR 2.090bn**;
- mean PIT-oriented 12-month PD: **3.38%**;
- mean probability-weighted forward-looking PD: **3.58%**;
- upside / baseline / downside mean scenario PD: **2.89% / 3.38% / 4.87%**;
- PIT diagnostic 12-month ECL: approximately **EUR 24.93m**;
- forward-looking diagnostic 12-month ECL: approximately **EUR 26.40m**;
- simplified forward-looking staged ECL: approximately **EUR 38.15m**.

Logistic Regression remains the governed model by design, not because the holdout was used to select the best algorithm. Fixed reference-threshold classification diagnostics are supplementary operational views; thresholds are not optimized against the holdout. The fixed 9-month EWS policy is likewise retained without post-holdout optimization.

## Project structure
```text
Credit-Risk-Analytics/
├── data/
│   ├── raw/
│   │   ├── sme_credit_portfolio.csv
│   │   └── sme_behavioral_history_36m.csv
│   └── processed/scored_portfolio.csv
├── scripts/generate_sme_portfolio.py
├── notebooks/
│   ├── credit_risk_pipeline.py
│   └── hybrid_pd_experiment.py
├── src/
│   ├── data_preparation.py
│   ├── pd_model.py
│   ├── lgd_model.py
│   ├── facility_ecl.py
│   ├── validation.py
│   ├── scorecard.py
│   ├── early_warning.py
│   └── ecl.py
├── app.py
├── outputs/
└── docs/
```

## Run
```bash
pip install -r requirements.txt
python scripts/generate_sme_portfolio.py
python scripts/generate_lgd_workout_history.py
python notebooks/lgd_model_pipeline.py
python notebooks/credit_risk_pipeline.py
python notebooks/hybrid_pd_experiment.py
python -m streamlit run app.py
```

Generate the synthetic data before running the analytics so the raw schema and governed feature set stay synchronized.

Generated raw/processed CSVs and model outputs are intentionally not version-controlled. The scripts and CI recreate them deterministically, preventing stale committed artifacts from contradicting the current code.

## Governance principles
- No future-default target leakage into reporting-date staging.
- Governed PD features are explicit; missing required features fail rather than being silently omitted.
- Logistic Regression is fixed as the primary model; RF/GB are challengers.
- Holdout results are reported, not optimized.
- The 9-month EWS threshold is fixed ex ante for V2 and is not retuned after seeing validation results.
- Synthetic assumptions and accounting simplifications are stated explicitly.
- PD and LGD are validated on separate untouched holdouts.
- Realized recovery cash flows, cure outcome, recovery timing and write-off outcome are excluded from LGD model inputs.
- Model output, accounting stage, internal rating and human override remain separate governed objects.
- Methodology changes are versioned and reviewed rather than silently optimized against holdout results.

## Disclaimer
Educational synthetic portfolio project only. It is not a production credit model and does not constitute accounting, regulatory, lending or investment advice.
