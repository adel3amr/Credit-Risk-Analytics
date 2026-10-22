# GenAI risk and controls

| Risk | Current control | Residual limitation |
|---|---|---|
| Fabricated calculation | PD/LGD/EAD/ECL/staging and exact rankings/concentrations remain deterministic; provider receives verified facts | Narrative can still be imperfect and requires review |
| Metric/entity mix-up | Question-specific verified facts plus exact-analytics routing; regression tests cover industry/customer concentration | New phrasings can require new tests |
| Unsupported claim | Governed evidence packet, frozen model-risk evidence, insufficient-evidence fallback | Evidence is limited to the selected governed scope |
| Credit-risk misinterpretation | Narrative gate rejects known errors such as “Stage 1 = high risk” and “blocked model gate = no new lending” | No finite rule set replaces expert review |
| Prompt injection | Input-pattern refusal; no system-secret or unrestricted database tool exposure | Pattern controls are not a complete adversarial defense |
| Unauthorized access | Platform RBAC for API; fixed local demo identities for Streamlit | Streamlit demo identity selector is not production authentication |
| Unrestricted database access | Typed/allowlisted service queries; no generated SQL execution | New tools require code review |
| Confidential external transfer | Deterministic and Ollama modes are local; hosted/external providers require explicit configuration | Hosted-provider privacy/vendor/residency qualification is external |
| Decision automation | Human-review flag; no autonomous approval, override or model promotion | Users must follow the governance process |
| Audit gaps | Append-only Copilot request metadata plus hash-chained platform audit | Raw prompt/answer deliberately not retained as authoritative evidence |
| Model/version drift | Prompt/provider versions stored with request metadata | Model weights can change when users deliberately change configured models |
| Provider outage/failure | Provider exceptions fall back to deterministic governed evidence | Rich narrative may be unavailable until provider recovers |

## Local Ollama boundary

Ollama receives a structured full-context packet relevant to the selected borrower/portfolio/model-risk scope, not a raw dump of every repository row. The publication guide uses a configurable context budget of 16,384 and response budget of 640 tokens.

The language model is used for interpretation and synthesis. Governed numerical calculations remain outside the LLM.

## Hosted-provider boundary

OpenAI and the generic external-JSON adapter are optional integration examples. They are **not required** for the public project and may carry external cost/privacy/vendor requirements. No hosted provider constitutes bank approval or model validation.

## Deployment boundary

This is research/reference software. Institution-specific privacy, retention, identity, row-level entitlement, penetration testing, TLS/perimeter, vendor and operational controls remain separate deployment qualification work.
