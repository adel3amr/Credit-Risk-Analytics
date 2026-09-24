# LGD remediation and corrected root-cause assessment

24 September 2026. Classification: BUG FIX, VALIDATION, RESEARCH, DOCUMENTATION.
Frozen V5, all R2 data, generators and research model artifacts remain unchanged.
**Bank-use gate remains BLOCKED. No model has been promoted.**

## Implemented corrections

The platform adapter previously called the historical clipping function before
checking its outputs. Positive/negative infinity could become a plausible 100%/0%
LGD; a short output array could silently truncate the facility loop. The adapter
now requires exactly one finite scalar prediction per facility **before** applying
the approved finite clipping rule. Invalid output fails the run without decisions.
This fixes real execution defects; neither was demonstrated to cause the measured
historical severe-loss bias. We do not claim they improve historical metrics.

## New evidence: expected loss versus retrospective severe outcomes

The original research tested future-information oracles but did not integrate over
future outcomes while keeping prediction-time features fixed. The protocol in
`research_diagnostics/lgd_conditional/PROTOCOL.md` specifies that missing experiment.
For every one of the 3,000 existing R2 final cases, 4,096 independent outcome draws
were generated from unchanged R2 equations, using only its 13 feature columns.
The original realization was never an input. This is retrospective diagnosis on
an already-viewed holdout, not a fresh selection or promotion test.

| Predictor | Whole-population RMSE (pp) | Whole-population bias (pp) | Realized >75% bias (pp), n=536 |
|---|---:|---:|---:|
| Frozen V5 | 17.6503 | -0.8203 | -12.7421 |
| Existing two-stage challenger | 15.6923 | +0.2188 | -12.0482 |
| Simulator conditional mean | 15.4013 | -0.1035 | -12.5017 |

The conditional mean's severe-cohort Monte Carlo standard error is 0.0135 pp.
This measures simulation precision only, **not** sampling uncertainty, real-bank
uncertainty or validity of the generator. The complete scorecard also includes
>60%, >90%, low loss and all five predeclared prediction bands, with denominators.

The mean-error identity is:

`prediction - realization = (prediction - conditional mean) + (conditional mean - realization)`.

For V5 in the >75% realized cohort it gives **-12.7421 = -0.2405 -12.5017 pp**.
For >90%, n=100, it gives **-16.6636 = -2.7737 -13.8899 pp**. The nonzero residual
at >90% is retained; the result does not establish that V5 is an ideal predictor.
These are group averages that can conceal cancellation, not a universal fraction
of irreducible error or a causal attribution for bank data.

Even a simulator-informed expected loss underpredicts the subgroup selected
*afterward* for severe realized outcomes. Raising every expected loss until that
retrospective subgroup has zero error changes the target and can overstate other
losses. The existing p90 experiment's aggregate overprediction remains adverse
evidence; it is not an expected-LGD replacement.

## Material issues that remain

Prediction-time calibration is still imperfect. On this population, V5's fixed
forecast bands 0–20%, 20–40%, 40–60%, 60–80%, 80–100% have biases of approximately
-5.99, -2.86, -3.00, +3.24, +9.49 pp respectively. This is not explained away by
the severe-outcome selection diagnostic. No calibration was fitted on this holdout.

The conditional-mean diagnostic knows the synthetic process and uses R2 quality
and downturn inputs absent from live data. It is **not deployable**. The incumbent
still has almost no zero-guarantee development support, while that state dominates
live facilities. Synthetic evidence cannot supply missing institutional records.
No new data were fabricated to close these gaps.

An honest closure therefore separates:

- Execution defects: corrected and regression-tested.
- Reason for much of the retrospective severe-cohort gap in R2: demonstrated by
  conditional simulation; prior blanket interpretation as tree underprediction
  is incomplete and is superseded by this evidence.
- Prediction-time calibration, feature availability and live support: unresolved;
  need genuine captured inputs and independently validated representative data.
- Production approval: blocked. No threshold or gate has been weakened.

## Verification and reproduction

`python -m pytest -q` — 104 tests passed after this change.

`python -m research_diagnostics.lgd_conditional.diagnostic` reproduces the diagnostic.

The independently transcribed outcome equations reproduce the original generator's
1,000 held-input outcomes within 1e-14 from its captured pre-outcome RNG state.
Tests poison all future columns and demonstrate identical predictions. Nine unit/
diagnostic cases and two API/database failure cases cover the additions. The run
manifest records source, input and prediction hashes; historical hash checks pass.
The experiment has no import path into production scoring.

External context: Gneiting, *Making and Evaluating Point Forecasts*,
https://arxiv.org/abs/0912.0902. Mean and quantile targets require appropriate scoring.
This is statistical context, not bank certification or imported recovery assumptions.
