# Artifact inventory and reproducibility

| Artifact | What it contains | Origin |
|---|---|---|
| `RESEARCH_REPORT.md`, `RESEARCH_REPORT.pdf` | Full assessment and figures | Review-only publication. |
| `CONTENT_INSIGHTS.md`, `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, `DATA_DICTIONARY.md` | Evidence, change classification, risk register, semantic dictionary | Review-only documentation. |
| `evidence/commit_history.csv`, `branches.csv`, `pull_requests.json` | Git/PR chronology | `tools/forensic_inventory.py`, PR metadata retrieval. |
| `evidence/phases.csv`, `capability_matrix.csv`, `test_inventory.csv`, `frozen_source_hashes.csv` | Phase, features, tests, benchmark source fingerprints | `tools/forensic_inventory.py`; matrix includes source-inferred annotations. |
| `evidence/historical_reproduction.csv` | 15 representative clean-checkpoint run commands, generated populations and metrics | `tools/reproduce_history.py`; commit records provide exhaustive context. |
| `evidence/independent_reconciliation.json`, `independent_lgd_segments.csv`, `independent_lgd_calibration.csv`, `independent_facility_traces.csv` | Independent frozen V5 calculations, cohort diagnostics and per-stage worked cases | `tools/independent_recalculation.py` against isolated frozen run. |
| `figures/history.png`, `lgd_calibration.png`, `lgd_tail_bias.png`, `lgd_residuals.png` | Publication plots | `tools/make_figures.py`. |

**Benchmark origin:** `0dfe4c883a8314704394c49fa096dfb45525096c`. Rebuild from source with Python 3.12 and `requirements-v5.txt`. Expected raw-data SHA-256 values from the clean run are `d1ff68a25593693039ee00b0d6b7a1f84b226d2d0995d9e6a54a897fcf5de220` (workout), `38be57d2027ef2fcd3210d6243cf21e45d8f87be7abe998736cd402fcab3cfcc` (36-month behavior), and `2312db398a92c242abec665af6e1e7535b18e47349cfaf0cdf48e8ed3f83c8cd` (borrowers). The raw datasets, fitted joblib models and generated production outputs reside in the isolated run, not committed to the review branch. This avoids a second mutable copy of frozen production artifacts.
