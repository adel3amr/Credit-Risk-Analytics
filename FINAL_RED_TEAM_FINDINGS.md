# Final red-team findings register

Categories: A code-fixable; B governed methodology; C unavailable data; D external/institutional qualification. Historical findings remain in their original registers.

## RT-01 — Run lineage

- **Description:** Runs recorded schema 0001 while the migrated service requires 0002.
- **Evidence:** test_run_records_actual_schema
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Hard-coded stale schema label.
- **Severity:** Moderate
- **Classification:** DATA LINEAGE
- **Remediation Category:** A
- **Remediation Status:** CLOSED
- **Files Affected:** credit_platform/service.py
- **Tests Added:** test_run_records_actual_schema
- **Remediation:** Schema checked before execution and recorded as 0002.
- **Residual Risk:** Future migrations must update the supported schema explicitly.
- **Final Disposition:** CLOSED

## RT-02 — Decision integrity

- **Description:** Decision listing, drill-down and borrower Copilot could report corrupted scalar projections despite trace hashes.
- **Evidence:** test_decision_views_reject_corrupted_projection
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Integrity checks applied to portfolio traces but not all decision reads; scalar fields were not compared to trace.
- **Severity:** High
- **Classification:** BUG / SECURITY
- **Remediation Category:** A
- **Remediation Status:** CLOSED
- **Files Affected:** credit_platform/service.py; credit_platform/api.py; credit_platform/copilot.py
- **Tests Added:** test_decision_views_reject_corrupted_projection
- **Remediation:** Verified decision-row helper checks trace hash, scalar projections and full run output hash before those reads.
- **Residual Risk:** Trusted DB administrators can rewrite storage and hashes; history and other administrative views still need external integrity anchoring.
- **Final Disposition:** CLOSED

## RT-03 — Copilot audit

- **Description:** Unknown run requests produced a foreign-key conflict while persisting insufficient-evidence responses.
- **Evidence:** test_unknown_run_copilot_is_audited_without_fk_error
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** A nonexistent requested run ID was copied into a foreign-key column.
- **Severity:** Moderate
- **Classification:** GENAI / DATABASE
- **Remediation Category:** A
- **Remediation Status:** CLOSED
- **Files Affected:** credit_platform/copilot.py
- **Tests Added:** test_unknown_run_copilot_is_audited_without_fk_error
- **Remediation:** Return insufficient evidence and persist a nullable run link.
- **Residual Risk:** Question hash retained; no arbitrary rejected payload stored.
- **Final Disposition:** CLOSED

## RT-04 — Input contract

- **Description:** Boolean borrower features were coerced to floats before numeric contract validation.
- **Evidence:** test_boolean_feature_is_not_silently_coerced
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Pydantic post-validation hid original JSON boolean types.
- **Severity:** Moderate
- **Classification:** DATA / BUG
- **Remediation Category:** A
- **Remediation Status:** CLOSED
- **Files Affected:** credit_platform/domain.py; credit_platform/contracts.py
- **Tests Added:** test_boolean_feature_is_not_silently_coerced
- **Remediation:** Validate mapping and numeric values before coercion.
- **Residual Risk:** Source truth and institutional feature availability cannot be proven by types.
- **Final Disposition:** CLOSED

## RT-05 — Copilot intent controls

- **Description:** Forbidden action requests received ANSWERED explanations instead of explicit refusal. No action was executed.
- **Evidence:** test_copilot_prohibited_actions_are_refused (5 cases)
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Refusal patterns missed supplied red-team instructions.
- **Severity:** Moderate
- **Classification:** GENAI
- **Remediation Category:** A
- **Remediation Status:** CLOSED for tested prompts
- **Files Affected:** credit_platform/copilot.py
- **Tests Added:** test_copilot_prohibited_actions_are_refused (5 cases)
- **Remediation:** Versioned refusal rules reject booking, SQL, approval and cross-user prompts with no tool calls.
- **Residual Risk:** Finite patterns are not a general prompt-injection guarantee; deterministic capability separation remains essential.
- **Final Disposition:** CLOSED for tested prompts

## RT-06 — CI coverage

