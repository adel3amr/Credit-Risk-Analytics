# Authoritative WN-1 workout and platform closeout

Release review date: 8 October 2026. Branch: `research/lgd-workout-engine-vnext`.
Starting commit: `20595b33a121acd1148aac704ea1e9ab83171936`.
Frozen reviewed baseline: `7773beb86df8480d964daaaf62199cedc15d356a`.
Frozen fitted models: `c80f3050d24b4c3075ef5e2ece4c0f110accdd74`.
Final delivery commit and working-tree verification: supplied in the accompanying post-commit receipt; the checkout's `git rev-parse HEAD` identifies this report's release. A commit cannot include its own hash as content.

## Decision

The bounded experiment and local reference-platform integration are complete. **The WN-1 component LGD model is NOT PROMOTED. LGD remains BLOCKED FOR INSTITUTIONAL PRODUCTION.** The severe-loss issue has not been solved. No historical model, target, dataset or release was retroactively improved. The active scorer was not replaced.

Freeze this as a transparent learning/professional reference checkpoint, not as a qualified deployed production release. PostgreSQL, Docker, rendered browser and hosted CI for this final branch remain unverified. Missing qualification is not treated as passing. No additional model search is recommended within this completed experiment.

The generated `results/decision.json` contains the experimental status string `REFERENCE_ARCHITECTURE_COMPLETE_MODEL_NOT_PROMOTED` and engineering `PENDING`. These are preserved raw experiment output, not a claim that every release requirement passed. This report is the authoritative qualified interpretation: local reference integration is verified, deployment qualification remains outstanding, and workout simplifications remain explicit.

## What was delivered

Dated relational workout schema and transactional loader; prospective frozen ledger; observation-time feature contract; fixed direct/component experiment with eight preregistered family ablations; clustered uncertainty; segment, vintage and stress diagnostics; independent cashflow/target reconciliation; a controlled Stage 3 ECL bridge; blocked registry entries and retained findings; one deterministic portfolio evidence source for API, dashboard and Copilot; authenticated WN-1 evidence endpoint/tab; numerical narrative guard; updated workflows, documentation, worked cases and validation figure.

This is not a fully institution-calibrated workout system. Timing regression is resolved-only; survival is descriptive; security availability is incompletely depleted after payout; real source capture is absent. These are documented, not concealed by aggregate metrics.

## Dataset and lineage

| Item | Frozen evidence |
|---|---|
| Dataset/DGP | WN-1, seed 1072026, new prospective population |
| Borrowers / facilities / defaults | 8,000 / 8,000 / 8,000 |
| Workout observations | 31,815 |
| Recovery transactions | 64,838 |
| Default vintages | 2010–2020 |
| Development | 4,800 borrowers, vintages 2010–2014, 18,994 snapshots |
| Validation | 1,600 borrowers, vintages 2015–2017, 6,611 snapshots |
| Final | 1,600 borrowers, vintages 2018–2020, 6,210 snapshots |
| Final accuracy population | 5,290 resolved snapshots; 1416 distinct borrowers |
| Unresolved | 1,020 episodes; 5,100 snapshots across splits without invented realized targets |
| Currency | EUR for WN-1 only |
| Hashes | `data/manifest.json`, `results/LOCK.json`, `EVIDENCE_LOCK.json` |

One facility/default per borrower is a demonstration simplification. Correlated snapshots are split by borrower, and uncertainty resamples borrower clusters. Snapshot averages do not give every borrower equal weight; long unresolved trajectories contribute more snapshots. ECL uses exactly one age-zero observation per final facility.

Both effective and recorded dates must precede observation. The audit checked all 31,815 snapshot lineage sets. Future cashflows, final cure/resolution, realized LGD and latent simulation capacity are excluded from predictor columns. These checks establish implementation lineage in synthetic data, not the completeness of institutional source systems.

Principal plus predefault accrued interest forms default exposure; received recoveries reduce remaining EAD. Postdefault Marginal Interest is a suspended memorandum balance and is never capitalized into EAD or counted again in recoveries. Writeoff is noncash. Costs and positive recovery channels are distinct dated ledger records. Independent discounting used calendar dates and reconciled to stored targets with maximum absolute error **3.71e-11**. 391 resolved targets require [0,1] clipping; raw ratios are retained. This clipping is visible, not a hidden accuracy adjustment.

