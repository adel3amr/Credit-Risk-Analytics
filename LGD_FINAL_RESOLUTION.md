# Final LGD resolution decision

25 September 2026. Baseline: `3539e36`; branch `platform/production-foundation`.

## Required final category: **3 — MODEL DEFECT REMAINS**

The specific observed defect is **conditional calibration under S1 population
transfer**, not an arithmetic bug and not evidence that every severe realization
should be predictable. No tested deployable challenger satisfies promotion criteria.
The governed reference LGD is retained, not approved for institutional use.

The original headline mixed two different problems. Selecting realized losses above
75% creates a large negative residual even for the simulator's conditional mean.
On S1 final, that effect is -14.5908 pp. The actual governed model is **2.4830 pp
above** the conditional mean inside that selected group, giving total -12.1078 pp.
Thus the severe-realized statistic itself does not demonstrate expected-loss
underprediction in that group. Earlier wording treating a worse tail statistic
as sufficient proof that enhanced LGD is economically worse is superseded.

A separate, genuine issue exists on current S1: governed LGD averages 45.61% versus
58.26% conditional expectation, a **-12.65 pp** mean deficit. In the ex-ante
conditional-mean >75% region it is -10.92 pp (1,284 facilities, 840 borrowers).
This cannot be dismissed as conditioning on realized outcomes: current outcomes
were never used, and the grouping uses independently integrated expectations.

## Before/after evidence—no governed model changed

All final metrics use the same 1,017 defaulted facilities, 593 borrowers. Severe
realized >75% has 168 facilities, 118 borrowers. Current comprises 8,695 facilities,
5,000 borrowers; no actual future outcomes exist. ECL is a shadow comparison holding
PD, stage and EAD fixed; units are synthetic currency, not institutional allowances.

| Model | Final MAE pp | Final RMSE pp | Final bias pp | Final >75% bias pp | Final conditional bias pp | Current conditional bias pp | Current conditional >75% bias pp | Current ECL, million |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Governed V5 (8,000 fit) | 13.05 | 18.10 | 0.03 | -12.11 | -0.27 | -12.65 | -10.92 | 78.75 |
| Frozen V5 benchmark (6,000 fit) | 12.81 | 18.13 | 1.64 | -10.42 | 1.35 | -10.82 | -9.22 | 81.24 |
| S1 unchanged-spec refit | 14.76 | 19.72 | 5.20 | -14.48 | 4.90 | -6.89 | -12.20 | 88.93 |
| Existing S1 enhanced GB | 12.39 | 17.08 | 1.48 | -15.31 | 1.18 | -1.25 | -4.55 | 98.18 |
| Targeted context/rate GB | 12.35 | 16.97 | 1.48 | -14.91 | 1.18 | -1.62 | -4.91 | 98.29 |

The targeted row is a retrospective research test, not a new untouched holdout.
The previously reported 18.13 pp RMSE belongs to the 6,000-case benchmark. The actual
platform uses the 8,000-case fit (18.10 pp on S1 final). Both are retained explicitly.
No model artifact, PD, EAD, staging, SICR or production ECL policy was replaced.

## Exact final-tail decomposition

Bias convention: prediction minus outcome. Total = model-minus-conditional plus
conditional-minus-realized. All figures below are percentage points.

| Model | Total severe bias pp | Model minus conditional pp | Conditional minus realized pp |
|---|---:|---:|---:|
| Governed V5 (8,000 fit) | -12.1078 | 2.4830 | -14.5908 |
| Frozen V5 benchmark (6,000 fit) | -10.4177 | 4.1731 | -14.5908 |
| S1 unchanged-spec refit | -14.4751 | 0.1157 | -14.5908 |
| Existing S1 enhanced GB | -15.3103 | -0.7195 | -14.5908 |
| Targeted context/rate GB | -14.9138 | -0.3230 | -14.5908 |

The identity holds within 1e-12 in every nonempty reported cohort. Full results
also retain >60%, >90%, low-loss cases, fixed predicted/conditional bands, collateral
coverage, guarantee support, product, security, lien, industry and EAD bands.
The conditional mean is an estimate under the S1 DGP using all legitimate synthetic
inputs, not empirical bank truth, and not the incumbent's smaller information set.
Consequently model-to-mean differences combine omitted information, approximation
and population transfer; they cannot all be called coding defects.

## Root cause and supported conclusions

**Validation design/stochastic realization:** retrospective selection explains most
of the negative severe-realized residual, including the existing enhanced model's
-15.31 pp total: only -0.72 pp is model-minus-full-information conditional mean in
that cohort. This resolves the interpretation of that headline, not every model issue.

**Population transfer/model inputs:** known downturn context appears in 82.38% of
current facilities, but only 8.65% of final and 33.78% of development workouts.
The incumbent has no context input. Its ordinary-context current bias is +1.05 pp;
downturn-context bias is -15.59 pp. Changing only context to zero in a paired
simulation reduces conditional mean from 58.26% to 45.39%, while the governed mean
stays 45.61%. The 12.87 pp simulated context effect accounts for most of the current
average shortfall. This is a conditional simulator contrast, not a real-bank causal
estimate. The source cohorts were not altered or regenerated.

**Feature/support limitations:** quality/context exists in S1 source records but is
not in the frozen incumbent feature contract. A real institution still needs
validated capture. Each S1 industry has one regime per vintage, creating unseen
industry/context combinations across cohorts. The known borrower discount rate
also enters the DGP but is omitted from both original model feature lists.

