# Limitations and blocked gates

> Final red-team review: see [CURRENT_SYSTEM_STATE.md](CURRENT_SYSTEM_STATE.md), [FINAL_RED_TEAM_REPORT.md](FINAL_RED_TEAM_REPORT.md), and [FINAL_RELEASE_READINESS.md](FINAL_RELEASE_READINESS.md). Historical results below retain their original scope. No model promotion, methodological change, or dataset regeneration occurred in this review.

Latest hardening (28 September): **no new final validation was opened**. R1's
results remain unchanged after a continuous calibration worsened key errors and
was rejected. Imported S1 latent quality shifts remain in S2 recovery targets;
validated prediction-time capture/derivation is absent. Explicit domain, OOD and
capture controls improve safety but do not constitute model remediation or
approval. See `lgd_hardening/DECISION.md`; 168 local tests pass.

## Latest S2-R1 residual limitations

The constrained successor removes scenario reversals but is **not promoted**.
Current downside uncertainty exceeds the frozen equivalence bound; full-guarantee
fresh baseline and partial-guarantee current downside fail their bounds. The
high predicted-LGD band remains overcalibrated. Fresh downside economic support
rejects 327/6,000 facilities despite complete coverage of the known current
scenario set. `s2_remediation/DECISION.md` separates these statistical, data and
model limitations. Unsupported scoring is explicitly blocked. Hidden quality
composition differs between populations and is not a deployable input. Synthetic
truth and seven current economic clusters do not establish bank suitability.

## Data and synthetic evidence

All borrower, facility, default and recovery data are generated. No institution feed, legal security assessment, independently observed recovery vintage or multi-currency portfolio has been qualified. The canonical monetary unit is the single synthetic unit of the source portfolio. Institutions require explicit currency mapping/FX policy before aggregate use. A local research development CSV was truncated; the original workspace is preserved, and this branch uses the intact committed hash.

## Methodology and model risk

Frozen V5 logistic PD and GB LGD remain reference models. The nine-month EWS/watchlist condition remains internal policy. Stage 2 retains the existing constant-hazard lifetime approximation on weighted forward PD. Scenario coefficients are synthetic assumptions, not estimated macroeconomic relationships. No new method, risk driver or champion was promoted.

R2 improves overall error but does not demonstrate resolution of severe-loss risk. Two-stage final RMSE .156923; realized >75% bias −.120482 across 536 cases. The paired severe-bias difference interval includes zero. Quality inputs are absent in current scoring. Oracle future information is prohibited. Institutional use of all reference models remains BLOCKED.

## Validation

Independent arithmetic, held-out research recalculation, regression tests and reference shadow runs concern synthetic data. They do not constitute an external independent validation opinion or regulator approval. Baseline bootstrap and research stress tables were inspected; no new candidate was tuned. EAD forecast validation against observed defaults remains unavailable. New live outcome validation reports selected resolved cases and coverage; it does not infer missing outcomes are good loans.

## Software and operations

The consolidated release has now been qualified on fresh GitHub-hosted runners with PostgreSQL 16 migrations, the full 5,172-facility shadow calculation, audit verification, WN-1 PostgreSQL persistence, Streamlit headless startup and Docker image build. These checks establish reproducible reference-platform execution; they are not evidence of a production deployment.

Full Docker Compose service-lifecycle/restore testing, production backup/RPO/RTO, sustained concurrency/load/SLA testing and external observability/alert delivery remain outside the demonstrated scope. SQLite remains the local development/reference path. Destructive Alembic downgrade is prohibited. Finalized evidence has database mutation guards, but a database owner can still defeat database-local protections; audit hashes are not external WORM storage. Crash recovery remains operator-controlled.

## Security

High-entropy credentials are provisioned by a trusted local operator, expire, can be revoked and are hashed at rest. Backend permissions are enforced. This is a single institutional scope, not multi-tenant isolation. No SSO, MFA, external secret vault, independent penetration test, TLS termination, perimeter rate limits or security operations integration was validated here. Local composition binds only loopback. Do not expose it publicly as a production service.

## Interface and product

The API serves a credential-authenticated workflow interface and the repository retains the richer Streamlit research workbench. Hosted CI now verifies Streamlit headless startup, and the workbench has been exercised during local integration/testing. The earlier Chromium-download failure remains historical evidence; there is still no comprehensive automated cross-browser/layout qualification.

The Streamlit identity selector is deliberately a demo RBAC surface rather than real authentication. Do not expose the research workbench with confidential data or treat it as a production identity boundary.

## Longitudinal and external data scope

Multiple dated snapshots, point-in-time reads, stage migration and ECL movements are implemented. Existing 36-month conduct and recovery generators are preserved. No new correlated financial-statement/default/recovery lifecycle generator was scientifically justified in this release; synthetic transition fixtures are software tests, not empirical transition calibration. No external macro feed, paid data, Scite, Exa, Supabase, Datadog or PostHog integration was fabricated. Scenario ingestion remains the frozen governed CSV, snapshot into each run. Expanded simulation and live integrations remain roadmap work tied to evidence and actual infrastructure.

### LGD diagnostic update

See LGD_REMEDIATION_REPORT.md. The conditional expected loss under the frozen R2
simulator still has -12.5017 pp bias among realized >75% cases, demonstrating that
zero retrospective severe-cohort bias is not a valid sole expected-loss target.
This does not close prediction-time calibration, live-support or unavailable-input
findings. The diagnostic is synthetic, retrospective and non-deployable.

### Final LGD interpretation and current transfer

See LGD_FINAL_RESOLUTION.md. Realized-tail bias alone is not proof of expected-LGD
underestimation. The separate S1 current conditional bias is real under the synthetic
DGP and concentrated in omitted downturn context. Full-information simulator
expectations are not a deployable oracle and do not validate real-bank applicability.
Borrower-cluster intervals do not span arbitrary sector-regime histories; existing
final data cannot be reused as an untouched promotion population.

### Downturn operational identification

Calibration with hidden S1 state reduces the shortfall, but canonical predictors
do not identify its arbitrary current sector assignment. Blanket stressed LGD
materially overstates normal outcomes. See LGD_DOWNTURN_FINAL_DECISION.md; a
sensitivity control is not a booked MoC, IFRS9 allowance or production approval.

## GenAI Copilot limitations

The default Copilot is a deterministic grounded reference provider, not evidence of general language-model quality. Retrieval is intentionally limited to stored run outputs and selected authoritative model-risk evidence. The present platform has a shared institutional access scope and no row-level tenant/portfolio entitlements. Prompt-injection pattern filtering reduces common attacks but is not a substitute for an institutional adversarial assessment. External LLM transmission is disabled by default and remains unqualified for confidential data, privacy, retention, vendor, security and residency requirements. Generated narratives require human review and cannot approve credit decisions.
# S2 successor limitations

See `economic_lgd/DECISION.md`: scenario extrapolation and -2.32 pp downside bias,
78 facility ordering exceptions, +4.65 pp final full-guarantee bias, limited macro
clusters, hypothetical rather than observed-default workouts and assumed economic
elasticities. Improved S2 aggregate calibration cannot repair historical S1
evidence or establish bank approval. No challenger promoted and no MoC applied.

## WN-1 final research limitations
See `workout_vnext/FINDINGS.md`. Calibration, support, scenario reversals, unresolved-selection bias and institutional source capture block promotion. Security features do not fully deplete after payouts. No empirical-bank validation or bank approval is claimed.
