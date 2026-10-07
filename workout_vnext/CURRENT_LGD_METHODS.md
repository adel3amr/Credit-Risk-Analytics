# Phase 1 — frozen methodology reconstruction

Verified source baseline: 20595b33a121acd1148aac704ea1e9ab83171936, descendant of immutable reviewed 7773beb86df8480d964daaaf62199cedc15d356a. No methodology changed before this reconstruction. Prompt correction: MI ECL used unspecified currency units, not verified EUR.

| Topic | V5 active reference | S2-R1 research | MI-1 research |
|---|---|---|---|
| Target | Bounded 1 − discounted net recovery/default EAD | Same economic default/reference-date target, observable macro inputs | Remaining loss/remaining principal at impaired observation |
| Exposure | Term loan drawn; OVD limit; trade face×CCF .2/.5/1 | Source facility default exposure | Principal after dated repayments, suspended interest excluded |
| Default/staging | >=90DPD or credit impaired Stage3; >=30DPD/approved SICR Stage2; internal9month EWS treatment preserved | Hypothetical workout population | All observation rows impaired Stage3 |
| Observation | Borrower/facility reporting snapshot | Hypothetical reporting date; not fully dated legal/workout state | Monthly default-to-observation ledger,1–24months |
| Horizon | Recovery buckets1/6/12/24/36/60months | Same buckets to60months | Future buckets from observation,60months |
| Discount | Synthetic workout discount rate .035–.12; production artifact fitted to target | Contractual/effective source interest_rate | Same rate, remaining principal cashflows |
| Collateral | Capped recovery with type,coverage,lien and realization effects | Market/liquidity-sensitive recovery; hidden security_quality affects DGP | Static nominal collateral divided by remaining principal |
| Guarantee | Coverage capped at residual after collateral | Guarantor strength hidden from scoring,macro-sensitive | Coverage updated for reduced principal; no dated claims |
| Cure | Simulator cure probability and top-up recovery,not separate predictor | Latent cure and timing mixture | Extra full-payoff cure path; incomplete labels for inner simulator cure |
| Restructure | No complete dated restructuring/payment ledger | No separate dated state engine | One known binary decision; no full negotiated payment plan |
| Writeoff | Ex-post flag LGD>=.97,not predictor | Economic loss remains independent of accounting writeoff | No dedicated accounting event ledger |
| Unresolved | Simulated completed outcomes,not censor-aware | Future synthetic outcomes,not empirical completed history | Completed synthetic future outcomes; no censor estimator |
| Interest | No complete suspended-interest ledger | Rate used for PV; no complete accrual allocations | Noncapitalized opening principal×rate/12 memorandum amount |
| Costs | Negative net recovery cashflows;type/lien-sensitive | Explicit costs within buckets | Inherited costs plus hypothetical cure cost |
| Scenario | Governed weighted macro PD; V5 LGD artifact adapter | Macro growth,unemployment,collateral price,liquidity;monotone challenger | Same mapping,new frozen research scenario fixtures |
| Status | Synthetic reference only,bank blocked | CHALLENGER_NOT_PROMOTED | CHALLENGER_NOT_PROMOTED |

Information sets: original financial/product/security coverage features are observation inputs; S2 source security_quality/guarantor_strength and MI willingness/shocks are DGP-only; eventual proceeds,cure,writeoff,resolution and recovery dates are future outcomes. Their observation-time equivalents require dated capture,not relabelling ultimate values.

Prior findings: V5 tail underprediction and development/current guarantee mismatch; two-stage research insufficient; S2-R1 current conditional bias+.10pp did not overcome downside/fully-guaranteed uncertainty, prediction-band calibration or327/6000 downside support exceptions. MI: M4 RMSE21.9075% vs M0 22.1715% on a DIFFERENT remaining-loss target; MI-specific increment0.0104pp,CI spanningzero.200 tests passed. No new feature/promotion follows from that small difference.

Sources: src/lgd_model.py; scripts/generate_lgd_workout_history.py; credit_platform/risk.py; economic_lgd/recovery.py; s2_remediation/{model,generate,support,review}.py; marginal_interest/{PROTOCOL,REPORT,FEATURE_CONTRACTS}.md. Old artifacts/datasets/adverse evidence remain unchanged.

Architectural gaps: no relational legal/security/claim timeline; no dated PD/rating in MI; incomplete cure labels; unresolved exposures not represented; portfolio Copilot builds its own SQL stage aggregation despite common base portfolio,creating a divergence risk. vNext must isolate the new methodology, provide as-of joins and one shared portfolio evidence view, rather than silently replacing the production risk engine.
