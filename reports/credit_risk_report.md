# Credit Risk Model Validation Report

## Executive Summary
This report documents the development of a synthetic SME Probability of Default model and a portfolio-level Expected Credit Loss framework.

## Scope
The analysis covers data preparation, exploratory risk analysis, PD model development, model benchmarking, validation, credit scoring, risk segmentation, and ECL estimation.

## Models
Logistic Regression is used as the primary interpretable benchmark. Random Forest and Gradient Boosting are included to test whether nonlinear relationships improve discrimination.

## Validation
The models are compared using ROC-AUC, Gini, KS and Brier score. In a production setting, model selection should consider discrimination, calibration, stability, interpretability, governance requirements and economic rationale rather than AUC alone.

## ECL Framework
The project uses the simplified relationship PD × LGD × EAD for 12-month ECL. Lifetime ECL is illustrated through stage-dependent multipliers. A production IFRS 9 implementation would require significantly richer assumptions including forward-looking macroeconomic scenarios, probability-weighted outcomes, discounting, staging criteria and documented model governance.

## Limitations
- Synthetic data
- No macroeconomic scenarios
- No time-series / vintage validation
- No reject inference
- Simplified LGD and EAD
- Simplified IFRS 9 staging and lifetime loss assumptions

## Conclusion
The project demonstrates an end-to-end credit risk analytics workflow suitable for portfolio monitoring and as a technical demonstration of PD modeling, model validation, credit scoring and ECL concepts.
