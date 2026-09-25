# Final platform validation report

24 September 2026. Scope: whole-project reference platform on `platform/production-foundation`, rooted in newest research `ae9942a`. Independent here means source-independent recalculation and adverse tests; no external validator sign-off is claimed.

## Verified baseline and history

Frozen V5 remains `0dfe4c8`; PR25 is open/unmerged. Its hosted interface/risk workflows succeeded (35879967200 / 35879966965). No hosted research or platform success is asserted. Full historical source reconstruction remains in validation_review. The new baseline commit d50d6f8 records reconciliation before platform implementation. Original local R2 training truncation is preserved outside this clean worktree; all frozen source/R2 hashes verified in platform_evidence/frozen_hash_verification.json.

## Model evidence

PD validation independently reproduced AUC .759455473, Gini .518910946, KS .408496732, Brier .030002535 and LogLoss .128562115 across 3,000 held-out borrowers, 102 defaults. V5 H LGD: 2,000 holdout, MAE .113964529, RMSE .165798487, bias −.003051719; realized >75%: 327 observations, bias −.155927834. No challenger was promoted.

Newest R2 final common predictions were independently recalculated: 3,000 facilities, 536 >75%; V5 RMSE .176503254 and severe bias −.127421287; two-stage RMSE .156922972 and severe bias −.120482483. The previously completed uncertainty, ablation, oracle and stress findings remain authoritative research evidence, with the distinction between recalculated metrics and previously archived experiments explicit in the reconciliation document.

## Software and calculations

93 unit/regression/integration tests pass: 54 existing and 39 platform tests. Existing Streamlit all five role views, three filter modes, search and drill-down pass. New API actual Uvicorn startup, readiness HTTP 200 and static/OpenAPI routes were exercised; see http_startup.json. New visual/browser interaction testing is incomplete because Chromium archive download failed. No claim of browser sign-off is made.

Full shadow: 5,172 facilities; maximum PD difference 9.97e-17, maximum LGD difference 9.71e-17, zero stage mismatches. New reference EAD 2,091,914,075.83000, ECL 45,265,972.04321. Maximum facility EAD difference 0.01000, ECL difference 0.00256855. Historical generated face/EAD amounts were rounded independently; new canonical trade conversion cannot reconstruct discarded precision. The maximum one-cent EAD tolerance is tied to source precision, not a weak model acceptance threshold. Original portfolio EAD remains 2,091,914,076.05 and ECL 45,265,972.05000534.

Canonical DQ rejects missing/future/outcome/duplicate/orphan/invalid values. API denies unauthenticated and forbidden-role access. Expired/revoked keys are rejected. Different-person override approval is enforced; original ECL is retained. Model corruption/configuration failure produces a failed run. Evidence mutation and terminal-run rewrite fail in SQLite integration tests. Audit verification and SQLite backup/restore tests pass. Point-in-time history, Stage2→Stage1 policy transition and ordered ECL movement reconciliation pass.

## Controls and remaining verification

Dependency audit reported no known vulnerabilities for 65 resolved packages at scan time, archived with versions; no security certification follows. Python static undefined/unused-name checks and JavaScript syntax checks pass. PostgreSQL schema compiles; actual PostgreSQL/container execution remains unverified in this environment. Restricted DB grants, triggers, Docker and hosted PostgreSQL CI are implemented but need actual deployment evidence. New models cannot be promoted and bank-purpose runs remain BLOCKED.

## Decision

The work delivers an implemented, locally tested **reference-platform foundation**, extending the whole project beyond notebooks and flat files. It is not institution-production-complete. Model, feature, institutional-data, PostgreSQL/browser/deployment and security-qualification findings remain open in FINAL_PRODUCTION_READINESS.md and LIMITATIONS.md. No severe LGD cure, external approval, bank-grade certification or real deployment is claimed.

## Resume and final retest

A later resume lost runtime-installed dependencies and exposed a truncated historical figure and malformed development SQLite file. The dependency lock restored the environment. The intact Git image was restored after preserving the truncated copy; the damaged database was retained and a separate database initialized through migrations and canonical ingestion. No repair silently altered risk outputs. Failed pre-recovery startup logs and recovery details remain in platform_evidence.

Continued validation closed P11: invalid reconciliation input and blocked/failed runs can no longer receive a successful validation record. Whole-run hashes are checked on validated result reads using canonical ordering. The final suite passes 93 tests.

The resumed borrower CSV also failed its identity check. Frozen seed-42 regeneration reproduced SHA-256 `2312db398a92c242abec665af6e1e7535b18e47349cfaf0cdf48e8ed3f83c8cd`; the fresh database shadow replay then passed across all 5,172 facilities. The read-only frozen hash gate now checks borrower/conduct as well as workout/R2 sources.

## LGD follow-up validation — 24 September 2026

The follow-up suite passes **104 tests**. The 5,172-facility shadow replay
retains the previous predictions and reconciliation bounds. Infinite/incomplete
LGD outputs now fail explicitly before clipping or persistence.

[LGD_REMEDIATION_REPORT.md](LGD_REMEDIATION_REPORT.md) adds a new conditional-mean
diagnostic: simulated expected LGD has -12.5017 pp realized >75% bias compared
with V5 -12.7421 pp. This changes the root-cause interpretation, not the production
gate. Prediction-time calibration, support and unavailable features remain open.
Historical validation and adverse findings above are preserved.

## S1 dataset release — 25 September 2026

New linked synthetic data and its predeclared comparisons are complete: see
[synthetic_bank/README.md](synthetic_bank/README.md). 107 tests pass; 8,695 current
facilities run through the reference platform with independent EAD/ECL reconciliation.
Consistent synthetic guarantee support is demonstrated; old model support is not
retrospectively fixed. Enhanced LGD RMSE improves but severe-loss bias worsens on
the new final population. No candidate promoted; institutional production remains
BLOCKED. Historical metrics above remain evidence for their original populations.

## Final LGD disposition — 25 September 2026

See [LGD_FINAL_RESOLUTION.md](LGD_FINAL_RESOLUTION.md). Category **3 — MODEL DEFECT
REMAINS**, specifically current-population conditional calibration/transfer. The
realized-tail diagnostic interpretation is corrected: actual governed final severe
bias -12.1078 pp = +2.4830 pp model component -14.5908 pp realization component.
Current governed conditional bias remains -12.65 pp, linked to omitted known
context and regime shift. 111 tests pass; no promotion or institutional gate waiver.
