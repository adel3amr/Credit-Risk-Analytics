# From Credit Models to a Governed Credit Risk Reference Platform

## Abstract

This project studies the engineering boundary between predictive credit models and a traceable credit decisioning system. An existing synthetic SME PD, facility LGD and IFRS 9-style reference implementation was reconstructed across its historical releases and extended with canonical dated inputs, persistent calculation records, backend authorization, model and configuration identities, independent reconciliation, controlled overrides and operational interfaces. The latest completed LGD programme was consumed as evidence rather than repeated. A two-stage research model improved aggregate error on a frozen synthetic final sample but retained severe-loss underprediction and depended on unavailable current-scoring information. Consequently, the platform retains reference-only models and blocks institutional production use. Local tests demonstrate calculation fidelity and software controls; unavailable PostgreSQL/container and browser qualification remain explicit limitations.

## 1. Purpose and system evolution

The system began as a borrower PD/ECL analytical prototype and evolved through monitoring, score/rating, collateral, trade exposure and facility recovery components. V4/V5 introduced separate resolved-workout LGD development and facility ECL aggregation. Frozen V5 is identified by commit `0dfe4c8`; subsequent independent validation and research culminated in `ae9942a`. Historical reconstruction, adverse findings and failed challengers remain preserved under `validation_review/` and `lgd_research/`.

This platform release began by reproducing current repository evidence. Baseline reconciliation was committed before architecture implementation. It did not treat prompt metrics or prior completion narratives as authoritative when current files differed. In particular, a local development CSV was truncated while its committed version remained intact. A separate worktree preserved historical evidence and used verified committed bytes.

## 2. Credit risk framework and policy boundaries

The reference chain is borrower/facility information → PD → conduct EWS → SICR/staging → LGD/EAD → scenario-adjusted ECL → portfolio analytics → validation and governance. These components have separate purposes. A watchlist classification is not identical to SICR, Stage 2 or default. The existing nine-month persistence treatment is explicitly internal project policy, not a regulatory attribution.

The platform preserves these source-defined methods. No challenger, tail uplift, conservative quantile, altered scenario elasticity or revised stage rule was silently substituted. Institution policy suitability and accounting compliance remain separate from faithful software implementation.

## 3. Architecture

A modular monolith adds canonical data admission, SQLAlchemy persistence, risk adapters, service transactions, FastAPI endpoints and a static authenticated workflow UI. The original demonstration remains runnable for historical reproduction. No distributed queue, microservice network or Kubernetes architecture was justified by measured workload.

Data ingestion does not require the risk engine to know whether a validated canonical snapshot originated in a simulator or a future institutional mapping. Model artifacts, policy/scenario content, source datasets and application source identities accompany calculation runs. Architecture and implementation decisions are recorded under `docs/adr/`.

## 4. Canonical data and point-in-time history

A dataset has a business-effective date and a separate system-recorded timestamp. Borrowers and facilities are immutable snapshot records linked by composite dataset/entity keys. Source-observation dates cannot exceed the reporting date. Corrections create new snapshots instead of rewriting historical inputs.

Facility security and guarantee terms remain explicit snapshot attributes. Dedicated legal-security, guarantor, valuation and workout ledgers are not claimed to exist. Their required institutional capture is documented separately. Model feature contracts distinguish synthetic current availability from actual production availability. Future recovery or default information is excluded from scoring inputs.

Point-in-time queries constrain both reporting date and knowledge time. Stage migrations and ECL movement calculations compare retained runs. This provides historical reconstruction; it does not by itself supply a calibrated longitudinal banking simulator.

## 5. Synthetic portfolio and economic assumptions

The preserved SME generator produces 12,000 borrowers and a 36-month conduct panel. The original workout generator produces 8,000 resolved synthetic facilities. R2 research adds a separate economic recovery process with collateral, guarantee, unsecured and cure recoveries, costs, timing, discounting and irreducible future shocks.

These are transparent generated populations, not empirical bank observations. R2 development, selection, final and stress datasets have fixed seeds, sizes and hashes. Data-generation formulas were not altered during platform work to obtain favorable metrics. No new macro/credit correlation process was invented merely to fill an architecture diagram.

## 6. PD and rating