The preceding MI study did not establish incremental MI value. Its ECL currency was unspecified; the supplied mandate's euro symbol was not supported by that prior dataset. WN-1 explicitly defines EUR. No historical currency label or dataset was changed.

## Fixed LGD comparison

All errors below are percentage points of LGD. These are new remaining-workout targets; historical V5 and MI metrics cannot be compared as if only the algorithm changed.

| Final model | MAE pp | RMSE pp | Bias pp | Predicted mean % | Realized mean % |
|---|---:|---:|---:|---:|---:|
| direct_new | 15.2919 | 22.6201 | -1.4251 | 20.0047 | 21.4299 |
| component | 15.8566 | 22.6473 | -1.7876 | 19.6423 | 21.4299 |
| retained_transfer | 27.0964 | 31.8179 | 15.4167 | 36.8466 | 21.4299 |

The retained R1 transfer uses proxy feature mapping and a different target; it is a transfer diagnostic, not a fair matched-target contest. Direct-new and component use the same WN-1 population. The fixed algorithms differ, so that comparison does not isolate feature value. Within-component leave-family-out ablations hold the algorithm fixed. Removing interest gives RMSE 22.5909% versus 22.6473%; this does not establish a useful MI contribution, and no ablation was selected as a replacement.

The component RMSE minus direct RMSE is **+0.0272 pp**, with paired borrower-bootstrap 95% interval **[−0.4823, +0.5553] pp**. No reliable superiority is demonstrated. MAE difference interval **[+0.1629, +0.9583] pp** indicates worse MAE. Candidate RMSE absolute interval is [21.6129, 23.6716]%; candidate MAE [15.0448, 16.6720]%; overall bias paired-bootstrap interval [−3.0465, −0.5694] pp. Separately resampled absolute intervals are in `absolute_uncertainty.csv`; small differences across interval estimates reflect different RNG draws, not alternate model selection.

### Severe losses and cures

| Final segment | Model | Snapshots | Bias pp | RMSE pp |
|---|---|---:|---:|---:|
| high60 | direct_new | 746 | -40.322 | 44.938 |
| high60 | component | 746 | -44.768 | 47.246 |
| high75 | direct_new | 570 | -42.066 | 46.637 |
| high75 | component | 570 | -46.208 | 48.613 |
| high90 | direct_new | 262 | -42.135 | 47.277 |
| high90 | component | 262 | -46.338 | 49.330 |
| low10 | direct_new | 2901 | 9.343 | 15.336 |
| low10 | component | 2901 | 9.522 | 14.120 |
| cure | direct_new | 3317 | 9.878 | 16.639 |
| cure | component | 3317 | 9.717 | 14.866 |
| noncure | direct_new | 1973 | -20.429 | 30.107 |
| noncure | component | 1973 | -21.129 | 31.680 |

The >75% tail has **570 snapshots from 166 distinct borrowers**. The candidate's severe-loss bias is −46.2085 pp versus direct −42.0656 pp. These observations are not 570 independent facilities. Outcome-conditioned tail bias is diagnostic, not by itself proof that a conditional-mean model is incorrectly calibrated. Independent prediction-time calibration and stress failures also occur here, so promotion is blocked on broader evidence.

Cure decomposition reduces cure-cohort RMSE but does not improve aggregate accuracy. Cure probability Brier and confidence intervals are in `cure_validation.json` and `absolute_uncertainty.csv`. Paid cure and resolved-only sampling limit interpretation. The experiment cannot assert unbiased eventual cure predictions for censored cases.

### Calibration, support, stability and stress

Predeclared overall 1 pp and material-segment 2 pp bias-equivalence gates are not met. Calibration failures: all, restructured, unsecured, guaranteed, full_guarantee, industry:Construction, industry:Manufacturing, industry:Retail, industry:Services, product:OVD, product:Term Loan, default_vintage:2018, default_vintage:2019, default_vintage:2020, age:0, age:6, age:12, age:24, predicted:0-0.1, predicted:0.25-0.5, predicted:0.5-0.75, predicted:0.75-1. Outcome-based cohorts were not substituted for prediction-time promotion groups. Calibration slope/intercept and clustered intervals are reported rather than silently recalibrating predictions.

