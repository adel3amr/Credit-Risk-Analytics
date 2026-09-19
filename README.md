# Credit Risk Analytics & Probability of Default Modeling

## Overview
End-to-end credit risk analytics project simulating a commercial banking SME portfolio. The project develops and validates Probability of Default (PD) models, converts PD into an interpretable credit score, segments borrowers by risk, and estimates Expected Credit Loss (ECL) using PD × LGD × EAD.

> **Data note:** The portfolio is fully synthetic and contains no real customer information.

## Objectives
- Analyze portfolio-level credit risk and default behavior
- Build an interpretable Logistic Regression PD model and benchmark tree-based models
- Evaluate ROC-AUC, Gini, KS and Brier score
- Produce borrower-level PDs and credit scores
- Segment exposures into Low / Moderate / High / Very High risk
- Estimate 12-month and simplified lifetime ECL
- Provide a Streamlit risk dashboard

## Methodology
### PD modeling
Three models are compared:
1. Logistic Regression — interpretable baseline
2. Random Forest — nonlinear benchmark
3. Gradient Boosting — nonlinear benchmark

### Model validation
- ROC-AUC
- Gini coefficient
- Kolmogorov-Smirnov (KS) statistic
- Brier score / probability calibration proxy

### Credit scoring
PD is transformed into a score using a conventional odds-based scorecard relationship. Higher scores indicate lower modeled default risk.

### IFRS 9-style ECL
A simplified framework is implemented:

**12-month ECL = PD × LGD × EAD**

Risk stages are assigned using PD thresholds:
- Stage 1: PD < 3%
- Stage 2: 3% ≤ PD < 15%
- Stage 3: PD ≥ 15%

Lifetime ECL uses illustrative maturity multipliers. These assumptions are educational and are not intended to reproduce a bank's regulatory or accounting model.

## Project Structure
```text
credit-risk-analytics/
├── data/
│   ├── raw/sme_credit_portfolio.csv
│   └── processed/scored_portfolio.csv
├── notebooks/credit_risk_pipeline.py
├── src/
│   ├── data_preparation.py
│   ├── pd_model.py
│   ├── validation.py
│   ├── scorecard.py
│   └── ecl.py
├── dashboard/app.py
├── outputs/
├── reports/
├── requirements.txt
└── README.md
```

## How to Run
```bash
pip install -r requirements.txt
python notebooks/credit_risk_pipeline.py
streamlit run dashboard/app.py
```

## Key Risk Variables
The synthetic portfolio includes financial and behavioral indicators such as:
- EBITDA margin
- Leverage ratio
- Current ratio
- Debt-to-income ratio
- Credit utilization
- Recent delinquencies
- Previous defaults
- Days past due
- Collateral coverage
- Years in business
- Industry

## Business Interpretation
The project demonstrates how a bank can combine borrower financial information and behavioral indicators to:
- differentiate credit risk,
- prioritize manual underwriting,
- identify high-risk exposures,
- estimate expected losses,
- support risk-based pricing and portfolio monitoring.


## V2 — Hybrid SME PD & Risk Direction

The V2 experiment extends the original point-in-time PD framework by asking a different modeling question:

> **How does the information available to the model change SME risk differentiation?**

Rather than changing algorithms, the experiment holds Logistic Regression constant and compares three nested information sets:

1. **Financial only** — profitability, leverage, liquidity, debt burden, collateral and business maturity.
2. **Financial + Behavioral** — adds current utilization/delinquency information and synthetic trajectory variables such as 6-month utilization change, average utilization, months above 80% and limit breaches.
3. **Hybrid** — additionally introduces structured relationship/qualitative indicators such as relationship tenure, account conduct, management quality, reporting quality, information cooperation and covenant compliance.

Run:

```bash
python notebooks/hybrid_pd_experiment.py
```

The experiment produces:
- `outputs/information_set_comparison.csv` — AUC, Gini, KS and Brier by information set.
- `outputs/borrower_pd_comparison.csv` — borrower-level PD comparison across the three specifications.
- `outputs/information_set_auc.png` — discrimination comparison suitable for reporting.
- `outputs/utilization_trend_pd_uplift.png` — relationship between utilization direction and incremental hybrid PD.

### Why compare information sets?

The purpose is not simply to find the algorithm with the highest AUC. Holding the modeling technique constant makes the comparison easier to interpret: it tests the incremental signal associated with broader borrower information in this synthetic experiment.

This also operationalizes a portfolio-monitoring distinction between **risk level** and **risk direction**. A current utilization ratio describes a level; a sustained increase in utilization is a trajectory. Both can matter to a credit assessment.

### Synthetic-data limitation

All borrower data in this repository are synthetic. The V2 qualitative and trajectory variables are also synthetically derived using reproducible assumptions and seeded randomness. The default target is **not** used directly to construct these added features, which avoids direct target leakage; however, several features share underlying financial/behavioral drivers with the existing synthetic portfolio.

Consequently, any improvement in model performance should be interpreted only as a demonstration of methodology under the simulated data-generating assumptions. It is **not empirical evidence** that a particular qualitative factor or behavioral trend improves real-world SME default prediction. A production model would require observed historical data, time-aware development/validation samples, governance, stability testing, calibration and independent validation.

## Disclaimer
This is an educational portfolio project using synthetic data. It is not a production credit model and does not constitute financial, accounting, regulatory, or lending advice.
