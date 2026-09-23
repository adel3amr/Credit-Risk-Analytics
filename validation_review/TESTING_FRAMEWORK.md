# Testing strategy and actual results

| Level | Scope | Result on 23 September 2026 |
|---|---|---|
| Unit/policy | Existing source regression tests plus 22 review boundary cases for DPD/EWS migration, product mapping and numeric ECL at zero/one PD and zero EAD/LGD | 49/49 pytest pass in review branch; frozen commit by itself 27/27. |
| Data | IDs/links, structural missingness, numeric bounds, source recovery sample and product cashflow integrity | 15/15 direct checks, `evidence/frozen_data_quality.json`. |
| Integration | Source rebuild and model pipelines, split disjointness, raw recovery target, PD validation and facility/borrower sums | 30/30 frozen release checks plus `evidence/independent_reconciliation.json`. |
| Interface | Five demonstration roles, three filters and search; reviewer compares hero totals, validator metrics and one facility drill-down with source CSVs | Frozen AppTest smoke passed and 25/25 extra source comparisons, `evidence/dashboard_reconciliation.json`. |
| Historical | 15 immutable archived snapshot pipelines and four isolated experiments | All selected commands completed, `evidence/historical_reproduction.csv`; historical dependency lock was not preserved. |
| Reproducibility | Python 3.12 with `requirements-v5.txt`, fixed source commit, generator hashes and results | Raw hashes match `ARTIFACT_INVENTORY.md`; total EAD/ECL reproduce. |

**Remaining test gaps:** real out-of-time loss data, operational role enforcement, sustained browser usability/accessibility, stateful stage migration after a live event ledger, deployment/monitoring, and remote CI observation for this review branch. They are in `FINDINGS_REGISTER.csv`. Re-running the tests should not be mistaken for measuring out-of-sample institutional performance.
