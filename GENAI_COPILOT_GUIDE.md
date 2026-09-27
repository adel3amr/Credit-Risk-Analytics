# GenAI Credit Risk Copilot guide

Version 2 adds an allowlisted S2 economic LGD validation source. Ask "Explain S2
observable economic LGD and the promotion decision" in Model risk mode. Facts and
numeric comparisons are read from the frozen decision and checked against source
hashes. The answer explicitly distinguishes S1 from S2 and retains the no-promotion
decision. Authentication, permissions, audit and provider controls remain unchanged.

## Purpose

The Copilot explains existing governed outputs. It answers four controlled use cases: borrower explanation, portfolio summary, model-risk/validation explanation, and a draft credit review. Every narrative is marked for human review and is not an authoritative credit decision.

It does not estimate PD or LGD, calculate EAD or ECL, assign SICR/stage/watchlist status, approve an override, promote a model, or execute SQL supplied by a model. Those functions remain in the deterministic risk and governance services.

## Grounding and tool calling

The request explicitly selects a use case. The service maps it to an allowlisted function:

| Use case | Allowed source/tool |
|---|---|
| Borrower / credit review | Stored facility decision traces for one run and borrower |
| Portfolio | Reconciled run portfolio and stage aggregation |
| Model risk | Frozen authoritative LGD decision artifact |

The response returns `facts`, `sources`, and `tool_calls` separately from the generated narrative. Missing entities produce an insufficient-evidence response. Prompt-injection patterns produce a refusal. There is no natural-language-to-SQL facility.

## Access, audit and privacy

The endpoint requires the platform's bearer authentication and `read` permission. It inherits the platform's current shared institutional scope; the platform does not claim multi-tenant borrower entitlements. Only audit/admin roles can list Copilot request records. The immutable record stores actor, role, use case, hashes, provider/version, prompt version, tools and sources. It does not retain raw questions or answers.

The default deterministic provider runs locally. No information leaves the platform. An external JSON provider can be enabled only with `COPILOT_PROVIDER=external-json`, `COPILOT_ALLOW_EXTERNAL=true`, an HTTPS endpoint, and a secret supplied outside Git. An institution must complete privacy, security, vendor and data-transfer approval before doing so. A future local model can implement the same provider interface.

## Hallucination controls

Responses use retrieved structured facts, deterministic calculations stay outside the provider, model-risk statements come from the frozen decision, sources are returned to the UI, and absent evidence fails closed. The deterministic provider renders fixed templates. External output is still a draft and requires human review.

## Evaluation

`tests/platform/copilot_benchmark.json` defines the curated reference questions, required tools/facts, prohibited claims and refusal cases. API tests verify numerical agreement with source runs, exact stage reasons, source attribution, metadata-only audit records, authorization, injection refusal, missing-evidence behavior, and external-provider opt-in. Results are frozen in `genai_evidence/copilot_evaluation_results.json`.

## API

`POST /api/v1/copilot/query` accepts `question`, `use_case`, and the required `run_id`/`borrower_id`. `GET /api/v1/copilot/requests` is restricted to audit permission. See `API_DOCUMENTATION.md` for the schema and example.
