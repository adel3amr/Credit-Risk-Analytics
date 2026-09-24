# LGD root cause: initial locked diagnostic (before challenger development)

**Research reference:** published V5 `0dfe4c8`; **prediction time:** reporting date for current facilities, with training inputs recorded at default before resolution. These dates are not identical and their transfer requires validation. No recovery outcome, cure, elapsed workout, future collateral realization or actual cash flow is available to a deployable forecast.

## Independent reconstruction

Using only `outputs/lgd_holdout_predictions.csv` joined one-to-one by facility ID to the original `data/raw/lgd_workout_history.csv` (SHA-256 `d1ff68a25593693039ee00b0d6b7a1f84b226d2d0995d9e6a54a897fcf5de220`), direct NumPy calculations reproduce on 2,000 rows: MAE .11396453, RMSE .16579849, bias −.00305172. The 327 realized LGDs above .75 have bias −.15592783. These are the frozen published predictions; no model training was performed for this check.

## Quantified cancellation

| Realized LGD band | N | EAD (millions) | Actual | Forecast | Mean error | Sum of 2,000 errors |
|---|---:|---:|---:|---:|---:|---:|
| 0–20% | 391 | 225.87 | .1125 | .3146 | +.2021 | +79.01 |
| 20–40% | 526 | 291.13 | .2850 | .3214 | +.0365 | +19.18 |
| 40–60% | 431 | 229.07 | .5043 | .4479 | −.0564 | −24.31 |
| 60–75% | 325 | 186.65 | .6744 | .5852 | −.0892 | −29.00 |
| 75–90% | 238 | 132.26 | .8144 | .6766 | −.1378 | −32.81 |
| 90–100% | 89 | 52.11 | .9477 | .7434 | −.2043 | −18.18 |

The positive 98.19 error units at realized LGD ≤40% offset 104.30 negative units elsewhere; total −6.10 units / 2,000 = −.00305. The realized bands are **retrospective**; they cannot assign a facility to the >75% group before recovery. The top 200 by *forecast* show −.02534 bias, a different population and actionable calibration question. A cure flag is unavailable at prediction: 322 eventual cures have +.27449 mean error (sum +88.39); 1,678 non-cures have −.05631 (sum −94.49). These facts support stochastic cure and regression smoothing, but they do not prove irreducibility without controlled experiments.

## Demonstrated support defect and attempted data correction

Only 1/8,000 original workouts has exactly zero guarantee coverage, versus 4,096/5,172 active facilities. The original training regime does not cover the dominant live guarantee input. The prior isolated support experiment added 12,000 development cases with the existing active guarantee map and used a different seed for 8,000 validation cases. The unchanged model specification improved validation-wide bias from +.0124 to −.0015, but for 1,618 realized >.75 cases worsened it from −.1313 to −.1466. This was a data support correction, not a severity solution; these datasets have already been examined and cannot be reused as a protected final holdout.

## Open hypotheses and test design

1. **Implementation:** recalculate discounted six-bucket cash flows, guarantee, collateral and clipping identities; compare source outputs. Existing review found no material arithmetic defect, but new generator needs independent identities.
2. **Information limitation:** fit a clearly non-deployable oracle with future cure/recovery information; compare against same-data, same-split deployable models. An oracle advantage establishes an information gap in the synthetic process, not a causal proof for real banks.
3. **Heterogeneous regimes:** test segmented and component models against a simple baseline and the fixed V5 architecture; fit all on development only, select on validation.
4. **Development/live shift:** report every feature's zero mass, range, quantiles, categorical support and differences on original development, validation and current facilities; avoid conflating a trade guarantee instrument with proven third-party recovery support.
5. **Economic materiality:** report group EAD and EAD-weighted error as well as unweighted errors; absence of real bank recoveries means materiality to actual allowances is unknown.

**Research status:** root cause not yet closed. Dataset generator changes and methodological candidates must remain outside V5 until formal validation; an apparently superior synthetic score is not a bank approval.
