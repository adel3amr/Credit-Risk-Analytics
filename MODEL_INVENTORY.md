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
