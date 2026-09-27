# S2-R1 focused remediation protocol — frozen before generation

Baseline: `ef5a1c55b1b0cf52bec1f0941dd1f0a5a8eeec6e`. Original S2, its
cashflows, model, validation and adverse findings remain immutable. This is one
candidate, not a model search. No numerical bias offsets or post-score sorting.

## Diagnosis and changes

The existing recovery waterfall caps collateral at EAD, guarantee at remaining
EAD, and other recovery at the residual. Nominal 100% guarantee is not 100%
recoverability: quality, stress, costs and discounting still apply. There is no
evidence of double counting warranting a changed target. Preserve this waterfall
and independently test it. The guarantee finding is a prediction approximation
and sparse-support hypothesis, not proof that realized recoveries are wrong.

Downside changes four economic coordinates coherently, but two leave the original
training range. Unconstrained trees also introduce economically unexplained
reversals. Extend development histories across complete synthetic cycles and fit
one histogram gradient-boosting model with monotone macro and protection inputs.
This constrained estimator is a **METHODOLOGY / MODEL IMPLEMENTATION** version
change; it is never silently substituted for historical S2 or V5.

Fixed estimator: squared error; 350 iterations; learning rate .05; 31 leaves;
minimum leaf 80; L2=5; seed=94001; no early stopping or hyperparameter search.
Monotonic signs: activity −, unemployment +, collateral prices −, liquidity −,
collateral coverage −, guarantee coverage −. Other incumbent features unchanged.
No hidden state, security quality, guarantor strength, actuals or simulator
conditional expectations are permitted training/scoring features or fit targets.
Fit only independently drawn, realized recovery cashflows. No calibration overlay.

## Data and independence

S2-R1 uses the same frozen recovery mechanism and source facility economics.
Development uses all S1 development facilities under three independent historical
economic vintages; borrower attributes repeat, but outcomes are new independent
workouts. This increases coverage of rare guarantee/collateral interactions;
it does not turn repeated borrowers into independent borrowers for uncertainty.
Quarterly histories 1950–2009 cover expansion, normal, deterioration, recession,
and recovery with persistent and correlated observable shocks. These are
hypothetical synthetic dates, not real bank history. All resolve by 2015.

Calibration/audit: 6,000 S1 selection facilities under 2016–2018 vintages,
resolved by 2024. No fit or tuning on these results is planned. Promotion:
6,000 S1 final facilities whose borrowers were **not** in the inspected S2 final
population, assigned fresh 2026–2028 economic vintages and new workout draws.
Synthetic future resolutions are evaluation fixtures, not currently observed
institutional evidence. Current S2 is a known diagnostic population, never called
an untouched holdout. Source borrower sets are disjoint across cohorts.

Seeds: development 94001; calibration 94002; promotion 94003. Targets seed+200;
conditional diagnostic streams 96001 onward, 512 draws. Freeze datasets, source
hashes, feature names, model and evaluator before opening promotion outcomes.
Final evaluation runs once; no retuning from its results.

## Support and operational handling

Check marginal macro ranges and local **joint** macro × collateral × guarantee
support, separately by collateral type. Scale the four macro variables and two
coverage variables by development IQR (no outcomes). Require at least 20 nearby
recovery observations within 0.75 IQR in every coordinate, spanning at least
three distinct sector/quarter clusters. These are minimum evidence-density
controls, not statistical guarantees. Log counts, distances and failed fields.
All intended current scenarios must pass; any unsupported score is rejected with
`UnsupportedDomain`, never clipped to training extrema or silently extrapolated.
Future extreme scenarios are blocked pending a new governed domain validation.

## Predeclared promotion tolerances

These are internal synthetic-reference tolerances, not regulatory materiality or
bank approval. One percentage point means 1 currency unit per 100 units of
PD-weighted EAD; two points is reserved for smaller, noisier segments. Report
currency effects and confidence intervals alongside these tolerances.

1. Current and fresh promotion conditional bias: absolute bias plus 1.96 clustered
   SE ≤ 1 pp (equivalence, not failure to reject zero).
2. Downside and upside: same ≤ 1 pp on current and promotion scenarios.
3. Scenario order: zero reversals beyond 1e-10; no sorted predictions.
4. Zero/partial/full guarantees: absolute conditional bias + 1.96 SE ≤ 2 pp;
   each promotion group ≥100. Waterfall identity, caps and boundary tests pass.
5. No rejected current scenario inputs; no silent scores outside support.
   Report fresh promotion exceptions; any exception blocks promotion.
6. Overall MAE and RMSE no worse than original S2 on the same new holdout.
   Normal/downturn ≤1 pp conditional bias including uncertainty. Material
   collateral/product/industry/exposure/coverage/prediction bands (n≥100)
   ≤2 pp including uncertainty. Realized-outcome tails are retrospective
   selection diagnostics, not unbiased conditional-mean targets; report them.
7. Scenario ECL facility recomputation ≤1e-7 currency; borrower/portfolio ≤1e-6;
   PD, EAD, stage, SICR, EWS and scenario weights unchanged.
8. Full existing and new tests pass; hashes, contracts, as-of controls, frozen
   candidate and untouched-final sequence verified. Any failure blocks promotion.

Cluster uncertainty by sector/quarter; also report borrower clustering where
practical. Seven current sectors limit inference. Conditional truth is simulator
truth, not independent empirical truth. Independent cashflow and ECL arithmetic
do not establish independent institutional model validation.

## External evidence and applicability

ECB WP2954 (2024), https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2954~1d1f8942c9.en.pdf,
reviewed 2026-09-27: supports collateral-dependent economic sensitivity, not this
simulator's coefficients or universally monotone real-bank LGD. Monotonicity here
is justified by the frozen synthetic recovery mechanisms and scenario mapping.
Scikit-learn 1.8 official HistGradientBoostingRegressor documentation,
https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html,
reviewed 2026-09-27: supports constrained boosting implementation; no credit-risk
approval is inferred. No literature coefficient is transplanted.

Classification: DATA (historical domain), METHODOLOGY/MODEL IMPLEMENTATION
(constrained estimator), VALIDATION (support/gates), GOVERNANCE/DOCUMENTATION.
Institutional bank-use gate remains blocked regardless of synthetic promotion.
