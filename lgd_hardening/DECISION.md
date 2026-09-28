# Post-R1 hardening disposition — 28 September 2026

**PREFLIGHT BLOCKED. No new final holdout generated or opened. No promotion.**
The retained best candidate remains `s2-r1-monotone-gb-1`. Its numerical results
are unchanged. The additional continuous-calibration candidate was rejected.
This is not a claim that all possible statistical models are incapable of better
metrics. It is a finding that the available evidence does not support the required
recovery-information contract or closure of the remaining model/domain failures.

## Authoritative history and baseline

The checked-out branch is `platform/production-foundation`; starting commit is
`14b8c4db691c8f795c27501b7237442426eb70b2`. V5 (`0dfe4c8`), the independent
review, research tail programme, S1 and downturn decisions, original S2
(`ef5a1c5`), and R1 freeze (`e8e9228`) remain preserved. No old branch, target,
workout, prediction or adverse decision was rewritten. The new protocol was
committed as `fe2f245` before the calibration assessment.

Source/data/model hashes were verified and the baseline **151 tests passed again**
in the pinned environment. The previous severe-realization selection explanation,
oracle exclusion, rejected blanket downturn uplift and independent ECL arithmetic
remain applicable. No previous challenger sweep, two-stage/oracle fitting or
seed search was repeated.

| Retained R1 check | Evidence | Disposition |
|---|---|---|
| Current baseline conditional bias | +0.10 pp; bound 0.77 pp | PASS |
| Current downside conditional bias | −0.47 pp; bound 1.15 pp | FAIL frozen 1 pp equivalence |
| Scenario reversals | 0 | PASS |
| Retired holdout full-guarantee bias | +1.35 pp; bound 2.06 pp | FAIL frozen 2 pp equivalence |
| Current support | 0 exceptions in all scenarios | PASS for known current inputs |
| Retired holdout downside support | 327/6,000 exceptions | FAIL release domain |
| Prediction 80–100% band | Current baseline +3.62 pp; retired holdout +2.63 pp | FAIL; bias itself exceeds 2 pp |

All previous final populations are **known engineering evidence** now. Their
historical untouched status is preserved as history, not claimed for this work.

## What the additional diagnosis established

### 1. Unavailable information remains in the recovery target

S1 generated security quality with a −0.10 shift and guarantor strength with a
−0.12 shift under its original latent sector state. S2/R1 dropped the direct
state feature and attached new economic histories, but copied these quality
values exactly. Their state dependence did not disappear.

The audit reconciles the quality columns to source records exactly. In the
current population 7,163/8,695 facilities retain the original adverse S1 state;
in the retired R1 promotion population only 425/6,000 do. These are **not** the
new S2 economic regime labels. The source linkage matters for explaining why
additional macro observations alone cannot certify recovery-quality stability.

A paired diagnostic on 256 **development-only** fully guaranteed facilities,
holding all scoring inputs fixed and applying the existing source-sized quality
shifts, changes mean conditional LGD by **2.62 pp** using common random numbers
and 2,048 recovery draws. This is a sensitivity, not an exact causal allocation
of the current bias, not a deployable oracle and not a real-bank estimate.

Unobserved heterogeneity is not automatically a fatal model flaw. The blocker
here is the unvalidated change in its population distribution and absent
prediction-time evidence needed to support the requested guarantee/security
mechanics and stable transfer claims. It would be unjustified to expose simulator
quality as observed data, remove its adverse effect to improve metrics, or assert
that a new synthetic marginal distribution represents the missing information.

### 2. Precision does not fix the high-band mean error

`precision_planning.csv` separates point bias from uncertainty. Holding the
estimated cluster variance and mean bias constant, current aggregate downside
would require approximately **12 independent economic clusters**, versus seven,
to reach the 1 pp bound. This is illustrative planning, not a validated sample-
size prescription: stationarity across quality populations is unproven.
Replicating facilities, quarters or simulator draws is not equivalent evidence.

The high predicted band already exceeds the 2 pp tolerance before uncertainty.
No increase in sample size alone can make a persistent +3.62 pp error satisfy a
2 pp bound. Every existing band is audited for prediction, realization,
conditional mean, realization noise, size, economic clusters, support,
collateral, guarantee, product, industry and regime composition. No severe-
realization cohort was optimized.

### 3. One justified calibration correction was tested and rejected

The new candidate `s2-r1-continuous-calibration-1` uses only matured R1 calibration
realized outcomes: 6,000 rows, 20 equal-count bins, weighted isotonic pooling and
continuous interpolation. It never fits current/retired-promotion outcomes,
conditional expectations or hidden information. Its knots and fit-source hash
are saved. Monotonic scenario order remains intact.

It damages important existing strengths:

| Known engineering metric | R1 | Calibration trial |
|---|---:|---:|
| Current baseline conditional bias | +0.10 pp | −0.41 pp |
| Current downside conditional bias | −0.47 pp | −1.59 pp |
| Retired holdout full-guarantee baseline bias | +1.35 pp | +1.49 pp |
| Original current high-band downside bias | +2.48 pp | −4.58 pp |
| Retired holdout baseline MAE | 12.27 pp | 12.46 pp |
| Retired holdout baseline RMSE | 16.40 pp | 16.42 pp |

