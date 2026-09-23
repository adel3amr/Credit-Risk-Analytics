# V5 LGD validation decision

V5 evaluates fixed LGD challengers against the V4 Gradient Boosting champion on the same deterministic 2,000-facility synthetic holdout. All LGD values and errors below are proportions; multiply by 100 for percentage points. The holdout has already been inspected repeatedly and is **validation evidence, not a fresh model-selection sample**.

## Results

| Model | Holdout MAE | Holdout RMSE | Mean bias (predicted - actual) | EAD-weighted bias | Train-to-holdout MAE gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gradient Boosting (governed) | 0.1140 | 0.1658 | -0.0031 | -0.0013 | 0.0017 |
| Huber Gradient Boosting | 0.1042 | 0.1673 | +0.0214 | +0.0242 | 0.0002 |
| Random Forest | 0.1126 | 0.1655 | -0.0034 | -0.0019 | 0.0092 |
| Histogram Gradient Boosting | 0.1127 | 0.1662 | -0.0033 | -0.0027 | 0.0118 |
| Ridge | 0.1198 | 0.1691 | -0.0007 | +0.0041 | -0.0024 |

The original `lgd_challenger_tail_comparison.csv` ranks each model's own predictions, so its rows have different facility membership. The V5 `lgd_fixed_cohort_tail_comparison.csv` evaluates every model on identical facilities selected by the champion's predicted LGD. On the champion's top 10% (200 facilities), the EAD-weighted bias is -4.41 percentage points for the champion, +1.77 for Huber and -2.38 for Histogram Gradient Boosting. On the top 5% (100 facilities), it is -6.48, -0.70 and -3.89 percentage points respectively. Huber's tail improvement comes with +2.42 percentage points of EAD-weighted overprediction on the whole holdout and a slightly worse overall RMSE. Histogram Gradient Boosting has a larger train-to-holdout MAE gap than the champion.

The file also includes a **realized-outcome top-loss cohort** to expose cases the predictions miss. This cohort is defined using actual LGD, which is unavailable when a live facility is scored. Its large negative bias is a retrospective diagnostic and cannot be used as a deployment selection rule. Neither cohort alone establishes how a challenger will perform on a new vintage.

## Decision

**Retain Gradient Boosting as the governed V5 LGD champion.** Keep the challengers and fixed-cohort diagnostics as validation artifacts. Do not introduce a tail uplift or switch to Huber based on the repeatedly observed holdout. The material tail underprediction remains an open model limitation, particularly for severe loss and unsecured/OVD segments. A future replacement needs newly collected or genuinely independent workout vintages, a development/selection split, a separate untouched out-of-time validation sample, explicit segment and aggregate calibration criteria, and approval of its ECL impact. Synthetic holdout results are not evidence of a real bank portfolio's recovery performance.
