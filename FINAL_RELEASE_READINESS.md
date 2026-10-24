# Final release readiness

**Public research / professional-demonstration release: READY.**  
**Verified full-workflow qualification:** `79a031192f4477351528e7384004d1d4e970a488` (24 October 2026, both branches).  
**Publication review:** 24 October 2026.

The current repository is runnable from a clean checkout, preserves its model/research challenge history, and exposes the consolidated platform through the public/default branch. It remains a research implementation using synthetic/publicly informed data; this status is about repository quality and reproducibility, not a live-bank approval claim.

| Domain | Publication status | Current evidence |
|---|---|---|
| Clean installation / dependencies | PASS | Python 3.12 + pinned `requirements-platform-lock.txt` on fresh GitHub runners |
| V5 data/model rebuild | PASS | deterministic generation + trusted artifact hash controls |
| Automated suite | PASS | **256 passed, 1 upstream warning** |
| V5 release checks | PASS | **30/30** |
| EAD/ECL/staging reconciliation | PASS | **5,172 facilities**, **0 stage mismatches** |
| Audit chain | PASS | **VERIFIED** |
| PostgreSQL | PASS for reference qualification | fresh migrations + full shadow + WN-1 persistence in hosted CI |
| Streamlit | PASS for reference qualification | headless startup/health smoke in hosted Linux CI; local demo exercised by project owner on Windows |
| Docker image | PASS | hosted Docker build |
| Risk Copilot | PASS for research demo | deterministic grounding + question-relevant Ollama context, optional full-context retrieval, visible fallback + exact-analytics routing |
| Documentation | PASS after publication refresh | README, reproducibility, Copilot guide, validation map and research history aligned |
| Historical research evidence | PASS / preserved | V5, validation review, S1/S2/R1/hardening, Marginal Interest and WN-1 remain separately traceable |
| LGD challenger promotion | NOT PROMOTED | adverse calibration/support/feature-transfer findings remain documented rather than hidden |

## What a reviewer should read

1. [README.md](README.md) — system overview and clean run.
2. [PUBLICATION_READINESS.md](PUBLICATION_READINESS.md) — current state, evidence and challenge map.
3. [FINAL_INDEPENDENT_VALIDATION_REPORT.md](FINAL_INDEPENDENT_VALIDATION_REPORT.md) — independent review.
4. [MODEL_INVENTORY.md](MODEL_INVENTORY.md) — active/reference/research model inventory.
5. [PLATFORM_CHANGELOG.md](PLATFORM_CHANGELOG.md) — classified evolution.
6. [REPRODUCIBILITY.md](REPRODUCIBILITY.md) — clean-clone commands and CI proof.
7. [GENAI_COPILOT_GUIDE.md](GENAI_COPILOT_GUIDE.md) — current Copilot design.

## Remaining boundaries

The repository does not claim real-bank empirical calibration, regulator/accounting approval, external IAM/MFA/TLS/perimeter deployment, penetration/load/SLA qualification, or a production monitoring/alerting estate. Those are external implementation/validation activities and do not prevent the repository from being a complete reproducible research demonstration.

Historical failed challengers, blocked promotion decisions and adverse findings are intentionally retained. They are part of the project's model-risk evidence, not incomplete cleanup.
