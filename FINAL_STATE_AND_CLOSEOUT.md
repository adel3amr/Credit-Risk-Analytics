# Final state and closeout

Latest post-R1 hardening: `lgd_hardening/DECISION.md`. Baseline `14b8c4d`,
preflight protocol `fe2f245`; 168 tests pass. Continuous calibration rejected,
R1 retained, unavailable recovery-information requirement documented and enforced
through new capture/domain/release boundaries. No new independent holdout,
promotion, booked ECL movement, historical rewrite or remote push.

## Latest focused S2-R1 remediation — 27 September 2026

Baseline `ef5a1c5`; protocol commit `8cb92ef`; frozen candidate/data `e8e9228`.
One new candidate, one final opening, **151 tests passed**, deterministic refit
reproduced exactly. See `s2_remediation/DECISION.md`. Scenario shape is corrected;
current point calibration is preserved; wider promotion checks fail. Challenger
`s2-r1-monotone-gb-1` remains unpromoted. Active reference engines and institutional
bank-use gate are unchanged. Latest authenticated UI/API/Copilot evidence includes
the failed checks. No remote push, final-set retuning or booked adjustment.

## Subsequent S2 remediation — 27 September 2026

Starting from 281f114, protocol commit ffe25da and frozen candidate/data commit
4a84ae5 precede final evaluation. See `economic_lgd/DECISION.md`. 136 tests pass;
original 125 retained. Current S2 conditional bias -6.33 → -0.26 pp, but scenario
and segment findings prevent promotion. Historical S1 -12.65 pp is not a like-for-
like comparison. Active risk engines, historical datasets and bank gates unchanged.
New read-only economic-LGD UI/API and Copilot evidence preserve auth/audit controls.

Date: 27 September 2026. Branch: `platform/production-foundation`. Starting commit for this closeout: `ca5826b`.

## Reconstructed completed state

The repository already contained the complete V5 historical release, independent whole-repository validation, the S1 linked synthetic bank, production-oriented persistence/API/UI/governance foundation, 5,172- and 8,695-facility reconciliation evidence, and the final downturn-calibration investigation. The last LGD decision remains authoritative: current conditional bias is -12.65 pp; true synthetic state calibration is diagnostic only; deployable state proxies fail; the all-downturn treatment is a sensitivity and cannot be booked. The active model, historical data, frozen evidence and institutional gate remain unchanged.

This closeout adds schema migration `0002`, a controlled Copilot service, API/UI integration, metadata-only immutable request evidence, benchmark evaluation, and release documentation. No data was regenerated and no model was retrained.

## Unresolved or externally blocked

- Institution-specific data mapping, outcome history, calibration, accounting approval and independent model validation.
- Prediction-time downturn/recovery-quality data sufficient to resolve LGD population transfer.
- PostgreSQL/container execution in this environment, external identity/MFA/TLS/perimeter controls, penetration testing, operational alerting, backup restoration in a deployed environment, load/SLA testing, and institutional browser qualification.
- Optional external LLM quality, privacy, contractual and security review. It is disabled by default.

## Closed here

- Controlled borrower, portfolio, credit-review and model-risk Copilot use cases.
- Allowlisted tool routing with no generated SQL and no scoring/decision capability.
- RBAC inheritance, evidence references, numerical grounding, refusal behavior, request/provider/prompt/tool audit metadata, and deterministic test provider.
- UI surfaces generated output as a human-review narrative and displays evidence/tool calls.
- Compact benchmark covers grounding, numerical consistency, source attribution, authorization, missing evidence, tool selection and prompt injection.

## Do not repeat

Do not regenerate the synthetic datasets, reopen completed LGD experiments, tune retrospective severe-loss cohorts, promote the oracle calibration, or turn the sensitivity overlay into booked expected LGD without a new governed methodology/data/validation process.

## Verification

- Full suite: 125 passed, zero failed, one upstream TestClient deprecation warning.
- Fresh schema migration: `0002`; audit chain: verified; copied-database restore integrity: `ok`.
- Copilot benchmark: 6/6 cases passed with the deterministic local provider.
- The malformed former default database remains in Git history and its hash is recorded. A clean schema-`0002` default reports READY. PostgreSQL, container and real-browser qualification remain blocked/unverified.
