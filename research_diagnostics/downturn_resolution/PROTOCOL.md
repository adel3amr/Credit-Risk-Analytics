# Current/downturn LGD resolution protocol

Baseline 4a9599f; actual baseline tests 111 (mandate's 107 is superseded).
No source data regeneration. No active risk methodology/model replacement.
Reuse all S1 conditional expectations and candidate artifacts. Final/current have
already been inspected; no claim of fresh independent promotion validation.

## Three targeted families, no search

1. Proxy-informed prediction: one fixed gradient-boosting classifier of the synthetic
   downturn state using incumbent canonical LGD features; test a companion without
   industry to expose a vintage-specific sector shortcut. Fit development borrower-
   clustered facilities only. Also test whether existing captured quality fields
   improve identification; those require institution capture, not production available.
   Evaluate on selection/final/current separately, report state discrimination,
   calibration, prevalence and LGD impact. No current labels used for fitting.
2. Transparent regime calibration: on development realized workouts, fit a bounded
   logistic-mean regression using logit(governed LGD), regime and collateral-category
   interactions with regime. Coefficients are fitted by fractional Bernoulli log loss,
   L2 penalized slopes (fixed penalty 1); no fitting to conditional means or current
   population. Compare true-state oracle, proxy-mixture forecast, and all-normal/
   all-downturn declared scenarios. State oracle remains non-deployable. Reuse
   existing enhanced and R2 two-stage models as comparisons, no retraining those.
3. Control: implement a separate, explicitly declared scenario overlay from the
   development-fitted calibration; preserve base LGD/ECL. Report incremental
   nonnegative risk sensitivity, not automatic expected loss or a booked allowance.
   Without validated state information or probability weights, expected-loss use
   must be blocked. A scenario reserve is not an unbiased LGD prediction.

## Mechanism decomposition

Use an independent copy of S1 conditional recovery integration with switches for
six direct D effects: collateral proceeds, guarantee proceeds, unsecured collection,
cure probability, timing, costs. All-on/off parity against previous integration is
required. Compute sequential paired contributions in the listed fixed order, using
identical random draws, all non-D quality inputs fixed. Sum equals total direct
D effect; order-dependent attribution, not a real-bank causal claim. Separately
quantify known quality reductions (.10 security, .12 guarantor) with shared uniforms
on nonclipped cases; clipping limits prevent exact latent-quality reconstruction,
so report a bounded-restoration sensitivity, not exact attribution.

## Acceptance and limitations

Report actual/current conditional bias, normal/downturn and ex-ante segments, MAE,
RMSE, current ECL and stage/segment breakdowns. Preserve all adverse results.
Do not call forced population mean matching a correction. No current truth used for
calibration or scenario probability. No selected threshold changes for promotion.
Lack of untouched evaluation and institutional feature capture remain distinct gates.
A control can be implemented without claiming the original point-prediction issue
solved. Final YES requires deployability and conditional calibration evidence;
otherwise NO with the selected control/restriction and quantified reason.

External context: IFRS9 expected loss is unbiased/probability-weighted using reasonable
supportable information. Prudential EBA margin-of-conservatism guidance is not an
IFRS9 mandate to substitute a stressed quantile or arbitrary reserve. No empirical
coefficient or regulatory requirement is imported into the frozen engine.

Mechanism sensitivity uses 1,024 draws per facility, fixed seed 2026092502, shared
random numbers across switches; marginal expectation comparisons continue to use
previous 4,096-draw estimates. This draw budget is fixed before mechanism results.
Proxy classifiers use 100 gradient-boosting trees, depth 2, learning rate .05,
min_samples_leaf 25, seed 42, fitted to the same development workouts as LGD.
No tuning or model selection against final/current state labels.
