# Final institutional-platform consolidation

Status date: 22 October 2026  
Branch: `release/final-institutional-platform`

## Purpose

This branch is the integration layer for the complete professional reference platform. It does not erase or rewrite any research stream. Historical model, validation and interface branches remain independently addressable and their commits remain reachable.

## Preserved source streams

- Reviewed red-team baseline: `review/final-red-team-release` at `7773beb86df8480d964daaaf62199cedc15d356a`.
- Marginal Interest research: `research/lgd-marginal-interest-workout` at `20595b33a121acd1148aac704ea1e9ab83171936`.
- WN-1 workout engine: `research/lgd-workout-engine-vnext` at `fa365e1f93da26c4bba1601c3c56d5b4bba59ac5`.
- Preserved Streamlit/Copilot work: `feature/integrated-streamlit-copilot` at `df075125cf108d1bf91809924b3484fb5ff7840e`.

The consolidation commit has both WN-1 and the preserved interface branch in its ancestry. Failed challengers and adverse validation evidence are retained rather than rewritten.

## End-to-end scope

The platform retains the complete chain:

borrower/facility data → PD → internal risk rating → EWS → Watchlist → SICR → IFRS 9-style staging → LGD → EAD → scenarios → ECL → portfolio monitoring → model validation → governance → audit → human review.

The historical direct LGD, V5 evidence, S1/S2/R1 investigations, Marginal Interest experiment and WN-1 component workout challenger remain visible with their actual dispositions. The WN-1 component challenger is **not promoted** and LGD remains **blocked for institutional production**.

## Data and workout evidence

WN-1 retains the dated relational workout domain and frozen evidence for borrower, facility, default event, workout snapshots, collateral and valuations/enforcement, guarantees and claims, recoveries, workout costs, restructurings, cures, write-offs, interest accrual, resolution events, macro snapshots, observation-time feature contracts and out-of-time vintages.

This is a synthetic/publicly benchmarked demonstration environment. It demonstrates institutional process and controls; it is not a substitute for a bank's own empirical workout history.

## User interface

The Streamlit workbench is preserved visually and functionally with:

- Portfolio Cockpit
- Borrower Credit File
- Risk Management
- Risk Copilot
- Model Validation for the validator role

The Copilot is additive. Borrower evidence includes rating, EWS/risk direction, scenario PDs, staging reasons, facility product, collateral/guarantee context and remaining maturity. It does not replace PD/LGD/EAD/ECL, staging, approvals or model promotion.

## GenAI control model

The final Copilot uses the platform service layer as its single source of governed portfolio evidence. That canonical service now carries the full dashboard evidence set: stage, industry, product, rating, risk direction and collateral aggregations; watchlist/unsecured/guaranteed segments; scenario PD means; EWS/stage-reason counts; borrower risk indicators; risk patterns; deterministic review actions; top borrower and facility cases; overrides and controlled reference ECL. Deterministic facts remain authoritative. Optional OpenAI and local Ollama providers may add narrative interpretation, but a provider failure falls back to deterministic evidence.

Controls retained:

- role-based access
- allowlisted use cases/tools
- evidence references
- append-only request metadata
- prompt-injection refusal
- human-review requirement
- no autonomous credit approval
- no model modification or promotion
- no generated SQL
- explicit blocked institutional status

## Verification baseline and release qualification

The WN-1 branch reached **225 passing tests** before consolidation. The consolidated platform has since been qualified on fresh hosted runners; current functional evidence is summarized below.

The current hosted qualification baseline (`8deaeff3664a42812aff8ec01b0170628705cb49`) passed both full workflows. The platform workflow starts from a fresh checkout, rebuilds the V5 reference artifacts, runs the full suite, migrates PostgreSQL, executes the shadow calculation, persists WN-1, starts Streamlit headlessly and builds the Docker image.

Current evidence:

- **240 passed, 1 upstream warning**
- V5 release checks **30/30**
- **5,172 facilities** reconciled
- EAD **2,091,914,075.83**
- ECL **45,265,972.04**
- **0 stage mismatches**
- audit chain **VERIFIED**
- PostgreSQL migrations/shadow **PASS**
- WN-1 PostgreSQL persistence **VERIFIED**
- Streamlit headless startup **PASS**
- Docker image build **PASS**

The final Risk Copilot also now carries a structured full-context evidence packet for open-ended local Ollama reasoning, while exact rankings, concentration calculations and borrower-driver extraction remain anchored to deterministic governed analytics.

## Claim boundary

Suitable public description:

> A full-stack, production-oriented Credit Risk analytics, decisioning, IFRS 9-style ECL, model-validation and governance platform demonstrating an institutional credit-risk lifecycle using synthetic and publicly benchmarked data.

Do not describe the project as bank-approved, regulator-approved or institutionally calibrated on real bank data.