Final numerical support violations: **13 feature-observation occurrences**, not 13 necessarily distinct facilities. Joint support and institutional feature availability are not established. Zero eligible guarantee share is 68.14% development, 66.90% validation and 70.11% final. The original near-universal development guarantee mismatch is not repeated, but this does not close all support gaps.

Direct training RMSE is substantially below out-of-time performance. Component validation RMSE is 25.7679% and final 22.6473%; changing vintage mixtures affect results. Per-vintage diagnostics remain visible in `segments.csv`; a lower final aggregate is not proof of transportability.

Final stress diagnostics: downturn +8.8003 pp mean LGD, collateral shock −0.2549 pp, guarantee-quality shock +0.1945 pp, slower recovery +3.5647 pp, cost shock +1.5581 pp. The negative average collateral-shock response is economically problematic. There are **4,466 reversal occurrences across scenarios**, not unique facilities. Timing/cost shocks are cashflow sensitivities; input shocks are model sensitivities, not realized stressed validation. Nothing was sorted or adjusted to make them monotonic.

## Controlled ECL bridge

After model freeze, hold borrower population, Stage 3, PD=1, EAD and baseline scenario weight=1 constant. The cohort spans default dates and is not a single reporting-date bank balance sheet.

| Measure | Value |
|---|---:|
| Facilities | 1,600 |
| EAD EUR | 584,272,556.30 |
| Direct-new ECL EUR | 95,166,131.45 |
| Component ECL EUR | 93,856,252.08 |
| Change EUR | -1,309,879.37 |
| Change % | -1.3764 |
| Maximum facility arithmetic error | 0.0 |

Stage 1 and Stage 2 are N/A in this impaired-only cohort. The active platform's Stage 1/2/3 totals remain unchanged and are independently reported below. No synthetic borrower join between unrelated datasets was fabricated. This is shadow/unbooked sensitivity, not an ECL reserve release or a promotion criterion. Industry contributions reconcile in `ecl_segments.csv` and facility contributions in `ecl_facilities.csv.gz`.

## Complete reference platform

The existing chain remains borrower/facility → PD/rating → EWS/watchlist → SICR/staging → LGD/EAD/scenarios → ECL → portfolio → validation/governance. The internal nine-month watchlist rule is preserved and not attributed to a regulator.

Full execution: **3,000 scored borrowers / 5,172 facilities**, EAD 2,091,914,075.83, reference ECL 45,265,972.04 in the existing portfolio's unspecified currency. WN-1 EUR does not relabel this portfolio.

| Stage | Facilities | EAD | ECL |
|---|---:|---:|---:|
| Stage 1 | 4772 | 1,930,297,086.16 | 28,437,247.57 |
| Stage 2 | 385 | 156,951,974.48 | 14,249,690.53 |
| Stage 3 | 15 | 4,665,015.19 | 2,579,033.95 |

No stage mismatches; maximum PD/LGD differences from retained output below 1e-12. Maximum EAD difference 0.010000, ECL difference 0.002569, attributable to documented stored face/CCF rounding. Independent ECL arithmetic maximum error 0. Audit chain verified. Watchlist: 505 facilities, 287 distinct borrowers.

PD was not refitted. Recalculated 3,000-borrower holdout output metrics: AUC 0.759455, Gini 0.518911, KS 0.408497, Brier 0.030003, log loss 0.128562, observed default 3.4000%, mean PIT prediction 3.4388%. These reproduce the currently inspected output; they supersede prompt numbers for this specific population only.

### Dashboard and Copilot

Ten representative full-portfolio questions exactly match the cockpit evidence object: totals, borrowers, facilities, stages, industries, watchlist, unsecured, guarantee support, top-risk cases and deterioration. Facility-level segment EAD reconciles to the total; distinct borrowers may overlap across segments. Single-run evidence cannot answer temporal deterioration or ECL-change causality, and the response states that limitation. Existing two-run movement remains available separately.

