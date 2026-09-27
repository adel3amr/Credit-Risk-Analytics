# Observable economic LGD remediation — S2 decision

**Architecture implemented; candidate NOT PROMOTED. Bank-use gate BLOCKED.**
Full regression suite: **136 passed, 0 failed**, one existing TestClient
deprecation warning. Original 125 tests retained and 11 targeted checks added.
Baseline release 281f114; protocol frozen ffe25da; candidate/data locked 4a84ae5
before final opening. One existing-specification GB candidate, no tournament,
post-final tuning, blanket adjustment, or change to V5/S1 source or results.

## What changed and what the comparison means

S1 linked hidden state directly to recoveries, without a corresponding observable
history. S2 replaces this missing link with dated sector activity, labour-market,
collateral-price and liquidity histories. The same inputs are available at training
and scoring; hidden regime and future outcomes are excluded. Effective interest
rate is joined from the existing borrower source, not replaced by policy rate.

This is a new DGP and new hypothetical workout release, reusing S1 facility
characteristics. It cannot retrospectively solve S1 or make the S1 -12.65 pp and
S2 -0.26 pp a like-for-like comparison. The proper comparison is incumbent and
corrected predictions on the SAME S2 cases below. S1's oracle +0.55 pp remains
historical diagnostic evidence; no S1 oracle feature entered S2 scoring.

## Locked quantitative results (percentage points)

| Population | Incumbent conditional bias | Corrected conditional bias | Incumbent RMSE | Corrected RMSE |
|---|---:|---:|---:|---:|
| Selection, 3,000 | -2.84 | +0.28 | 18.51 | 16.92 |
| Final, 3,000 | -4.72 | +0.52 | 18.62 | 16.47 |
| Current, 8,695 | -6.33 | -0.26 | 19.32 | 16.86 |
| Current normal, 2,305 | +1.81 | -0.42 | 18.27 | 17.16 |
| Current downturn, 6,390 | -9.27 | -0.20 | 19.68 | 16.75 |

Current realized MAE: 15.86 → 12.74 pp. Realized bias: -6.29 → -0.22 pp.
Mean predicted LGD: 45.61% → 51.68%; realized mean 51.90%; simulator conditional
mean 51.94%. Conditional integration uses 512 draws per facility, separate from
development-outcome draws. It is simulator-based validation, not empirical bank
validation. Macro-cluster standard error for corrected current bias is 0.235 pp;
seven current sector clusters give limited economic-regime evidence. All realized
tail diagnostics, predicted bands and requested segment metrics are retained in
`results/*_metrics.csv`; they did not determine fitting or data changes.

## Recovery mechanisms

- Collateral proceeds respond to price changes and liquidity, with zero direct
  market-price sensitivity for cash, full property sensitivity and lower other-
  asset sensitivity. Existing coverage and lien effects remain.
- Guarantees respond to activity and liquidity; existing guarantee amount and
  latent guarantor heterogeneity remain.
- Unsecured collections and cure probabilities respond to activity/labour stress.
- Recovery times and costs respond to liquidity/labour stress. Six dated net
  cashflow buckets produce discounted economic LGD, bounded 0–100% as before.

No `if downturn: LGD += X`. Latent regime only generates correlated observables;
it is never read by the recovery function or model. Unobserved security/guarantor
quality remains simulation heterogeneity, not a newly claimed operational field.
The candidate is the incumbent 220-tree, depth-3, learning-rate .035 specification
with the four observables and effective interest rate appended. No calibration
overlay or MoC has been fitted; there is no evidence-based magnitude approved.

## Scenario and ECL integration

Existing upside/baseline/downside names, weights (20/60/20), PDs, facility EADs,
stages, watchlist and EWS outputs are retained. S2's price/liquidity translations
from GDP/unemployment deltas are explicit synthetic assumptions in economics.py.
They are not estimated bank elasticities. Scenario assumptions are static shocks,
not full forecast recovery paths.

