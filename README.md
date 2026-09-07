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

## Disclaimer
This is an educational portfolio project using synthetic data. It is not a production credit model and does not constitute financial, accounting, regulatory, or lending advice.