WN-1 model-risk questions and the authenticated validation tab share one hash-verified evidence provider. The default model-risk response includes latest WN findings while preserving historical evidence. Registry seeding adds BLOCKED WN entries and findings. No autonomous approval, ECL booking, scoring modification or model promotion is available through Copilot. Unverified external provider prose falls back to deterministic text. This demonstrates governed narrative controls, not qualified unconstrained GenAI analytics.

## Engineering and release evidence

| Gate | Status | Evidence / residual risk |
|---|---|---|
| Automated suite | PASS: 225 tests | `release/tests.txt`; one upstream TestClient deprecation warning |
| Frozen artifacts | PASS | hashes and inference reproduce within 5e-13; no refitting |
| Ledger DQ/lineage | PASS within stated schema | 31,815 snapshot lineage/arithmetic checks; remaining-security limitation stays open |
| Persistence | PASS SQLite | full table counts; transaction/FK, dates, partial-schema rejection tests |
| Platform arithmetic | PASS | 5,172 facility comparison, independent ECL and audit |
| API/auth/RBAC | PASS local | live HTTP readiness 200, protected 401, forbidden audit 403, authorized evidence 200 |
| Copilot/cockpit | PASS deterministic evidence | exact shared object on full portfolio; no open-ended LLM qualification |
| JavaScript / Python static | PASS | Node syntax and compileall; not visual verification |
| PostgreSQL | NOT RUN current branch | no local PostgreSQL runtime; portable schema and workflow do not substitute for execution |
| Docker | NOT RUN | binary absent; existing nonroot Dockerfile retained |
| Hosted CI | NOT RUN on final branch | workflow extended; historical green runs are not this release |
| Rendered browser | OUTSTANDING | truncated Playwright browser download; no fabricated screenshots |
| GitHub publication | Pending final checkpoint push; receipt records actual result | no claim that remote branch exists until verified |
| Institutional LGD | BLOCKED | calibration, MAE, stress, support, censoring, real feature capture |
| Operational deployment | BLOCKED | no qualified live database/TLS/SSO/backup/monitoring environment |

The separate `research/lgd-tail-programme` worktree remains untouched with its pre-existing uncommitted `lgd_research/data/r2_development.csv` change. It is not part of the vNext commit. A Git bundle preserves committed refs/history, not uncommitted worktree files. Local runtime environments, database copies, tokens and caches are not release artifacts.

## Remaining limitations and future work

See `workout_vnext/FINDINGS.md` for preserved findings. Main limitations: hypothetical synthetic parameters; paid-cure simplification; stale in-workout credit snapshots; last known security versus remaining claimable security; one facility per borrower; resolved-only labels; uncensored timing regression; joint support absent; no institution-specific risk policy/approval; no qualified external GenAI; deployment gates outstanding. Security testing is practical regression coverage, not a penetration-test certification. Reference model artifacts are trusted repository binaries and must never be loaded from arbitrary user uploads.

A future version could capture depleted collateral/guarantees, refreshed credit histories and censored-outcome modelling under a fresh preregistration and untouched holdout. It must not rewrite this failed experiment. No new research search is part of this closeout.

## Reviewer run and demonstration

Follow `workout_vnext/README.md` for exact install, hash verification, tests, migrations, data loading, API and UI commands. Demonstrate: (1) reference-only gate and portfolio counts; (2) stage/industry composition; (3) borrower/facility decision trace; (4) WN dated ledger and worked cases; (5) validation figure and failed gates; (6) Copilot answer plus identical evidence; (7) blocked registry/findings; (8) two-person override and audit. Capture actual rendered screens after browser qualification; the committed figure is a validation plot, not a UI screenshot.

Recommended public description: **A full-stack, production-oriented reference Credit Risk analytics, IFRS 9-style decisioning, model-validation and governance platform demonstrating an institutional-style credit-risk lifecycle using transparent synthetic data and publicly informed data architecture.** No bank approval, real-bank calibration or regulatory certification is claimed.

Final recommendation: freeze the bounded research and local reference deliverable, retain the direct active reference scorer, keep WN component unpromoted, and complete separately tracked deployment/publication qualification before calling the release fully deployed.
