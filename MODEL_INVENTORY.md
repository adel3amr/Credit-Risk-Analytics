# Governed model inventory

| ID / version | Purpose / target | Inputs / outputs | Implementation / data | Validation / limitations | Status / monitoring |
|---|---|---|---|---|---|
| PD / V5 0dfe4c8 | Twelve-month default probability | Contracted borrower ratios/qualitative drivers and sector → PD | Logistic imputer/scaler, 9k training / 3k holdout, seed42; trusted model hash | AUC .759455, Brier .030003; synthetic population, no bank calibration | REFERENCE; calibration/discrimination and source support |
| LGD / V5 0dfe4c8 | Economic facility loss | Ten facility/borrower drivers → LGD | GB frozen structure; validated 6k/2k, reference scoring fit 8k | RMSE .165798 on H; >75 bias −.155928; guarantee support mismatch | REFERENCE, bank BLOCKED; tails/segments/support |
| LGD R2 / ae9942a | Research challengers | R2 inputs plus security/guarantor/downturn proxies | Separate 9k development, 3k selection, 3k final | Final two-stage RMSE .156923 and severe bias −.120482; new fields unavailable | BLOCKED; no active scoring path |
| Oracle / R2 | Information-gap diagnostic | Future cure/timing/shocks | Research only | Non-deployable future information | BLOCKED |
| EAD / v5-ccf-1 | Reporting exposure approximation | Drawn, limit, face and product → EAD | Term drawn, OVD limit, trade .20/.50/1 CCF | Reconciled arithmetic; actual default utilization not validated | REFERENCE; exposure/CCF support |
| SICR/staging / v5-internal-nine-month | Internal policy classification | DPD, impairment, delinquency, utilization, prior default and persistent EWS | Frozen assign_stage; Stage3 precedence | Source-independent tests, no origination-lifetime risk assessment | REFERENCE; triggers/migrations |
| EWS / v5-three-signals | Conduct deterioration | Six-month utilization movement, persistence and breaches | Frozen three conditions | Zero baseline mismatches; thresholds synthetic | REFERENCE; signals and persistence |
| Rating/watchlist / v5-rating-1 | Operational grade | PD, cash eligibility, stage and deterioration | Frozen scorecard.py; Watchlist != SICR | Full cash cannot cure Stage2/3 | REFERENCE |
| Scenarios / CSV content hash | Forward PD scenarios | Fixed macro assumptions → odds shifts/weighted PD | Frozen four sensitivities, weights .2/.6/.2 | Not empirically estimated; no live macro feed | REFERENCE; weight/date/version checks |
| ECL / v5-facility-hazard-1 | Reference loss estimate | PD, stage, LGD, EAD and maturity → ECL | Facility hazard approximation, Stage3 PD=1 | Independent reconciliation, source rounding disclosed | REFERENCE; movement and aggregate checks |

Artifact version, SHA-256, frozen source hashes, dataset identities, owner/purpose, contract and limitations accompany inventory docs and run versions. Registry status cannot become ACTIVE through this API. Database model rows are append-only and research entries explicitly BLOCKED. Institutional promotion requires a separate governed release with empirical evidence and feature/deployment qualification.

## S1 targeted context/rate research candidate

ID `s1-context-rate-gb-1`, status RESEARCH / NOT PROMOTED; same fixed GB as S1,
industry excluded and known borrower interest rate included with quality/context.
Artifact/hash: `research_diagnostics/s1_resolution/results/targeted_manifest.json`.
Development: frozen S1 default facilities only. Evaluation: existing retrospective
selection/final and current simulator expectations; no untouched promotion test.
Limitation: residual conditional errors and institution capture/transfer unknown.
No dependency from governed scoring; current active reference model is unchanged.

## Downturn regime calibration research/control

ID `s1-regime-calibration-1`, RESEARCH. Fractional-logistic bounded mean calibration
of governed LGD with collateral/state interactions, development outcomes only.
Artifact/coefficients: `research_diagnostics/downturn_resolution/results/`. True-state
version is ORACLE ONLY; proxy variants not promoted. Explicit normal/downturn
scenario helper preserves original predictions, rejects expected-loss booking, and
returns a separate risk sensitivity. No active registry or risk-engine replacement.
# S2 additive inventory entry — 27 September 2026

`s2-observable-gb-1`: CHALLENGER, NOT PROMOTED. Conditional LGD on synthetic S2
workouts; frozen existing Gradient Boosting architecture plus four economic
observables and effective interest rate. Registry, hashes, full metrics and
limitations: `economic_lgd/results/registry.json` and `economic_lgd/DECISION.md`.
Excluded: latent state, recovery outcomes, unobserved quality. No active replacement.
# S2-R1 inventory addendum — 27 September 2026

| Field | Value |
|---|---|
| Model | `s2-r1-monotone-gb-1` |
| Purpose/target | Conditional-on-default discounted economic LGD |
| Methodology | Histogram gradient boosting with economic/protection monotonic constraints; squared error; versioned successor |
| Inputs | Unchanged S2 facility/economic feature contract; no hidden quality or outcomes |
| Output | Bounded LGD; unsupported-domain rejection before operational scoring |
| Development | 156,294 independent simulated workouts on 30,000 borrowers across 1,680 economic vintages |
| Validation | Separate calibration; 6,000 fresh promotion facilities; known 8,695-facility current diagnostics |
| Status | CHALLENGER, NOT PROMOTED; see authoritative `s2_remediation/results/registry.json` |
| Limitation | Residual guarantee uncertainty and domain coverage; synthetic assumptions and unavailable institutional qualification |
| Dependencies | Frozen S2 recovery mechanism, new cycle history, original S2 feature contract, frozen support object |
| Monitoring | Bias/uncertainty, scenario order, guarantees, local support rejections, segment and tail diagnostics |

Previous V5/S1/S2 inventory entries and artifacts below remain historical evidence.
# Post-R1 inventory event — 28 September 2026

`s2-r1-continuous-calibration-1`: DEVELOPMENT candidate **REJECTED**, not promoted.
Global continuous monotone calibration of frozen R1 using 6,000 matured
calibration realized outcomes. Known engineering validation worsened downside
and high-band errors. Artifacts and fit-source hashes are retained in
`lgd_hardening/results`. The retained candidate stays `s2-r1-monotone-gb-1`,
CHALLENGER_NOT_PROMOTED. No new final independent holdout opened.
