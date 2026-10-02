# MI-1 feature and target contracts

All monetary amounts are unspecified currency units; rates are annual decimals, LGDs fractions. One default episode per source borrower, multiple facilities permitted within borrower. All synthetic predictor snapshots are created before actual outcomes. Event date and observation date use monthly anniversary dates; same-day recorded payment is available at end of observation day. No accounting posting-delay model exists.

| Feature | Definition/source | Availability/range | Operational fallback |
|---|---|---|---|
| marginal_interest_amount | Sum of opening monthly principal × contractual rate/12 through observation; noncapitalized memorandum, no interest payments in this policy | New ledger only, >=0; known at observation | Reject if ledger/definition missing; no zero imputation |
| marginal_interest_to_principal | Above / observation remaining principal | New ledger, >=0 | Reject zero denominator |
| marginal_interest_to_ead | Same ratio because EAD=remaining principal here | Diagnostic only; excluded duplicate | Not an additional predictor |
| months_since_default | Number of completed monthly accrual/payment events | 1–24, known dates | Reject missing/invalid date |
| cumulative_recovery_ratio | Principal repayments through observation / default principal | [0,1) | Requires dated principal allocation |
| recent_recovery_ratio | Principal repayments in final three months / default principal | [0,1) | Requires dated events |
| months_since_last_recovery | Elapsed months since last positive payment; age if none | [0,24] | Explicit no-payment convention |
| restructured | Restructuring decision recorded at observation | 0/1 | Must be captured; no final outcome substitution |
| default_principal | Principal at impairment | >0 | Requires archived default balance |
| ead_at_default | Legacy feature name; in this isolated release contains observation principal | >0; DOES NOT retain historical default-EAD semantics in this new target | Research-only adapter, never production mapping |
| interest_rate | Source contractual/effective rate used by existing simulator | >=0, frozen through episode | No repricing model |
| collateral/guarantees | Original nominal support / remaining principal, guarantee cap1 | As-of quantities, no future proceeds | Future valuation deterioration not captured in ledger |
| original risk drivers | Original financial, management, product, collateral, lien, industry and macro fields | Existing allowlist retained | Existing contract |
| source_pd/source_rating | Not in source schema | UNAVAILABLE, omitted | No invented PD or rating; separate control test unresolved |

New features: RESEARCH ONLY / REQUIRES NEW DATA CAPTURE in current platform. Synthetic availability is not production availability. The source current/live population lacks these contracts, so live missingness is **not measurable as an existing column**, rather than fabricated as 0%. Refresh expectation for future capture: monthly, archived effective and posting timestamps; audit payment allocation, ledger balance, impairment/cure status and capitalization policy. No operational capture mechanism is implemented here.

Prohibited model fields: actual/final LGD, cure, resolved date, future cashflows, willingness, quarter shock, simulator security_quality/guarantor_strength, latent_regime and latent conditional mean. Source financial/PD information may be stale: no fresh institutional validation is claimed. Latent regime used only to report diagnostics, never scoring.

Target lineage: future principal cashflows and recovery costs -> discount to observation at contractual/effective rate -> divide by remaining principal -> bound0–1. Full payoff cure at month6, fixed recovery cost .5% at month1, is a new hypothetical research outcome; original recovery simulator also has a latent cure channel, so reported `cure` identifies this explicit full-payoff event only and cannot enumerate all internally cured paths. This partial cure-label limitation prevents full cure-governance clearance.

Source schema and algorithm retain their historical names. Every new dataset carries MI-1 identity and is isolated from the production feature layer. No Stage1/2 scoring, integration or registry promotion is performed.
