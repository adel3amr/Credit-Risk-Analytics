# Research deviations from frozen V5 (no production approval)

| ID | Change | Type | Current disposition |
|---|---|---|---|
| M0 | Published V5: 220-tree squared-error Gradient Boosting, six numeric/four categorical inputs, discounted cash-flow target | **Frozen benchmark** | Commit `0dfe4c8`, original file hash in data register; never rewritten. |
| M1 | New R2 synthetic recovery process with correlated downturn, security quality, guarantor strength and future shock fields | **Experimental data-generating assumptions** | Isolated research datasets. Comparisons across H/R2 are process-sensitive, not historical performance improvement. |
| M2 | GB plus security/guarantor/downturn fields | **Methodological feature change** | Experiment only. These fields are absent in the live V5 data, so the candidate is currently non-deployable. |
| M3 | Two-stage severe probability and conditional means, threshold .75 fixed before evaluation | **Methodological structure change** | Experiment only; conditional means recombined as an expected-LGD forecast, no automatic ECL change. Threshold sensitivity would require a separate preregistered study. |
| M4 | Component recovery, duration and costs, then discounted cash shortfall | **Methodological structure change** | Experiment only, higher operating complexity. |
| M5 | Huber or random forest on unchanged input set | **Algorithmic challengers** | Experiment only, no V5 promotion. |
| M6 | Conditional .90 quantile and future-information oracle | **Non-deployable diagnostic objectives** | Quantile is a risk bound, not expected LGD. Oracle uses future resolution variables and cannot be scored prospectively. |

No challenger is allowed into V5 or ECL solely because its synthetic metric improves. Change approval requires a controlled live-data policy review, performance validation and reproducible ECL impact assessment.
