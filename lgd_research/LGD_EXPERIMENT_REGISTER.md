# LGD experiment register — prefinal selection evidence

All entries use `run_study.py` and `results/development_scorecard.csv`; R2 training SHA-256 `b19f397ac75e39687efe5b35d940f6381597fc6800a037b6974b720383bd0216`, selection SHA `422b5c75d600675c0f498f6610d69fb8700650b92e006f7cfbc46d635991f652`. H SHA is `d1ff68a25593693039ee00b0d6b7a1f84b226d2d0995d9e6a54a897fcf5de220`. H split seed42; R2 seed20261101 development, 20261102 selection; 6,000 training rows for controlled 2×2, 9,000 for full R2. All R2 results below evaluate the same 3,000 selection rows (491 realized LGD >75%). Bias means predicted minus realized; fractions, multiply by 100 for percentage points.

| ID / hypothesis | Data/model | MAE | RMSE | Bias | >75 bias | Decision / failure reason |
|---|---|---:|---:|---:|---:|---|
| A: V5 portability | H 6k, unchanged GB | .12675 | .17574 | −.00755 | −.13053 | Reference transfer; not a bank validation. |
| B: extra data | R2 6k, unchanged GB | .12730 | .17031 | +.00354 | −.16356 | RMSE improves but tail worsens on changed generator. |
| C: two-stage architecture | H 6k, common inputs | .12968 | .17816 | −.01820 | −.12904 | No overall case for replacing V5 on H-trained transfer. |
| D: data × method | R2 6k, common two-stage | .12670 | .16982 | +.00352 | −.15899 | Interaction measurable; tail remains. |
| S: simple segment mean | R2 9k | .15283 | .19271 | +.00499 | −.20831 | Materially less accurate. |
| P: original simple proxy transfer | No fit; original collateral haircut and mean unsecured severity applied to already viewed R2 selection | .22222 | .26507 | −.14549 | −.25853 | **Added as a postfinal completeness diagnostic only**; not a locked final candidate. Its original random severity residual is unavailable for forecasting. |
| V5 GB same method | R2 9k | .12695 | .16983 | +.00376 | −.16478 | Better support, same severe issue. |
| Huber | R2 9k, unchanged feature set | .12375 | .17107 | +.01618 | −.13603 | Lower MAE but material aggregate positive bias. |
| Random forest | R2 9k, unchanged feature set | .12668 | .17032 | +.00440 | −.16332 | No robust advantage. |
| Enhanced GB | R2 9k, plus three observable-at-default proxies | .11095 | .15366 | +.00182 | −.13132 | Improvement on synthetic data; extra fields absent live. |
| Enhanced two-stage | R2 9k plus proxy fields | .11109 | .15347 | +.00187 | −.12018 | Preselected challenger finalist; residual tail issue. |
| Recovery components | R2 9k plus proxy fields | .10907 | .15520 | +.00450 | −.13113 | Lowest selection MAE, higher complexity and RMSE. |
| Future-information oracle | R2 9k plus *future* cure/shocks/duration | .03997 | .05226 | +.00016 | −.03547 | **Non-deployable**; information-gap diagnostic. |
| Quantile p90 | R2 9k, extra proxies | .15413 | .21524 | +.14539 | +.03241 | Upper risk bound only; unsuitable unbiased expected LGD. |

**Ablations:** remove collateral RMSE .22261, guarantee .15910, facility .15354, borrower .16061, all three new proxies .16983, versus enhanced GB .15366. Marginal effects are model/data dependent and not causal importances. Economic stress and all individual cohort metrics are in `results/stress_responses.csv` and `results/development_scorecard.csv`. These experiments were planned from the initial root-cause analysis; no favorable reseeding, grid search or holdout-based tuning was used. The final-holdout outcome was protected until `FINAL_EVALUATION_LOCK.md` recorded the candidate set.