The governed PD model remains logistic regression with its existing imputation/scaling and approved numeric, qualitative and industry inputs. Its 9,000/3,000 stratified development/holdout split uses the original seed. Independent holdout results reproduce AUC 0.759455473, Gini 0.518910946, KS 0.408496732, Brier score 0.030002535 and log loss 0.128562115, with 102 defaults in 3,000 observations.

PD-based score/performing grades remain separate from operational watchlist and default severity. Full recognized cash coverage can affect the internal rating only where the existing policy permits; it cannot cure a Stage 2 or Stage 3 classification. No empirical institution calibration or long-run/through-the-cycle reinterpretation is asserted.

## 7. EWS, watchlist and staging

EWS retains its three utilization/conduct signals. Stage 3 follows reporting impairment or the source-defined arrears condition; Stage 2 follows the frozen observable deterioration conditions, including persistent EWS. Trigger-level explanations are retained with the result rather than reconstructed from a label alone.

Independent baseline checks found no staging or EWS mismatches. The original 3,000-borrower population contains 2,769 Stage 1, 221 Stage 2 and 10 Stage 3 borrowers, with 287 Rating-7 watchlist classifications. These are borrower counts, not facility counts. Boundary tests exercise eight versus nine months, default precedence and current-condition Stage 2→Stage 1 behavior. Such tests demonstrate policy execution, not empirical transition probabilities.

## 8. LGD findings and research disposition

The frozen facility Gradient Boosting LGD model has 2,000-case historical holdout MAE 0.113964529, RMSE 0.165798487 and mean prediction-minus-realization error −0.003051719. The 327 realized LGDs above 75% have bias −0.155927834. Aggregate near-zero bias therefore does not establish uniformly accurate forecasts.

The later programme identified development/current support mismatch: zero guarantee support is common among current facilities and almost absent in original development. Matched-input refitting did not eliminate severe-loss error. R2 then examined a controlled data/model comparison, ablations, quality inputs, component and two-stage models, robust objectives, quantiles, an explicitly non-deployable oracle and stress scenarios.

On the same 3,000-case R2 final sample, the historical V5 benchmark has RMSE 0.176503254 and the enhanced two-stage model 0.156922972. Among 536 realized LGDs above 75%, their respective biases are −0.127421287 and −0.120482483. The archived paired confidence interval for the severe-bias difference includes zero. The quality inputs used by the research challenger are unavailable in the current scoring population. No promotion follows.

Retrospective outcome-selected tail cohorts and forecast-selected risk cohorts answer different questions. Future cure, recovery realization and timing can help an oracle while being unavailable at scoring. The platform neither uses future information operationally nor presents a conservative quantile as unbiased expected LGD. These limitations remain model-risk findings.

## 9. EAD and scenario-adjusted ECL

Term exposure uses drawn balance, OVD exposure uses the existing limit proxy, and trade exposure applies the frozen product CCF. Canonical trade conversion is rounded to cents. Historical face and converted-EAD fields were independently rounded at generation, so a one-cent facility difference may remain when reconstructing converted exposure from stored face amounts. That bound is disclosed rather than hidden by a numerical adjustment.

The scenario subsystem snapshots the existing CSV assumptions and fixed odds sensitivities. It requires unique scenarios, one baseline, finite values and nonnegative weights summing to one. It does not claim an official economic forecast or newly estimated macro relationship.

Facility ECL preserves Stage 1 twelve-month PD, Stage 2 constant-hazard lifetime conversion and Stage 3 PD equal to one. LGD/EAD remain constant across the preserved scenario treatment. These are the project's reference conventions, not evidence that all institution-specific IFRS 9 requirements are met.

## 10. Facility trace and portfolio analytics

A decision trace links source borrower and facility snapshots, feature values, model hashes, policy/scenario identity, PD, stage reasons, watchlist/EWS, LGD, EAD, effective PD and ECL. Portfolio aggregates reconcile to these retained decisions. Concentrations are available by industry, product, collateral and stage.

Movement analysis decomposes changes in a fixed order: effective PD including stage/maturity, then LGD, then EAD, with new and exited facilities separate. The ordering is disclosed and is not a causal attribution. Reference ECL and approved override adjustments remain separate totals.