Flat extension beyond the learned calibration knots contracts the upper scores.
Reporting only new bands could make the former highest band disappear, so both
the original and recalibrated populations are retained. This correction is
rejected, not tuned repeatedly. It is evidence against this scalar calibration,
not proof that every legitimate calibration is impossible.

### 4. A mechanical economic range is not validated model support

`ECONOMIC_DOMAIN_CONTRACT.json` explicitly separates the original S2 mechanical
bounds, its scenario mapping, and empirical/local model support. Bounds and
deltas were not selected around the 327 failures. The boundary checks every
scenario and never silently truncates the requested shock.

Engineering tests cover the known calibration, retired promotion and current
populations. Current scenarios retain zero exceptions. Retired downside still
rejects 327/6,000; baseline rejects 35. Under the new explicit, non-clipping
boundary, retired upside rejects 1,060: 979 outside the mechanical domain and 81
outside model support. Calibration upside has 1,182 mechanical-domain exceptions.
These extra flags concern historical boundary saturation, not a changed R1 score.
The original scenario artifacts remain unchanged and comparable.

OOD output has **no expected LGD**. Its [0,1] interval is a clearly labelled
non-bookable sensitivity bound, never an approved estimate or ECL replacement.
This closes uncontrolled-output risk at the new boundary; it does **not** close
the model's domain-coverage finding. No training ranges were widened or rejected
holdout rows copied into development.

## Implemented controls and traceability

* `capture.py`: dated source, facility/provider/asset identities, nominal/eligible
  amount, currency, legal evidence, valuation/financial evidence and expiry;
  rejects future records, hidden simulator columns, unsupported eligibility and
  absent validated derivations. No actual capture observations or quality mapping
  were invented. The capture requirement remains unmet.
* `release.py` and the new controlled `runtime.py`: a promotion status string
  alone cannot waive decision-hash, model-identity and all-eight-gate checks.
  Historical research entry points are frozen; use the new controlled boundary.
* `facility_traces.json`: representative facilities with available feature/source
  hashes, scenario LGDs, model version, ECL and supported protection-input
  sensitivities. These are model responses, not causal component allocations or
  an invented decomposition of an opaque prediction into actual recoveries.
* API/Copilot evidence identifies this preflight disposition, the retained R1
  model and the rejected calibration. It does not describe known engineering
  data as a new independent final validation.

## ECL and preserved risk components

No PD, EAD, SICR, staging, watchlist or EWS method changed. No model was promoted,
so the existing bridge remains: governed **78,746,507.57**, original S2 shadow
**90,181,093.71**, R1 shadow **92,036,058.42** currency units. There is no new
booked movement. Original R1 maximum independent facility arithmetic discrepancy
is 1.7463e−10; borrower/portfolio difference is zero. Existing regression tests
recheck these results. A rejected calibration was not propagated as a release.

Retained R1 retired-holdout MAE/RMSE/realized bias remain **12.27/16.40/+0.29 pp**;
conditional bias **+0.24 pp**, normal/downturn **−0.03/+0.62 pp**. These are old
verified results, not a new model's independent performance claim.

## Stop condition and remaining work

The genuine operational blocker is absent validated prediction-time recovery
information (or evidence justifying stable marginalization of that heterogeneity)
under the observed population changes. The contracts needed to obtain it now
exist; the source observations and validated derivation do not. Statistical
approximation may still improve, but it cannot be asserted to supply that missing
evidence. Inventing it, using future/simulator truth, or changing the DGP merely
to erase the population shift would violate the mandate.

Support extension, regime-sensitive calibration and stronger validation sampling
remain possible future implementation work once that information/assumption is
properly governed. They are not declared impossible or falsely marked closed.
No final promotion sample was consumed while these preflight failures remained.
Consequently final independent promotion validation is **not run**, approval is
**not achieved**, and all failed R1 model gates remain failed. Bank use stays
blocked by these and the previously documented institutional/operational gates.

## External evidence and scope

Primary sources reviewed 28 September 2026:

* BIS general credit risk management (CRI10),
  https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/cri/10:
  guarantor credit quality/legal capacity and continuing collateral valuation/
  enforceability motivate the capture fields; no model coefficients imported.
* Basel CRE22 operational guarantee requirements,
  https://www.bis.org/committees/bcbs/basel-framework/standard/cre/22/inforce/2023-01-01/published/2020-11-26:
  documentary coverage and enforceability context only. Prudential CRM rules
  were not substituted for IFRS 9 or project methodology.
* Scikit-learn 1.8 IsotonicRegression documentation,
  https://scikit-learn.org/1.8/modules/generated/sklearn.isotonic.IsotonicRegression.html:
  interpolation/monotonic implementation only; not credit-risk approval.
