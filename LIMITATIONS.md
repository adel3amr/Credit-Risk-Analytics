# Limitations and blocked gates

## Data and synthetic evidence

All borrower, facility, default and recovery data are generated. No institution feed, legal security assessment, independently observed recovery vintage or multi-currency portfolio has been qualified. The canonical monetary unit is the single synthetic unit of the source portfolio. Institutions require explicit currency mapping/FX policy before aggregate use. A local research development CSV was truncated; the original workspace is preserved, and this branch uses the intact committed hash.

## Methodology and model risk

Frozen V5 logistic PD and GB LGD remain reference models. The nine-month EWS/watchlist condition remains internal policy. Stage 2 retains the existing constant-hazard lifetime approximation on weighted forward PD. Scenario coefficients are synthetic assumptions, not estimated macroeconomic relationships. No new method, risk driver or champion was promoted.

R2 improves overall error but does not demonstrate resolution of severe-loss risk. Two-stage final RMSE .156923; realized >75% bias −.120482 across 536 cases. The paired severe-bias difference interval includes zero. Quality inputs are absent in current scoring. Oracle future information is prohibited. Institutional use of all reference models remains BLOCKED.

## Validation

Independent arithmetic, held-out research recalculation, regression tests and reference shadow runs concern synthetic data. They do not constitute an external independent validation opinion or regulator approval. Baseline bootstrap and research stress tables were inspected; no new candidate was tuned. EAD forecast validation against observed defaults remains unavailable. New live outcome validation reports selected resolved cases and coverage; it does not infer missing outcomes are good loans.

## Software and operations

PostgreSQL-compatible schema, migrations, least-privilege grants, Docker composition and CI job are implemented. Local PostgreSQL execution could not be completed: system package setup lacks required privileges and packaged PostgreSQL cannot create its non-root runtime user. Docker is unavailable in this workspace. Hosted platform CI has not been run. These are operational verification gates, not successful deployments.

SQLite tests and backup/restore checks are development evidence only. Migration 0001 is an additive initial schema, with a frozen schema snapshot. Destructive downgrade is prohibited. Finalized evidence has database mutation guards. A database owner can still defeat these protections; audit hashes are not external WORM storage. Crash during a run may leave RUNNING state; operator recovery is required, and a new request key creates a replacement run without modifying the old result.

## Security

High-entropy credentials are provisioned by a trusted local operator, expire, can be revoked and are hashed at rest. Backend permissions are enforced. This is a single institutional scope, not multi-tenant isolation. No SSO, MFA, external secret vault, independent penetration test, TLS termination, perimeter rate limits or security operations integration was validated here. Local composition binds only loopback. Do not expose it publicly as a production service.

## Interface and product

The API serves a workflow UI with credential authentication, role-aware actions, portfolio, datasets, registry, findings, validation and decision detail. Static assets and API contracts were tested. Chromium download returned a truncated archive, so new browser interaction/layout verification remains incomplete. Existing Streamlit demonstration is retained and has no real authentication. Do not deploy that legacy app with confidential data.

## Longitudinal and external data scope

Multiple dated snapshots, point-in-time reads, stage migration and ECL movements are implemented. Existing 36-month conduct and recovery generators are preserved. No new correlated financial-statement/default/recovery lifecycle generator was scientifically justified in this release; synthetic transition fixtures are software tests, not empirical transition calibration. No external macro feed, paid data, Scite, Exa, Supabase, Datadog or PostHog integration was fabricated. Scenario ingestion remains the frozen governed CSV, snapshot into each run. Expanded simulation and live integrations remain roadmap work tied to evidence and actual infrastructure.

### LGD diagnostic update

See LGD_REMEDIATION_REPORT.md. The conditional expected loss under the frozen R2
simulator still has -12.5017 pp bias among realized >75% cases, demonstrating that
zero retrospective severe-cohort bias is not a valid sole expected-loss target.
This does not close prediction-time calibration, live-support or unavailable-input
findings. The diagnostic is synthetic, retrospective and non-deployable.
