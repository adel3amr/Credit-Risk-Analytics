# Current/downturn LGD final decision

25 September 2026. Baseline: 4a9599f. No push authorized or performed.

## Is the LGD issue finally solved? **NO**

**Final classification: E — UNRESOLVED for legitimate operational point prediction.**
The mechanism is now demonstrated, and an evidence-based scenario control is
implemented. That control does not turn an unobserved synthetic state into a
validated economic input or an approved expected-loss adjustment.

A development-fitted transparent calibration reduces current conditional bias from
**-12.65 pp to +0.55 pp when supplied with the true synthetic regime**. It is an
oracle sensitivity, not deployable. Canonical scoring inputs do not identify the
current regime reliably: the no-industry proxy has AUC **0.5001**, while the industry
proxy exploits a development shortcut and has current AUC **0.2274**. Quality fields
raise AUC only to **0.5936** and require institutional capture. There is no validated
macro/recovery data source that maps onto the arbitrary S1 sector-state assignments.

The simplest mathematical correction works, but its required state information
is missing from legitimate operational inputs. Additional tuning cannot supply it.
No source dataset was regenerated, no historical benchmark was shifted, and no
active PD/LGD/EAD/staging/SICR engine was modified.

## Root cause and mechanism

S1 chooses one random downturn regime per sector/vintage after generating borrower
fundamentals. That regime affects recovery outcomes but is absent from the incumbent
scoring contract. Current exposure is 82.38% in downturn sectors, versus 8.65% of
final workouts. Industry predicts development regime perfectly because each sector
has one state; that association reverses across vintages. The source is a synthetic
latent sector condition, not an observed GDP series or independently measured index.

Direct pathways in the unchanged S1 generator:

| Mechanism | DGP change for downturn | Sequential current mean LGD contribution |
|---|---|---:|
| Collateral recovery | Subtract .20 from the realization multiplier before clipping | +1.9154 pp |
| Guarantee recovery | Subtract .20 from guarantor realization multiplier | +0.3930 pp |
| Unsecured collection | Subtract .10 from residual collection rate before clipping | +3.5730 pp |
| Cure | Reduce cure log-odds by .55 | +2.8608 pp |
| Timing | Add 13 months to ordinary timing; add 4 months for cash | +2.2519 pp |
| Cost | Add .025 of EAD to costs before bounds | +1.8813 pp |

Total direct effect: **+12.8753 pp** with quality fields fixed. These are sequential,
order-dependent paired simulator effects, not independent additive causal estimates
for real bank data. Same seed, 1,024 draws/facility, all switches checked against
the independent S1 equations. Full collateral-segment breakdown is retained.

The source also reduces security quality by .10 and guarantor strength by .12
before clipping. Restoring these on a diagnostic copy reduces ordinary-context
LGD by a further 0.8328 pp. Because clipping loses latent information, this is a
bounded-restoration sensitivity rather than an exact indirect causal decomposition.
It must not be casually added to the observed baseline shortfall. Discount rate is
not directly changed by this state; it is the pre-existing borrower rate. Lien and
collateral caps create heterogeneous effects; no global +12.65 uplift was used.

## Before/after evidence

No column below is an approved replacement. All fitted corrections use development
realized outcomes only; all current comparisons use existing 4,096-draw conditional
expectations. Final is already examined and remains retrospective. Final MAE/RMSE
use 1,017 workouts; current has 8,695 facilities and no realized future targets.

