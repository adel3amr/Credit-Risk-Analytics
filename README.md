# Credit Risk Analytics & SME PD Modeling

## Overview
End-to-end synthetic SME credit-risk project covering borrower PD, validation, credit scoring, early-warning monitoring, product-level EAD mechanics, aggregate LGD and a simplified IFRS 9-style staging/ECL layer.

> **Data note:** All customer and behavioural data are synthetic. Results demonstrate methodology under the stated data-generating assumptions; they are not estimates of a real bank portfolio.

## Architecture
```text
Current financials + current behaviour -> PIT-oriented 12M PD -> score / risk band
36-month behavioural history          -> EWS / monitoring
Macro scenarios                       -> forward-looking PD overlay
Reporting-date credit deterioration   -> simplified SICR / stage
Facilities                            -> EAD
Collateral / recovery assumptions     -> LGD
Forward-looking PD + stage + LGD + EAD -> simplified ECL
```

Logistic Regression is the governed primary PD model because interpretability and probability calibration are central to the use case. Random Forest and Gradient Boosting are challengers; the primary model is not selected by whichever algorithm happens to achieve the highest holdout AUC.

## Synthetic portfolio
- 12,000 SME borrowers.
- 36 monthly behavioural observations per borrower (432,000 borrower-months).
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
LGD is an aggregate borrower-level synthetic recovery proxy driven primarily by collateral coverage, with limited sector differentiation. Collateral is not allocated by individual facility, seniority or enforceability. A production implementation would require facility-level recovery data and recovery timing.

## PD model
The governed feature set uses current financial and behavioural information:
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

Trajectory variables are evaluated separately and are not forced into the governed PD merely to improve apparent model performance.

Validation includes ROC-AUC, Gini, KS, Brier score, log loss, calibration-in-the-large and calibration by holdout decile.

## Operational Risk Rating
The continuous PD-derived credit score is retained as a model-risk measure, while the workbench also exposes a bank-style **1-10 internal Risk Rating**:

- **1-6:** performing grades, ordered from strongest to weakest using transparent PD bands.
- **7:** Watchlist / enhanced monitoring. This is an operational monitoring grade and is not synonymous with IFRS 9 Stage 2.
- **8-10:** non-performing grades available only to Stage 3 borrowers; severity is differentiated using reporting-date delinquency.
- A non-Stage-3 borrower with **full eligible cash coverage** (recognized cash collateral coverage at least 99.9% of EAD) is assigned **Risk Rating 1**.
- Full cash security does **not** cure a Stage 3/non-performing exposure; staging remains governed separately.

The PD grade cut points are transparent synthetic policy assumptions and are not optimized on the holdout.

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

Stage 1 uses 12-month PD. Stage 2 uses a simplified lifetime-PD approximation based on current annual PD and the synthetic contractual term. Stage 3 uses a simplified discounted cash-shortfall workout: collateral-type-specific recognized recovery is reduced for synthetic realization costs and discounted over a synthetic recovery horizon, with recovery capped at EAD.

The ECL layer applies explicit upside, baseline and downside macroeconomic scenarios using GDP growth, unemployment, policy-rate and inflation shocks. These feed a fixed synthetic log-odds sensitivity mapping and are probability-weighted. The macro paths and sensitivities are methodology assumptions, not official forecasts or empirically estimated elasticities.

Important limitations include no true origination/reference PD comparison, no empirically estimated macro-credit model, no instrument-level effective-interest-rate workout engine, no facility-level lifetime EAD term structure, and one borrower-level contractual term for aggregate facilities.

## V2 information-set experiment
Logistic Regression is held constant while four nested information sets are compared:

1. Financial only.
2. Financial + current behaviour.
3. Financial + current behaviour + trajectory.
4. Full hybrid, adding synthetic qualitative/relationship variables.

The purpose is to test whether broader information adds out-of-sample discrimination, not to maximize AUC through feature accumulation. Paired bootstrap resampling is used for AUC differences.

The final V2 architecture keeps current behaviour in core PD and trajectory in the separate EWS layer. The frozen synthetic default DGP itself contains selected trajectory effects, so incremental trajectory discrimination is documented as a methodology result rather than treated as independent empirical evidence for expanding the governed PD feature set. Qualitative variables remain supplementary.

## Collateral and LGD methodology

The recovery layer generates collateral type before collateral value so that security is conditional on the exposure rather than assuming that every SME is heavily collateralised. The synthetic portfolio mix is 35% unsecured, 10% cash collateral, 35% mortgage and 20% other collateral. Nominal collateral coverage is generated from type-specific distributions.

For ECL recovery purposes, eligible cash collateral is recognized at 100% of nominal value (capped at EAD), mortgage collateral receives a 20% haircut, and other collateral receives a 35% haircut. Residual exposure after recognized collateral is treated as unsecured and carries the synthetic unsecured loss-severity assumption. These collateral shares, coverage distributions, haircuts and unsecured-LGD parameters are transparent project assumptions: they are not IFRS 9 minimums, regulatory haircuts, official benchmarks or empirically calibrated recovery rates.

The architecture is intentionally causal: EAD → collateral type → nominal collateral → recognized recovery → unsecured EAD → LGD → ECL. Haircuts are not tuned to obtain a target Stage 2 ECL ratio.

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
python notebooks/credit_risk_pipeline.py
python notebooks/hybrid_pd_experiment.py
python -m streamlit run app.py
```

Generate the synthetic data before running the analytics so the raw schema and governed feature set stay synchronized.

## Governance principles
- No future-default target leakage into reporting-date staging.
- Governed PD features are explicit; missing required features fail rather than being silently omitted.
- Logistic Regression is fixed as the primary model; RF/GB are challengers.
- Holdout results are reported, not optimized.
- The 9-month EWS threshold is fixed ex ante for V2 and is not retuned after seeing validation results.
- Synthetic assumptions and accounting simplifications are stated explicitly.
- The V2 DGP, PD specification, EWS threshold, staging logic and macro sensitivities are frozen after final validation; no post-holdout tuning is performed.

## Disclaimer
Educational synthetic portfolio project only. It is not a production credit model and does not constitute accounting, regulatory, lending or investment advice.
