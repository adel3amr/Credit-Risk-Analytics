# Known limitations and future methodological recommendations

## Open limitations

1. **High-loss LGD tail:** 327 holdout realized losses >75% average 15.59 pp underprediction; n=89 above 90% averages 20.43 pp. Forecast-selected top decile has smaller but negative bias of 2.53 pp. The tail risk remains open after checking data support, cash-flow arithmetic, split integrity, clipping and forecast propagation. Aggregate bias does not override it.
2. **Cure/recovery outcome uncertainty:** cure cases average 27.45 pp forecast-minus-realization; non-cure cases −5.63 pp. Their eventual outcome is not observable at decision time. The current synthetic predictors cannot distinguish all extreme realizations; using ex-post indicators would leak outcomes.
3. **Synthetic single-vintage evidence:** no external institution or out-of-time multi-vintage workout performance, no empirical macro shocks, no confidence bands for sparse extreme strata. A 2,000-facility holdout with only 25 ≥97%-LGD cases cannot yield a precise near-total-loss benchmark.
4. **IFRS 9-style illustration:** stage proxies, term hazard and internal nine-month watchlist rule are project assumptions. Review proves adherence to source rules, not an institution-specific interpretation or accounting compliance conclusion.
5. **Application/governance:** demo role identities do not enforce production authentication; dashboard was covered by AppTest rather than a full manual browser/accessibility/security audit. CI is locally reproduced, not remotely witnessed in this review.
6. **Legacy comparator:** the old simple LGD formula is reapplied with fresh fixed-seed noise to the resolved-workout sample; this is not archived historical forecasts nor a prospective live-portfolio performance study.

## Future methodological work — recommendations only, **not implemented**

- Subject to separate approval, evaluate whether additional *pre-workout observable* recovery indicators, separately estimated cure behavior, distributional loss forecasts, or segment-specific calibration address operational severity risk. These are **METHODOLOGICAL CHANGES**, not code fixes.
- Seek actual multi-vintage default and recovery data, counterparty/guarantor realizations and external-period monitoring before relying on numerical error estimates. Development data and untouched future validations must remain separate.
- Independently assess whether stage and ECL simplifications fit a specific institution's approved accounting policy. Do not silently replace the internal nine-month rule or add externally inferred thresholds to this frozen version.

## Software/validation recommendations within frozen methodology

Adopt the independent checks on a future review-controlled CI path, explicitly trigger PRs targeting V5, tighten artifact provenance and test missing/extreme live-input behavior if a production data interface is added. These do not authorize replacing the governed credit models.
