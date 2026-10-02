# Final independent red-team review and release qualification

Review dates: 1–2 October 2026. Starting SHA:
`33d3ad4670bd7c5cfad31ac5d6b54f8f42224180`.
Review branch: `review/final-red-team-release`.
Protocol committed as `6c7b1a1` before remediation; reproduced fixes checkpoint
`204c6c5`. The release SHA is the final commit containing this report and is
reported with the verified bundle; `git rev-parse HEAD` identifies it exactly.

## Disposition

Local synthetic single-workspace reference use: **PASS WITH LIMITATIONS**.
Full deployment qualification: **PARTIAL**. Institutional production: **BLOCKED**.
This is an independent arithmetic/adversarial implementation review, not an
independent institutional validation team or regulatory certification. The review
makes no claim to have proven every possible defect absent.

## Baseline and actual changes

The clean starting tree and checkpoint SHA were verified. All pre-existing branch
refs remain unchanged. The separate research worktree was not edited. Original
V5, R2, S1, S2, S2-R1, datasets, predictions, artifacts and adverse decisions remain
unchanged. The protocol, successive commits, evidence and source manifest make the
new work independently reviewable.

Eight remediation groups are recorded in `FINAL_RED_TEAM_FINDINGS.md`: stale schema
lineage; incomplete decision integrity checking; unknown-run Copilot audit failure;
boolean-to-numeric coercion; unsupported Copilot-action refusal gaps; missing branch
CI coverage; missing V5 workflow dependencies/artifact preparation; and Docker context
exclusions. Five initial regression failures and six further control failures were
captured before fixes. The complete suite grew from **168 to 186 passing tests**;
zero failures/skips, one upstream Starlette/httpx deprecation warning. Existing
tests and acceptance thresholds were retained. Negative-test logs redact disposable
test credentials; those credentials belonged only to removed temporary test databases.

No model was trained or promoted. No methodological formula, risk driver, target,
scenario assumption, CCF, staging rule, model gate, or dataset was changed. No new
independent final population was generated or opened. No algorithm sweep was justified:
the retained evidence still fails data/feature/domain/calibration requirements.

## Independent calculation evidence

`python scripts/final_red_team_verify.py` reads known historical outputs, verifies
R1 frozen hashes, recalculates metrics directly, migrates an isolated SQLite database,
and executes the active reference pipeline. Arithmetic uses independently written
scalar rules rather than calling the production EAD/stage/scenario/ECL functions.
Predicted LGD and base model PD remain supplied model outputs; the review does not
pretend to independently reconstruct trained estimators from first principles.

- 5,172 reference facilities: EAD maximum difference **0**; scenario-weighted PD
  maximum difference **1.1102e-16**; ECL maximum difference **7.2760e-11**.
- Independently reconstructed staging and ratings: **zero mismatches**.
- Boundaries 0/29/30/31/89/90/91 DPD pass. Prior tests retain zero exposure,
  zero/total loss, full cash/guarantee, persistence, cure, malformed data,
  missing/corrupt artifacts, blocked bank runs and two-person override coverage.
- PD: **3,000** reference observations, **102** defaults, observed rate **3.40%**,
  mean prediction **3.4388%**, AUC **0.759455**, Gini **0.518911**, KS **0.408497**,
  Brier **0.030003**, log loss **0.128562**. These independently recalculated values
  match the historical evidence for this population.
- R1 scenario shadow ECL: **92,036,058.41877422 currency units**; independent
  weighting error **1.1642e-10**; borrower-to-portfolio difference **0**. This is
  an unbooked challenger comparison, not the active reference portfolio.
- The first draft independent verifier used Python `round(x,2)` for trade EAD;
  this differs at binary half-cent ties from the established NumPy scaling/rounding
  implementation. The verifier now independently performs round(x*100)/100. No
  production calculation or tolerance was changed to conceal that discrepancy.

Full numeric evidence, run/data/model/configuration identities and worked cases are
in `final_red_team_evidence/independent_verification.json` and `worked_cases.json`.
The reported currency is deliberately unspecified; no EUR accounting claim is made.

## LGD interpretation and remaining gates

`lgd_independent_metrics.csv` recalculates current and retired promotion observations
by scenario/model, full-guarantee segment, high prediction band and realized >75%
tail. This uses known engineering evidence and is not labelled fresh validation.