**Targeted test:** one fixed-GB candidate removed the industry proxy and added the
known discount rate. It was fitted on development only; no tail weighting, uplift,
parameter search or final calibration. It modestly reduced final conditional RMSE
but did not improve current conditional calibration over the existing enhanced GB.
Current high-conditional-LGD bias remained -4.91 pp, versus -4.55 pp for existing
enhanced GB. The hypothesis did not yield a promotion-ready correction. No more
variants were tuned against the already-viewed final population.

**No demonstrated implementation cause:** independent S1 recovery equations replay
the original generator's controlled outcomes within 1e-14. Approved clipping and
predictor validation remain intact. The earlier NaN/Inf/cardinality fixes remain
valid, but do not explain these conditional differences.

## Irreducible variation and uncertainty

With all legitimate S1 inputs known, simulated conditional variance implies a
full-information minimum expected RMSE of **15.98 pp** over final inputs and
**16.35 pp** over current inputs. These are marginal squared-error lower bounds
under this DGP, not guaranteed realized sample RMSEs or a bound for a bank.

On current inputs the governed model has 15.35 pp RMSE against the conditional
mean, giving 22.43 pp model-implied expected outcome RMSE; existing enhanced GB has
5.73 pp RMSE against the mean and 17.33 pp expected outcome RMSE. Substantial
stochastic error is unavoidable, but substantial incumbent approximation/transfer
error also remains. Future cure, recovery shocks and realized costs were prohibited
as prediction inputs. No future oracle was promoted.

4,096 independent draws per facility estimate marginal means/variances. Original
outcomes share borrower shocks, so reported bias confidence intervals use borrower
clusters. Examples: current governed all-population conditional bias 95% interval
[-12.90,-12.41] pp; final governed conditional >75% group [-5.84,+0.60] pp (54
facilities/38 borrowers). The latter does not establish a precise tail deficit.
Intervals are approximate, conditional on these cohorts/sector regimes, unadjusted
for multiple comparisons, and do not establish cross-regime bank generalization.
Small groups are flagged; no statistical threshold was relaxed to obtain approval.
Independent Monte Carlo draws do not estimate joint portfolio extreme-loss risk.

## Downstream ECL and governance

Current governed ECL remains **78.7465 million**. Using simulator conditional mean
as a diagnostic only gives **100.0760 million**, a 21.3295 million difference.
This is neither an approved uplift nor a recommended booked allowance. Existing
enhanced shadow gives 98.1821 million and the targeted shadow 98.2896 million.
PD, stage, maturity and EAD are identical across these comparisons. Facility ECL
and borrower/portfolio summations reconcile; original governed output is unchanged.

**Governed LGD retained as REFERENCE. No challenger promoted.** Existing enhanced
GB is economically better on conditional accuracy than its worse realized-tail bias
suggested, but retains conditional errors, operational capture limitations and no
fresh independent promotion test. Removing the incumbent shortfall properly would
require a governed context-aware model with validated prediction-time capture and
new independent evaluation. The present mandate does not justify bypassing those
requirements or silently installing synthetic expected values as a risk engine.

## Tests, evidence and broader readiness

111 tests pass: all 107 previous tests plus four targeted tests for independent
DGP replay, future-information exclusion/reproducibility, decomposition/ex-ante
group invariance, and nonfinite rejection. Existing risk/run/authorization/ECL
regressions are preserved. No frozen source, S1 input data or historical model
artifact was changed. Full evidence is in `research_diagnostics/s1_resolution/`.
A manifest-only missing import was corrected after simulation; outputs were not
rerun or tuned. That recovery is disclosed in the diagnostic manifest.

Institutional gates remain separate and BLOCKED: empirical calibration, operational
feature capture, population suitability, PostgreSQL/container execution, hosted CI,
real-browser qualification and institution security controls. No institutional
approval is implied by resolving the interpretation of severe-realized bias.

## Reproduction

Install the repository's pinned requirements; ensure original reference artifacts
exist (`python -m credit_platform.cli build-models`). New diagnostics are additive:

```bash
python -m pytest -q
python -m research_diagnostics.s1_resolution.analyze
python -m research_diagnostics.s1_resolution.followup
```

Scripts refuse overwriting their existing evidence. To reproduce, use a disposable
checkout and first preserve/move only the diagnostic results directory, then run
these commands. Do not remove the frozen S1 data or its original evaluation locks.
The follow-up trains only the single documented candidate. Original S1 final results
remain an already-examined retrospective population throughout.

## Repository change record

- `research_diagnostics/s1_resolution/BASELINE_AND_PROTOCOL.md`: reconstructed
  DONE/STILL VALID/SUPERSEDED/UNRESOLVED inventory and predeclared diagnostic.
- `conditional.py`: independent S1 expected-loss integration.
- `analyze.py`: fixed-model cohort decomposition, uncertainty and ex-ante groups.
- `TARGETED_FOLLOWUP.md`, `followup.py`: narrowly justified candidate, context
  sensitivity and facility-level shadow ECL reconciliation.
- `results/`: facility expectations, grouped metrics, calibration slopes, source/
  artifact manifests, candidate, context support, counterfactual, ECL shadows,
  historical integrity and test evidence.
- `tests/platform/test_s1_resolution.py`: four new targeted tests; no prior test removed.
- Root README, limitations, model inventory, findings, changelog, independent
  validation and production-readiness reports updated with the explicit disposition.

These changes are additive to baseline 3539e36. The final commit containing this
report records the complete file list; no external GitHub push has been performed.
