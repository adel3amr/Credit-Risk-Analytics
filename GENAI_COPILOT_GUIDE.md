# GenAI Credit Risk Copilot guide

## Purpose

Risk Copilot is a narrative/reasoning layer over the platform's governed Credit Risk evidence. It does **not** replace the deterministic PD, rating, EWS, Watchlist/SICR, staging, LGD, EAD or ECL engines.

Supported scopes:

- portfolio analysis;
- borrower explanation;
- draft credit review;
- model-risk / validation explanation.

Every response is for human review and is not an authoritative credit decision.

## Current architecture

```text
governed data + stored run evidence
        ↓
canonical service / deterministic analytics
        ↓
question-specific verified facts
        ↓
full governed context packet
        ↓
deterministic provider OR local Ollama OR optional hosted provider
        ↓
human-review narrative + evidence/tool metadata
```

The deterministic layer remains authoritative for exact calculations. The language model may synthesize and explain, but it may not silently replace governed numbers or decisions.

## Evidence available to the Copilot

### Portfolio scope

The context can include:

- portfolio borrower/facility totals, EAD and ECL;
- stage, industry, product, rating, risk-direction and collateral-type aggregations;
- EAD/ECL shares, mean PD, mean LGD and loss intensity;
- Watchlist, unsecured and guaranteed segments;
- scenario mean PDs;
- EWS trigger and stage-reason counts;
- risk-indicator counts and risk patterns;
- review actions;
- top borrowers by ECL and EAD;
- top facility risk cases;
- concentration evidence;
- approved overrides and controlled reference ECL where present.

### Borrower / credit-review scope

The context can include the complete admitted borrower feature vector and all selected-run facility traces: utilization, delinquency/DPD, leverage, qualitative factors, rating, risk direction, EWS, Watchlist, SICR, stage reasons, PIT/scenario/effective PDs, LGD, EAD, ECL, product, maturity, collateral, guarantees, lien rank, drawn/limit/face amounts and related decision evidence.

### Model-risk scope

The Copilot can retrieve the preserved authoritative validation/research evidence, including the economic LGD, hardening and WN-1 workout decisions used by the current platform.

## Exact analytics vs narrative reasoning

Questions that require exact rankings/concentrations or explicit borrower adverse-driver extraction are routed through deterministic governed analytics for the final numerical answer. Examples include:

- "riskiest 5 customers and their concentration";
- "riskiest industry";
- "what are this borrower's key adverse indicators?"

Open-ended interpretation can use the richer model context, for example:

- "summarize the portfolio and prioritize human review";
- "explain why this borrower deserves attention";
- "explain the LGD validation story and why the challenger was not promoted."

This separation keeps arithmetic/reconciliation inside the risk engine while still allowing richer language reasoning.

## Local Ollama — recommended zero-cost demo

```powershell
$env:COPILOT_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.2"
$env:OLLAMA_NUM_CTX="16384"
$env:OLLAMA_NUM_PREDICT="640"
python -m streamlit run app.py
```

Ollama receives a structured business-readable evidence packet rather than an unbounded raw-data dump. The larger local context window exposes the relevant platform evidence while reducing the chance that a smaller model becomes distracted by serialization details.

## Other providers

- `deterministic`: default, local, no model/API dependency.
- `ollama`: local conversational reasoning.
- `openai`: optional hosted Responses API adapter; not required and may incur separate charges.
- `external-json`: explicit opt-in adapter for a configured HTTPS provider.

`COPILOT_PROVIDER=auto` prefers a configured hosted key, then configured Ollama, otherwise deterministic.

## Controls

The current implementation includes:

- role-aware governed evidence access;
- allowlisted use cases/tool routing;
- no generated SQL execution;
- no autonomous approval/override/model promotion;
- deterministic verified facts for numerical questions;
- prompt-injection/refusal patterns;
- narrative quality filters for known failure modes;
- explicit guardrails against interpreting Stage 1 as "high risk";
- explicit guardrails against interpreting a research/model gate as a ban on new lending;
- provider failure fallback to deterministic evidence;
- evidence/tool metadata and append-only request audit records;
- human-review requirement.

The audit record stores metadata/hashes rather than using generated prose as an authoritative decision record.

## Evaluation

Tests in `tests/platform/` cover provider selection, evidence completeness, concentration/ranking logic, borrower adverse indicators, injection refusal, known credit-risk misreadings, source integrity and platform permissions. The complete repository suite is run in CI.

For API contracts see [API_DOCUMENTATION.md](API_DOCUMENTATION.md). For architecture/risks see [GENAI_ARCHITECTURE.md](GENAI_ARCHITECTURE.md) and [GENAI_RISK_AND_CONTROLS.md](GENAI_RISK_AND_CONTROLS.md).