| Candidate | Final MAE pp | Final RMSE pp | Final bias pp | Current conditional bias pp | Current downturn bias pp | Current normal bias pp | Final realized >75 bias pp | Current ECL million |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Governed baseline | 13.05 | 18.10 | 0.03 | -12.65 | -15.59 | 1.05 | -12.11 | 78.75 |
| Existing enhanced (true synthetic context) | 12.39 | 17.08 | 1.48 | -1.25 | -2.05 | 2.50 | -15.31 | 98.18 |
| True-state calibration ORACLE | 12.47 | 17.05 | 1.33 | 0.55 | 0.24 | 2.03 | -13.92 | 99.09 |
| Canonical proxy calibration | 14.68 | 19.75 | 5.47 | -6.31 | -11.08 | 15.96 | -12.61 | 88.21 |
| Canonical proxy without industry | 13.13 | 18.18 | 4.93 | -6.66 | -9.58 | 7.00 | -12.02 | 88.12 |
| Quality-proxy (new capture required) | 12.95 | 18.01 | 4.82 | -6.33 | -9.14 | 6.85 | -11.84 | 88.49 |
| Declared all-downturn sensitivity | 16.93 | 22.68 | 14.42 | 3.17 | 0.24 | 16.85 | -4.26 | 103.63 |

The previous R2 two-stage comparison is preserved in its original report. There
is no serialized two-stage artifact in the repository, so it was not rebuilt merely
to add a current-population row. Its published R2 performance is not a fair substitute
for a measured S1 comparison. Existing enhanced S1 and all new serious candidates
are evaluated on the same S1 rows. Reports retain prediction bands, collateral,
guarantees, products, lien, industry, EAD bands and conditional high-risk groups.

## What was tested and rejected

**Deployable proxies:** fixed nonlinear classifiers were fitted to development only.
The industry model's development state AUC is 1.000, but current 0.227; removing
industry gives current 0.500. This is evidence against relying on the sector shortcut.
It does not prove no possible proxy could ever exist. More strongly, the generator
can change D while holding all canonical incumbent inputs unchanged; such inputs
cannot distinguish those alternative recovery environments. The existing sensitivity
experiment demonstrates a 12.87 pp mean difference between observationally identical
canonical inputs. Expected loss requires either state information or credible weights
for that missing state, not just an alternative regressor.

**Calibration:** a bounded fractional-logistic mean model uses base LGD logit,
regime, collateral categories and their regime interactions. Slopes have a fixed
L2 penalty of 1; no search, no fitting to simulator means, no current recalibration.
True-state current bias is +0.55 pp (normal +2.03, downturn +0.24), establishing that
state awareness can remove most of the shortfall. The same correction with the
best-evidenced canonical no-industry proxy remains -6.66 pp overall and -9.58 pp
in downturn, while overpredicting normal conditions by +7.00 pp. That fails the
normal/downturn protection objective. Extra captured quality proxies still leave
-6.33 pp overall and -9.14 pp in downturn, normal +6.85 pp.

**Global downturn/MoC:** applying the all-downturn scenario gives +3.17 pp current
bias, but **+16.85 pp** bias for normal current facilities and +14.42 pp final
realized bias. It therefore cannot be booked as unbiased expected LGD. No threshold
was loosened and no uplift was installed. A probability-weighted mixture needs
externally supported weights: none were estimated from current hidden labels.

## Selected risk control—implemented, not a booked MoC

`research_diagnostics/downturn_resolution/calibration.py::scenario_control` provides
a reproducible development-estimated scenario sensitivity. It requires an explicit
normal/downturn scenario, source description and run ID; preserves original LGD/ECL;
returns calibrated scenario LGD/ECL and nonnegative incremental facility sensitivity;
rejects expected-loss, booking and production purposes. No automatic trigger based
on the synthetic hidden state exists in the operational engine.

Scope: the assessed synthetic current portfolio, with collateral-category responses
estimated from 1,933 development workouts. This is a reference risk control and
scenario report, not an institution-approved reserve or a prudential MoC model.
Review when independent macro/recovery data, policy-approved regime probabilities,
representative regime histories or fresh outcome validation becomes available.
Remove the restriction only after governed feature and promotion checks pass.
The applied production control remains **bank-use blocked**; original best-estimate
reference outputs are preserved with an explicit limitation.

## ECL impact and reconciliation