Retained R1 retired-promotion baseline MAE/RMSE/realized bias remain approximately
**12.27/16.40/+0.29 pp**, with conditional bias **+0.24 pp**. Current aggregate
conditional bias is **+0.10 pp**. Scenario reversals remain zero in frozen tests.
However current downside equivalence bound **1.15 pp** exceeds **1 pp**; full-guarantee
bound **2.06 pp** exceeds **2 pp**; high predicted 80–100% band conditional bias is
**+3.62 pp current / +2.63 pp retired promotion**; and **327/6,000** retired promotion
downside observations violate development support. These findings remain OPEN.

The realized >75% cohort is selected on the outcome and therefore cannot alone
validate a conditional mean. Its adverse realized bias remains reported alongside
conditional bias, prediction bands, population transfer and feature availability.
Missing validated reporting-time recovery-quality information and few independent
economic clusters are real evidence gaps. More replicated rows cannot provide
independent economic information. Simulator quality/oracle states remain excluded.
The rejected continuous calibration remains rejected and R1 remains
`CHALLENGER_NOT_PROMOTED`; there is no booked adjustment.

## Database, API, UI, security and GenAI

The actual local HTTP server returned READY; UI/static/OpenAPI resources returned
200 and unauthenticated runs returned 401. SQLite migration, immutable evidence,
backup/restore, expired/revoked credentials and RBAC tests pass. Decision projections
are now checked against hashed traces before listed/detail/Copilot reads. This
adds O(portfolio-size) integrity work to a decision view; large-scale latency/SLA
qualification remains open. Append-only tables and two-person approval are retained.

The API is explicitly a shared single workspace. User roles are permission controls,
not tenant boundaries. Per-user/portfolio partitioning was not invented or claimed.
The five supplied adversarial Copilot requests now return REFUSED with no tool calls.
Unknown runs return audited insufficient evidence. Numerical grounding, allowlisted
retrieval, default-disabled external provider and model-gate explanations pass tests.
The regex refusal layer is finite; safety also relies on deterministic rendering and
absence of SQL/scoring/approval tools. External LLM output remains unqualified.

Real-browser QA was attempted through a local Playwright install (invalid/truncated
browser archive) and the cloud browser (localhost blocked with
`net::ERR_BLOCKED_BY_CLIENT`). Neither is a passed rendered-UI test. HTTP success
is not substituted for browser evidence. No fresh dependency vulnerability scan,
load/concurrency certification, external IAM/TLS or penetration test is claimed.

## Hosted versus local deployment evidence

Newly retrieved GitHub baseline evidence supersedes older statements that no hosted
run existed. At exact SHA 33d3ad4, platform run **36838731071** passed on 1 October,
including PostgreSQL migrations, full shadow calculation, audit verification and
Docker build. It does not prove final-branch Compose runtime or PostgreSQL restore.
V5 run **36838731545**, job **110292375714**, failed during test collection with
missing `pydantic` / `alembic`. The review fixes the full locked dependencies and
prepares reference artifacts before running all tests. No tests were removed.
Final-candidate hosted CI must still be verified after publication.

Local PostgreSQL tools and Docker are absent; attempted package installation could
not locate PostgreSQL. Exact commands/errors are retained in environment evidence.
Baseline hosted success and these local environment limitations are compatible.

## Reproduction

On a fresh checkout (Python 3.12), use a NEW local environment:

```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-platform-lock.txt
python scripts/run_v5.py
python -m credit_platform.cli build-models
python -m pytest -q
python scripts/final_red_team_verify.py
python scripts/final_red_team_http.py
```

The first two build commands reproduce ignored V5 inputs/artifacts on clean clones;
they are not new model research or permission to overwrite frozen historical evidence.
The review itself reused already-built reference artifacts and generated no dataset.
The two final review scripts write only the new review evidence directory and
isolated temporary databases. For interactive reference API/UI:

```bash
python -m alembic upgrade head
python -m credit_platform.cli issue-token --name local-reviewer --role analyst
python -m uvicorn credit_platform.api:app --host 127.0.0.1 --port 8000
```

Enter the locally issued token only into the local UI. Never commit it. Use the
canonical upload workflow or the documented reference CLI mapping to populate data.
See `DEPLOYMENT_OPERATIONS.md` for owner/application role separation and recovery;
external acceptance tasks are explicit in `FINAL_RELEASE_READINESS.md`.

## Release identity and transport

The final source/evidence manifest records hashes; `changed_files.txt` lists all
changes from the exact baseline. Final Git status and bundle verification are
reported at delivery. Only this review branch may be pushed; no merge or force push.
If command-line authentication is unavailable, the complete Git bundle preserves
all reachable refs and history for manual transport. Uncommitted/ignored runtime
files and the separate research worktree modification are not Git-bundle contents.
