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

Stage 1 uses 12-month PD. Stage 2 uses a simplified lifetime-PD approximation based on current annual PD and the synthetic contractual term. Stage 3 uses LGD x EAD as a simplified 100% default-probability proxy.

The ECL layer applies explicit upside, baseline and downside macroeconomic scenarios using GDP growth, unemployment, policy-rate and inflation shocks. These feed a fixed synthetic log-odds sensitivity mapping and are probability-weighted. The macro paths and sensitivities are methodology assumptions, not official forecasts or empirically estimated elasticities.

Important limitations include no true origination/reference PD comparison, no empirically estimated macro-credit model, no discounted cash-shortfall engine, no facility-level lifetime EAD term structure, and one borrower-level contractual term for aggregate facilities.

## V2 information-set experiment
Logistic Regression is held constant while four nested information sets are compared:

1. Financial only.
2. Financial + current behaviour.
3. Financial + current behaviour + trajectory.
4. Full hybrid, adding synthetic qualitative/relationship variables.

The purpose is to test whether broader information adds out-of-sample discrimination, not to maximize AUC through feature accumulation. Paired bootstrap resampling is used for AUC differences.

The final V2 architecture keeps current behaviour in core PD and trajectory in the separate EWS layer. The frozen synthetic default DGP itself contains selected trajectory effects, so incremental trajectory discrimination is documented as a methodology result rather than treated as independent empirical evidence for expanding the governed PD feature set. Qualitative variables remain supplementary.

## Current governed validation
The latest chronological-data workflow should be treated as the current V2 baseline. On the 3,000-borrower holdout:
- governed Logistic Regression AUC: **0.7673**, Gini: **0.5346**;
- holdout observed default rate: **3.33%**;
- mean predicted PD: **3.33%**;
- Stage 1: **2,760 borrowers**, observed future default **2.8%**;
- Stage 2: **231 borrowers**, observed future default **9.5%**;
- Stage 3: **9 borrowers**; no holdout defaults were observed and the sample is far too small for inference;
- total holdout EAD: approximately **EUR 2.394bn**;
- mean PIT-oriented 12-month PD: **3.33%**;
- mean probability-weighted forward-looking PD: **3.53%**;
- upside / baseline / downside mean scenario PD: **2.84% / 3.33% / 4.82%**;
- PIT diagnostic 12-month ECL: approximately **EUR 25.97m**;
- forward-looking diagnostic 12-month ECL: approximately **EUR 27.53m**;
- simplified forward-looking staged ECL: approximately **EUR 37.75m**.

The fixed 9-month EWS policy is retained without post-holdout threshold optimization. Its results are interpreted as synthetic policy diagnostics rather than evidence of a universal SICR timing rule.

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
├── dashboard/app.py
├── outputs/
└── docs/
```

## Run
```bash
pip install -r requirements.txt
python scripts/generate_sme_portfolio.py
python notebooks/credit_risk_pipeline.py
python notebooks/hybrid_pd_experiment.py
streamlit run dashboard/app.py
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