Governed current ECL remains **78.7465 million** synthetic currency units. True-state
oracle calibration gives **99.0890 million**, compared with simulator-mean diagnostic
100.0760 million from the prior analysis. Declared all-downturn scenario ECL is
**103.6257 million**, +24.8792 million versus reference; this is scenario sensitivity,
not a booked increase. The nonnegative per-facility incremental control can differ
from a net portfolio delta because it does not offset positive sensitivities with
negative ones. Both original and scenario values remain visible.

PD, effective lifetime/stage PD, EAD and stages were held fixed using the existing
audited facility traces. Facility/borrower/portfolio sums reconcile within floating
point tolerance. Stage, collateral, industry and downturn breakdowns are in
`results/ecl_impacts.csv`. No zero/NaN/Inf or outside-range predictions are accepted.

## Governance and remaining evidence gap

Governed LGD retained as REFERENCE. No challenger promoted. No expected-LGD calibration
or booked MoC introduced. Only the separate guarded scenario control was added.
The oracle result does not clear deployability, stability or untouched-validation
gates. Quality/context labels in synthetic records are not proof of real institutional
measurement. Existing final/current populations cannot become untouched again.

A legitimate operational resolution now requires a dated independently observable
recovery-environment feed (with jurisdiction, sector, source, availability timestamp,
refresh rules and missing-data behavior) and a validated mapping to recovery response,
or externally supported scenario probabilities and an approved uncertainty policy.
The S1 random regime is not tied to a public economic series; attaching real current
GDP or collateral-index data would not identify its arbitrary historical draws.
Inventing such a mapping would manufacture evidence. No further blind ML search is
justified within the supplied data/information set.

Institutional calibration, deployment/hosted CI/PostgreSQL/container/browser and
security gates remain separate and blocked. This decision is not bank certification.

## Primary accounting context

IFRS Foundation, IFRS9 5.5.17 and B5.5.41–42, 2021 issued text, accessed 25 September
2026: expected loss considers probability-weighted outcomes and supportable available
information, rather than simply using a worst-case scenario. This is why the stress
sensitivity is not relabelled as an allowance. Prudential EBA downturn/MoC literature
is a different framework; no prudential floor or multiplier was imported here.
https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ifrs-9-financial-instruments.pdf

## Tests and reproduction

Baseline is 111 tests, superseding the mandate's older 107. Eleven targeted cases
cover bounded/reproducible calibration, mixture arithmetic, explicit scenario
selection, forbidden booking purposes, preserved baseline/ECL propagation, invalid
probabilities, and all-on/all-off DGP equation parity. **122 tests passed, zero failed** (one existing dependency deprecation warning). Full test evidence is retained.

Pinned environment; `python -m pytest -q`. Evidence is already committed. To repeat
this exact research in a disposable checkout, preserve/move only this diagnostic's
`results` directory, then run `python -m research_diagnostics.downturn_resolution.run`.
The script refuses to overwrite results and never regenerates S1 data. Source and
artifact hashes plus coefficients are retained. Existing R2/S1/research evidence
and failed candidates remain unchanged.

## Change record

New files: diagnostic protocol; bounded calibration and explicit scenario helper;
mechanism-switch integration; focused run script; result tables, coefficients,
artifact and manifests; eleven test cases in `tests/platform/test_downturn_resolution.py`.
Root inventory, feature contracts, findings, readiness/validation reports, limitations,
external evidence register and changelog were updated. New calibration is classified
METHODOLOGY / RESEARCH ONLY; mechanism tests are VALIDATION, scenario restrictions
GOVERNANCE. No active-methodology change was made. The commit containing this report
is the final local research/control change; no GitHub push was attempted.

Approximate borrower-cluster confidence intervals, sample counts and Monte Carlo
precision are retained in grouped metrics. They are conditional on synthetic
vintages and do not quantify uncertainty across all possible sector-regime maps.
No independent institutional approval or untouched final promotion sample exists.