- **Description:** Platform workflow did not trigger on the checkpoint/review branch.
- **Evidence:** Source trigger inspection
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Push branch filter covered platform/** only.
- **Severity:** Moderate
- **Classification:** DEPLOYMENT
- **Remediation Category:** A
- **Remediation Status:** FIXED; hosted final rerun pending
- **Files Affected:** .github/workflows/platform.yml
- **Tests Added:** Source trigger inspection
- **Remediation:** Added explicit checkpoint/review branch filters.
- **Residual Risk:** Final commit hosted CI not yet verified.
- **Final Disposition:** FIXED; hosted final rerun pending

## RT-07 — V5 CI

- **Description:** Hosted regression collection failed with missing pydantic and alembic. Platform artifacts were also not prepared before full-suite tests.
- **Evidence:** Hosted run 36838731545 / job 110292375714; full local suite
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** V5-only dependency installation while collecting the expanded platform suite.
- **Severity:** High
- **Classification:** INTEGRATION / DEPLOYMENT
- **Remediation Category:** A
- **Remediation Status:** FIXED; hosted final rerun pending
- **Files Affected:** .github/workflows/validate-hybrid-v2.yml
- **Tests Added:** Hosted run 36838731545 / job 110292375714; full local suite
- **Remediation:** Install full locked requirements and build trusted reference artifacts after the original pipeline and before the unchanged full test suite.
- **Residual Risk:** No hosted pass claimed for this patch.
- **Final Disposition:** FIXED; hosted final rerun pending

## RT-08 — Container context

- **Description:** COPY . could include local virtual environments and tool caches.
- **Evidence:** Dockerfile/.dockerignore inspection
- **Reproducibility:** Run tests/platform/test_red_team.py and inspect referenced evidence/source; hosted IDs identify original failure
- **Root Cause:** Incomplete Docker context exclusions.
- **Severity:** Low
- **Classification:** CODE QUALITY / DEPLOYMENT
- **Remediation Category:** A
- **Remediation Status:** CLOSED
- **Files Affected:** .dockerignore
- **Tests Added:** Dockerfile/.dockerignore inspection
- **Remediation:** Exclude .venv, venv and .ruff_cache.
- **Residual Risk:** Final container build still requires execution.
- **Final Disposition:** CLOSED

## RT-09 — LGD R1

- **Description:** R1 fails predicted-band calibration, scenario/guarantee uncertainty and release-domain support.
- **Evidence:** Frozen regression checks; final_red_team_evidence/lgd_independent_metrics.csv
- **Reproducibility:** See cited frozen reports and recorded execution attempts
- **Root Cause:** Unvalidated population transfer of recovery heterogeneity, conditional calibration error and limited independent economic clusters.
- **Severity:** High
- **Classification:** MODEL / VALIDATION
- **Remediation Category:** B/C
- **Remediation Status:** OPEN; PROMOTION BLOCKED
- **Files Affected:** s2_remediation/DECISION.md; lgd_hardening/DECISION.md
- **Tests Added:** Frozen regression checks; final_red_team_evidence/lgd_independent_metrics.csv
- **Remediation:** Preserve rejection and domain checks; no further tuning or new final opening.
- **Residual Risk:** Recovery capture/derivation evidence or governed new methodology and independent validation required.
- **Final Disposition:** OPEN; PROMOTION BLOCKED

## RT-10 — Deployment qualification

- **Description:** Final PostgreSQL restore, Compose runtime and real-browser workflows are unqualified here.
- **Evidence:** Real HTTP passed; baseline hosted PostgreSQL/shadow and Docker build passed
- **Reproducibility:** See cited frozen reports and recorded execution attempts
- **Root Cause:** Local tools missing; browser download invalid; cloud browser blocked localhost.
- **Severity:** High for institutional use
- **Classification:** INSTITUTIONAL / EXTERNAL EVIDENCE
- **Remediation Category:** D
- **Remediation Status:** OPEN
- **Files Affected:** final_red_team_evidence/environment_attempts.json; hosted_baseline_ci.json
- **Tests Added:** Real HTTP passed; baseline hosted PostgreSQL/shadow and Docker build passed
- **Remediation:** Separate baseline hosted success from unexecuted final release checks.
- **Residual Risk:** Requires representative deployment and final-SHA CI.
- **Final Disposition:** OPEN

## RT-11 — External GenAI

- **Description:** Opt-in external provider responses have no demonstrated grounding/approval-language enforcement equivalent to deterministic provider.
- **Evidence:** Source review and default-disabled provider test
- **Reproducibility:** See cited frozen reports and recorded execution attempts
- **Root Cause:** External text returned without independently qualified output validation.
- **Severity:** High for external deployment
- **Classification:** GENAI / SECURITY
- **Remediation Category:** D
- **Remediation Status:** OPEN; DISABLED BY DEFAULT
- **Files Affected:** credit_platform/copilot.py; GENAI_RISK_AND_CONTROLS.md
- **Tests Added:** Source review and default-disabled provider test
- **Remediation:** Do not qualify or enable for sensitive production use.
- **Residual Risk:** Provider privacy, security, adversarial output and numerical grounding validation required.
- **Final Disposition:** OPEN; DISABLED BY DEFAULT

## RT-12 — Access scope

- **Description:** Read permissions cover the shared workspace; no per-user/tenant ownership isolation exists.
- **Evidence:** Existing RBAC/expiry/revocation tests; source review
- **Reproducibility:** See cited frozen reports and recorded execution attempts
- **Root Cause:** Single-workspace architecture is explicit in SECURITY_REVIEW.md.
- **Severity:** High for multi-tenant use
- **Classification:** SECURITY / INSTITUTIONAL
- **Remediation Category:** D
- **Remediation Status:** OPEN for multi-tenant use
- **Files Affected:** credit_platform/security.py; SECURITY_REVIEW.md
- **Tests Added:** Existing RBAC/expiry/revocation tests; source review
- **Remediation:** Limit release to synthetic single workspace; no false claim that refusal patterns enforce tenancy.
- **Residual Risk:** Institutional access partitioning, IAM/MFA/TLS, penetration tests and external audit anchoring required.
- **Final Disposition:** OPEN for multi-tenant use

## RT-13 — Validation completeness

- **Description:** This review does not demonstrate exhaustive concurrency, load, external LLM or browser behavior.
- **Evidence:** Explicit coverage and environment records
- **Reproducibility:** See cited frozen reports and recorded execution attempts
- **Root Cause:** Local automated review is bounded; no independent institutional team.
- **Severity:** Moderate
- **Classification:** VALIDATION
- **Remediation Category:** D
- **Remediation Status:** OPEN
- **Files Affected:** FINAL_RELEASE_READINESS.md
- **Tests Added:** Explicit coverage and environment records
- **Remediation:** Qualified PASS WITH LIMITATIONS only for tested reference use.
- **Residual Risk:** Passing tests are not proof of total correctness or bank approval.
- **Final Disposition:** OPEN
