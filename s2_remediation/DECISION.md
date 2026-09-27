# S2-R1 final promotion decision — 27 September 2026

**NOT PROMOTED. Bank-use gate BLOCKED.** The focused remediation materially
improves S2, eliminates its scenario reversals, and supports every defined current
scenario. It does not satisfy all predeclared promotion tests. No thresholds were
relaxed, no final-sample tuning occurred, and no model or ECL result was booked.

## Four blockers and preserved current calibration

All LGD figures below are percentage points. The original +4.65 guarantee result
was on the historical S2 final sample; the new final sample is different. The
same-population comparison immediately below avoids attributing sampling changes
to model improvement.

| Check | Historical S2 | Remediated evidence | Decision |
|---|---:|---|---|
| Current baseline conditional bias | −0.26 | +0.10; approximate 95% interval [−0.56, +0.77] | PASS |
| Current downside conditional bias | −2.32 | −0.47; interval [−1.15, +0.21] | FAIL: equivalence bound 1.15 > frozen 1.00 |
| Scenario reversals | 78; maximum 0.9342 | 0; maximum 0, on current and fresh promotion populations | PASS |
| Full guarantee conditional bias | +4.65; historical n=135 | +1.35; fresh n=233, interval [+0.63, +2.06] | FAIL: bound 2.06 > frozen 2.00 |
| Downside support | Current GDP/unemployment outside original development | Current: 0/8,695 rejected. Fresh promotion: 327/6,000 rejected | FAIL for proposed release domain; rejection control works |

Current upside also fails the equivalence test: point bias −0.36, bound 1.17 pp.
Current partially guaranteed downside exposures have bias −1.79, bound 2.90 pp.
These are not erased by the improved aggregate results.

## Same-population model comparison

Fresh promotion baseline: 6,000 facilities, 5,194 borrowers, new outcomes and
economic vintages; none of these borrowers appeared in the inspected S2 final
sample. Realized bias means prediction minus the single realized workout;
conditional bias means prediction minus an independently simulated conditional mean.

| Model | MAE | RMSE | Realized bias | Conditional bias | Full-guarantee conditional bias |
|---|---:|---:|---:|---:|---:|
| Governed V5 | 14.42 | 18.52 | −2.68 | −2.73 | +1.48 |
| Original S2 | 12.66 | 16.58 | +0.38 | +0.33 | +3.80 |
| S2-R1 | 12.27 | 16.40 | +0.29 | +0.24 | +1.35 |

For S2-R1, fresh baseline normal/downturn conditional biases are −0.03/+0.62 pp.
Known-current baseline normal/downturn biases are −0.43/+0.29 pp. The latter
point estimates look small, but their uncertainty bounds are 1.34/1.08 pp and
fail the frozen 1 pp regime criterion. Fresh upside downturn bound is 1.0100 pp:
it fails, rather than being rounded into a pass.

Current baseline MAE/RMSE/realized bias are 12.47/16.85/+0.16 pp. Fresh promotion
upside/baseline/downside conditional biases are +0.27/+0.24/+0.25 pp. Current
counterparts are −0.36/+0.10/−0.47 pp. The original current transfer failure has
not reappeared in the aggregate, but segment stability is insufficient.

All products, industries, collateral/lien/coverage/exposure groups, prediction
bands and realized tails are retained in `results/*_metrics.csv`. Twenty-nine
individual acceptance checks fail, grouped into four failed gates below; see
`gate_checks.json` for exact bounds and populations. In particular, the predicted
80–100% band overpredicts fresh baseline conditional LGD by +2.63 pp (n=186,
bound 2.97), and current baseline by +3.62 pp (n=297, bound 4.31). This is a
residual calibration defect, not merely a small-sample guarantee issue.

For fresh realized LGD >75%, n=908, realized bias improves −18.72 → −15.86 →
−13.92 pp across the three models. S2-R1 bias against the conditional mean within
that retrospectively selected tail is +0.35 pp. Realized-tail underprediction
does not disappear; selecting extreme outcomes is not an unbiased test of a
conditional-mean forecast. These results are reported, not hidden or relabelled
as institutional validation.

## Root causes and actual changes

**Downside response / DATA and METHODOLOGY–MODEL IMPLEMENTATION.** Original S2
was evaluated beyond parts of its economic training range. One new constrained
histogram-boosting version was fitted on 156,294 new realized synthetic workouts,
using all 30,000 development borrowers under three historical economic vintages.
No actual or conditional outcome from calibration/current/promotion entered fit.
No bias offset, calibration overlay or MoC was applied. The downside point bias
improved, but seven current economic sector clusters do not establish the frozen
equivalence criterion, and some segment effects remain.

**Scenario ordering / METHODOLOGY–MODEL IMPLEMENTATION.** Signs are constrained
for activity, unemployment, collateral prices, liquidity and protection coverage.
The fixed scenario mapping deteriorates these inputs coherently. Consequently
the prediction function itself is ordered; its three outputs are never sorted.
Single-coordinate and complete-scenario invariants pass. The original recovery
equations and historical models remain unchanged.

