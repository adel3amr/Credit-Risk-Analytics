# Current system baseline

Reference: `ae9942a`, inspected and rebuilt 24 September 2026. Repository-wide historical reconstruction remains in `validation_review/`; this work adds current evidence under `platform_evidence/` without replacing it.

The current system generates 12,000 synthetic borrowers and 36 months of conduct, trains governed logistic PD and facility Gradient Boosting LGD, derives EWS/staging/rating, applies macro PD assumptions, calculates facility EAD/ECL, aggregates and displays CSV outputs through Streamlit. V4→V5 adds facility recovery and robust input checks; no wholesale V4 copy is required. Source and changed-file inventories are archived.

The newest completed programme is LGD R2 research at ae9942a, after whole-repository validation. It includes the 2×2 data/model experiment, ablation, oracle, segment and tree comparisons, two-stage/component/quantile candidates, frozen holdout, stress, 18 figures, research paper and findings. No challenger was promoted. New quality inputs are unavailable in the scoring population. Repeating these experiments has no present justification.

Models and generated CSV files have no database transaction, persisted run identity, backend identity enforcement or controlled operational service. The role selector is demonstration UI. Scenarios are versionable CSV assumptions, not observed macro forecasts. Historical snapshots, source hashes, adverse findings and failed experiments remain valuable evidence.

Baseline reproduction: 54 tests pass; clean V5 build and independent PD/stage/EWS/EAD/ECL reconciliation pass. See AUTHORITATIVE_BASELINE_RECONCILIATION.md for exact metrics and limitations. The original working tree contains a truncated R2 training CSV and remains untouched; isolated committed checkout has the correct hash.