## 11. Validation and monitoring

The independent arithmetic module does not call the risk-engine ECL function. LGD validation reports MAE, RMSE, signed bias, actual/predicted means, fixed severe thresholds, low-loss and forecast-selected cohorts, counts and exposure shares. Zero-exposure weighted metrics are undefined rather than assigned arbitrary weights. Outcome submissions remain separate from prediction snapshots and report coverage of the resolved subset.

Monitoring currently supplies source-support alerts, prediction summaries, stage distributions and outcome validation. It is not a deployed model-performance alerting service. No institutional monitoring threshold was weakened to obtain a green status. Lack of observed outcomes and representative production support continues to block qualification.

## 12. Governance, registry and overrides

The registry separates reference models from blocked research candidates. Artifact corruption is checked before trusted local deserialization. No endpoint accepts arbitrary model binaries or turns a reference model into an approved active bank model.

Findings and lifecycle events are append-only. An ECL override records original result, proposal, reason, identity, timestamp and a separate manager decision. A proposer cannot approve the same proposal. One proposal per facility/run is permitted in this release. Approval changes the controlled reference view, never the original calculated result or bank-use gate.

## 13. Security and persistence

High-entropy credentials expire, can be revoked and are stored as hashes. Backend permissions, not a client role selector, control actions. The scope is one institutional workspace; multi-tenancy is not implied. Static UI rendering uses text content, and credentials are not retained in browser storage.

Relational keys and checks enforce snapshot relationships. Database triggers protect immutable evidence and terminal runs; audit events form a verified hash chain. PostgreSQL API-role grants exclude deletion, DDL and credential administration. A privileged database administrator remains outside these integrity guarantees; the chain is not external WORM evidence.

TLS, SSO/MFA, perimeter controls, institutional secrets management and independent penetration testing require actual deployment qualification. The retained legacy Streamlit app remains a demonstration and must not expose confidential data.

## 14. Software validation and reproducibility

The local suite passes 93 tests: 54 existing and 39 added platform cases. Tests cover data admission, authorization, credential lifecycle, immutable records, separate approvals, failed models/configuration/database, zero/subunit/extreme exposure, point-in-time history, movements and SQLite backup restoration. The legacy dashboard passed five role views, three filter modes, search and drill-down.

The full shadow comparison covers 5,172 facilities with numerically identical PD/LGD and no stage mismatches. ECL differences are bounded by the disclosed cent-level source precision. Actual Uvicorn startup and HTTP readiness/assets were exercised. A resolved dependency scan reported no known vulnerabilities at scan time; that is not a security guarantee.

The environment could not start PostgreSQL or run Docker, and Chromium retrieval returned a truncated archive. PostgreSQL/container/browser qualification therefore remains unverified despite implemented configurations and tests. Reproducibility commands, versions and evidence paths are documented without representing unexecuted hosted checks as passed.

## 15. Product architecture, limitations and future work

The canonical mapping boundary, versioned model/feature contracts and separate validation module create a path toward institutional adaptation. Institution policy, real data and model approval cannot be replaced by a larger synthetic sample. Customer-specific mappings, legal security capture, observed default/workout histories, calibrated scenarios and independent validation are prerequisites for bank use.

The public/reference layer can retain synthetic data, transparent methods, validation examples and architecture. Institution connectors, secrets, confidential portfolios and deployment configurations should be separated before commercialization. No existing public content was removed. Commercial positioning is a future decision, not a reason to imply certification.

The strongest legitimate next work is operational qualification and prediction-time information capture. Repeating unsuccessful LGD experiments without a new hypothesis is not justified. The platform is a tested reference foundation with explicit unresolved gates; the full institutional production mandate remains incomplete.

## References and evidence

Primary-source references and applicability are recorded in `EXTERNAL_EVIDENCE_REGISTER.md`; exact model results, denominators, hashes, methods and older adverse findings remain in the two preserved validation/research packages. Current evidence is in `platform_evidence/`. Read `FINAL_INDEPENDENT_VALIDATION_REPORT.md`, `SYSTEM_FINDINGS_REGISTER.md` and `FINAL_PRODUCTION_READINESS.md` together: implementation, validation and production approval are distinct conclusions.