| Scenario | Mean predicted LGD | Conditional mean | Conditional bias |
|---|---:|---:|---:|
| Upside | 49.65% | 49.33% | +0.32 pp |
| Baseline | 51.68% | 51.96% | -0.27 pp |
| Downside | 55.97% | 58.29% | -2.32 pp |

Baseline's separate scenario MC stream explains the slight difference from -0.26
pp in the main current evaluation. Aggregate ordering is sensible. However 78
facilities reverse an adjacent ordering (31 cash, 7 mortgage, 11 other, 29
unsecured), maximum reversal 0.9342 pp. No economic justification established;
no post-hoc sorting or uplift conceals it.

Shadow ECL bridge (synthetic monetary units):

| Calculation | Portfolio ECL |
|---|---:|
| Unchanged incumbent production path | 78,746,507.57 |
| Incumbent LGD with within-scenario lifetime PD ordering | 78,701,888.37 |
| S2 scenario LGD with within-scenario lifetime PD ordering | 90,181,093.71 |

Ordering effect: -44,619.20. LGD effect on consistent scenario arithmetic:
+11,479,205.34. Total shadow movement: +11,434,586.14. Higher conditional losses
in the S2 economic environment explain the direction; this is not a booked
correction to original S1. Maximum independent facility arithmetic difference is
2.33e-10 monetary units (floating-point tolerance), facility→borrower→portfolio
aggregation difference 0.00. No claim of literal bitwise arithmetic equality.

The Stage 2 ordering change is explicitly a versioned METHODOLOGY / IMPLEMENTATION
correction for this shadow engine, not silently patched into historical V5.

## Promotion decision and exact remaining deficiencies

1. Downside support: 28.95% of exposures' activity inputs and 10.21% of unemployment
   inputs fall outside observed development ranges. Downside bias is -2.32 pp.
2. 78 unexplained facility scenario reversals require a justified shape-controlled
   estimator or predeclared monotone calibration evaluated on NEW validation data.
   Current final data must not be reused to tune and claim untouched validation.
3. Final full-guarantee segment bias +4.65 pp (135 facilities), versus +1.37 pp on
   current full-guarantee facilities, leaves a material segment-stability concern.
4. Only seven independent current macro-sector clusters; temporal robustness is
   not proved by thousands of facilities sharing those conditions.

These fail the mandate's scenario/segment/support promotion requirements despite
excellent aggregate current improvement. No active model promotion; the original
finding remains open, and this successor evidence is linked rather than substituted.
No additional broad experiments were started.

## Reference and institutional limitations

These are synthetic conditional-on-default workouts for sampled facilities,
including facilities that did not actually default in S1. They are not a new
empirically observed bank default population. Reused attributes are hypothetical
at S2 dates, not reconstructed historical bank information. Future residual draws
are independent across facilities conditional on macro/attributes; this simplifies
within-borrower residual dependence. Price/liquidity indices are model assumptions,
not a connected economic feed. Measurement/revision error and future macro paths
are not fully modelled. A current bank must map and validate actual source fields,
publication vintages, data rights and economic support before any deployment.

Separately, existing identity/perimeter/security qualification, PostgreSQL/container
runtime, operational deployment, accounting policy approval and institution outcome
validation remain unverified. A synthetic-model improvement cannot pass those gates.

## Reproduction

Use Python 3.12 and requirements-platform-lock.txt. Frozen data and candidate are
included. `python -m economic_lgd.review` recalculates result summaries and support
without retraining. `pytest -q tests/platform/test_economic_lgd.py` verifies the
contract, leakage exclusions, cashflow identity, scenario arithmetic and locks.
Generation/develop/final commands intentionally refuse overwrite. To reproduce the
full run, copy the module into a separate clean checkout without its S2 `data/`
and `results/` directories, then execute `python -m economic_lgd.generate`,
`python -m economic_lgd.evaluate develop`, and `python -m economic_lgd.evaluate final`.
Never remove or replace frozen evidence in the working release to rerun it.

Results, registry and feature contracts: `results/decision.json`,
`results/registry.json`, `FEATURE_CONTRACTS.json`. UI: Economic LGD validation.
Copilot model-risk question: "Explain S2 observable economic LGD and promotion".
