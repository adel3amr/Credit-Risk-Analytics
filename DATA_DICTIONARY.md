# Data dictionary

Canonical version 1 is defined by `credit_platform/domain.py`; relational types/keys by `credit_platform/schema.py`. Model features and definitions are enumerated in MODEL_FEATURE_CONTRACTS.md and its JSON contract.

| Field | Definition / type / unit | Controls |
|---|---|---|
| id, borrower_id | Stable source identifiers, string | Unique per snapshot; facilities require borrower FK |
| effective_date | Business reporting date, ISO date | No future-observed inputs |
| recorded_at | UTC system ingestion timestamp | Immutable, separate from business date |
| observed_at | Source information date | Must not exceed reporting date |
| source | Mapping/source identity | Required; hash provenance |
| drawn, limit, face | Nonnegative monetary inputs | Same synthetic currency unit per reference portfolio; no FX conversion |
| remaining_months | Nonnegative contractual remaining months | Required; no silent default |
| collateral_type, coverage, lien_rank | Facility security terms | Unsecured means zero collateral and unsecured lien |
| guarantee_coverage | Fraction 0..1 | Synthetic V5 product mapping, not proof of enforceability |
| source_hash, hash | SHA-256 canonical JSON | Verified on reads and trace reconstruction |
| models / versions | Model and source hashes | Trusted local files only; status REFERENCE |
| stage_reasons / ews | Trigger-level policy evidence | Retained inside immutable trace |
| original_ecl / proposed_ecl | Original result and requested reference adjustment | Original never overwritten; different manager approval |

All current data are synthetic, INTERNAL. Future borrower/facility/financial data should be CONFIDENTIAL; credentials RESTRICTED. Statistical support minima/maxima are observed, not approval thresholds. Generator field rules remain in scripts/generate_sme_portfolio.py and scripts/generate_lgd_workout_history.py; R2 recovery assumptions remain separate.
