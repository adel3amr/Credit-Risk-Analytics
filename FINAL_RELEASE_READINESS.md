# Final release readiness

**Reference implementation: PASS WITH LIMITATIONS for local single-workspace synthetic use.**
**Full deployment qualification: PARTIAL. Institutional production approval: BLOCKED.**
No model was promoted. No modelling methodology or synthetic dataset changed.

| Domain | Status | Evidence / residual requirement |
|---|---|---|
| Canonical data / feature contracts | PASS WITH LIMITATIONS | Schema, leakage/time/range tests; legitimate recovery-quality data absent |
| PD / ratings | PASS WITH LIMITATIONS | Independent metrics and rating reconciliation; synthetic outcomes only |
| EWS / Watchlist / SICR / staging | PASS WITH LIMITATIONS | Boundary tests and 5,172-facility independent reconstruction; internal policy only |
| LGD active reference | PASS WITH LIMITATIONS | Preserved historical reference, explicit support and calibration limitations |
| R1 model promotion | BLOCKED | Calibration/segment uncertainty/domain/data gates fail |
| EAD / ECL / portfolio | PASS | Independent arithmetic, aggregate and shadow reconciliation within floating-point tolerance |
| API / SQLite / migrations / audit / overrides | PASS WITH LIMITATIONS | Full suite, immutable evidence and two-person controls; no institutional penetration/load qualification |
| Deterministic Copilot | PASS WITH LIMITATIONS | Numerical grounding, rejection, RBAC, unknown-run and integrity tests; finite refusal patterns not universal language coverage |
| External LLM | BLOCKED for qualified deployment | Disabled by default; opt-in does not constitute validation |
| PostgreSQL | PARTIAL | Baseline hosted migration/shadow/audit passed; final branch and restore not demonstrated |
| Container | PARTIAL | Baseline hosted Docker build passed; Compose service lifecycle/restore not demonstrated |
| Browser UI | NOT VERIFIED | Static resources and real HTTP passed; local browser installation failed |
| CI | PARTIAL | Baseline platform passed; V5 dependency defect fixed; final hosted rerun required |
| Security / authorization | PASS WITH LIMITATIONS for local reference | One shared workspace, not per-user/tenant isolation; external IAM/TLS/rate controls remain institutional work |
| Monitoring / observability | PARTIAL | Support diagnostics, outcome metrics, audit/request logs implemented; no live alerting/SLA proof |
| Reproducibility | PASS WITH LIMITATIONS | Pinned install and local suite; ignored reference data/models require documented deterministic build on clean clones |
| Documentation / evidence | PASS | Current-state map, findings, independent results and frozen history retained |

## External closeout requirements

1. Run both workflows at the final candidate SHA. Confirm new-branch results, not only baseline results.
2. On a Docker-capable host: set unique owner/app database secrets, run `docker compose up --build`, check readiness and actual browser role/drill-down/filters/Copilot workflows.
3. Test PostgreSQL backup/restore with production-equivalent grants, migration owner separation and corruption recovery.
4. Independently qualify institution data mapping, prediction-time recovery information, outcome representativeness, accounting methodology, calibration, monitoring and security controls.
5. Keep challengers and simulator-only fields outside active reference and booked scoring. An institution may not treat the synthetic reference gate as approval.