**Guarantees / VALIDATION.** Independent fixed-shock cashflow checks verify the
existing waterfall: collateral is capped at EAD; eligible guarantee is capped at
the remaining claim; unsecured/cure recoveries use the residual; costs and
discounting apply once. Full nominal guarantee does not imply full recoverability.
There was no demonstrated double-counting/cap defect warranting changed outcomes.
Boundary tests cover zero, partial, 100% and epsilon transitions. More full-
guarantee development workouts and constrained interactions reduce bias, but
cannot close the guarantee gate.

The diagnostic mean hidden guarantor strength is 0.5502 in development,
0.5899 in fresh promotion, and 0.4812 in current full-guarantee groups. This
observed composition difference is a plausible contributor, **not a demonstrated
causal decomposition**. The variable remains unavailable for deployment and was
not introduced as a feature. Institutional data capture/validation cannot be
replaced by providing the model with simulator truth.

**Support / DATA and GOVERNANCE.** Complete-cycle development histories replace
the narrowly observed original S2 economic domain for this successor only.
Both marginal bounds and local macro × collateral × guarantee recovery support
are checked. All current scenarios pass. The fresh promotion domain still
extends beyond observed development:

| Feature/scenario | Development range | Promotion range | Outside observations |
|---|---|---|---:|
| GDP growth, downside | [−5.434, 5.473] | [−6.190, 2.402] | 176 below |
| Unemployment, downside | [2.000, 10.544] | [4.469, 12.032] | 190 above |
| Collateral change, baseline | [−20.695, 19.127] | [−12.454, 21.123] | 35 above |
| Collateral change, upside | [−20.695, 19.127] | [−9.954, 23.623] | 81 above |

Overlapping GDP/unemployment exceptions yield 327 unique downside rejections.
Local neighbor/cluster checks are also retained; a marginal range check alone
is not treated as sufficient. Unsupported operational inputs raise
`UnsupportedDomain`; raw diagnostic estimates in the comparison exports are
not authorized operational results. No range widening or outcome-driven
regeneration followed these final findings.

## Scenario ECL bridge and reconciliation

All figures are currency units, not an asserted currency or accounting booking.
PD, EAD, stage/SICR/watchlist/EWS, discount conventions and scenario weights are
unchanged. The original frozen V5 aggregation ordering is distinguished from
the scenario-specific ordering used by the existing S2 shadow engine.

| Run | Portfolio ECL |
|---|---:|
| Original governed V5 | 78,746,507.57 |
| Incumbent LGD under existing S2 scenario order | 78,701,888.37 |
| Original S2 | 90,181,093.71 |
| Remediated S2-R1 | 92,036,058.42 |

S2-R1 minus original S2 is +1,854,964.71: weighted upside −62,598.16;
baseline +817,691.80; downside +1,099,871.07. This is a scenario-LGD prediction
movement after refitting the response and support domain, not a change to the
guarantee waterfall or other risk components. Component-specific causal effects
cannot be inferred from this combined refit. Guarantee-group movements are
available in `results/ecl_movement.csv`.

Independent maximum facility recomputation discrepancy is 1.7463e−10; borrower
to portfolio difference is zero. All current inputs pass support, so this shadow
comparison does not contain unsupported current scores. It remains unbooked and
cannot authorize release of a model that fails other promotion gates.

## Eight gates

| Gate | Final status | Evidence |
|---|---|---|
| 1 Current calibration | PASS | Current and fresh baseline equivalence within 1 pp |
| 2 Scenario calibration | FAIL | Current upside/downside bounds 1.17/1.15 pp |
| 3 Scenario consistency | PASS | Zero violations on both current and fresh populations |
| 4 Guarantees | FAIL | Fresh full bound 2.06; current partial downside bound 2.90 pp |
| 5 Model support | FAIL | Current covered; fresh baseline/upside/downside reject 35/81/327 |
| 6 General performance | FAIL | MAE/RMSE improve, but high-prediction bands and several regime/segment bounds fail |
| 7 ECL | PASS | Independent facility/borrower/portfolio reconciliation |
| 8 Engineering/governance | PASS for local reference checks | 151 tests, no skips; source/data/artifact freeze; single final opening |

Engineering PASS does not mean deployment qualification: hosted Actions were not
run (no push), and PostgreSQL/Docker/browser/institutional security checks remain
unqualified. One existing Starlette TestClient deprecation warning remains.

## Evidence chain and reproducibility

Baseline `ef5a1c5` → protocol/tolerances `8cb92ef` → candidate/data freeze
`e8e9228` → single promotion opening → final decision. Original S2 and all
historical evidence are preserved. The pre-fit short-history generator defect
and rejected data are retained in `rejected_generation`; no model or metric was
used to select that correction. Full commands are in this directory's README.

Conditional expectations come from 512 independent simulator draws, not observed
bank outcomes. Confidence intervals use the larger of macro-cluster and borrower-
cluster standard errors and a 1.96 multiplier; they are approximate, particularly
with only seven current economic clusters. There is no externally independent
model-validation team. Independent metric, cashflow and ECL arithmetic provide
implementation evidence, not empirical or regulatory approval.

**Final disposition:** retain `s2-r1-monotone-gb-1` as an unpromoted challenger.
Close scenario-order finding for this candidate only. Keep calibration,
guarantee/segment support and institutional qualification findings open. Further
closure requires new legitimate supporting evidence or a separately governed
change; no additional search or tuning was launched after the final result.
