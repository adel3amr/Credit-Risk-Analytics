# GenAI risk and controls

| Risk | Control | Residual limitation |
|---|---|---|
| Fabricated calculation | Provider receives retrieved facts; risk arithmetic remains outside Copilot | External prose still needs review |
| Unsupported claim | Source list, fixed model-risk fact set, insufficient-evidence fallback | Retrieval corpus is deliberately narrow |
| Prompt injection | Input pattern rejection; no system prompt, secret or database tool exposure | Pattern controls are not a complete adversarial defense |
| Unauthorized access | Existing authentication/RBAC; audit-only request listing | Shared institutional scope, no row-level tenant policy |
| Unrestricted database access | Fixed SQLAlchemy queries with typed IDs; no generated SQL | New tools require code review |
| Confidential external transfer | Local provider default; explicit external opt-in and HTTPS/secret required | External provider has not been institutionally assessed |
| Decision automation | `authoritative_decision=false`, human-review flag and UI label | Users must follow governance process |
| Audit gaps | Immutable metadata record and hash-chained audit event | Raw prompt/answer intentionally not retained |
| Model/version drift | Provider and prompt versions recorded | External provider model identity depends on provider contract |

The Copilot is reference software. External-provider, institutional privacy, retention, identity, penetration-test and deployment controls remain blocked pending an actual institution and environment.
