# API and access contract

Run `python -m uvicorn credit_platform.api:app --host 127.0.0.1 --port 8000`. OpenAPI schemas: `/openapi.json`, interactive schema `/docs` (public schema only; data endpoints require credentials). UI `/` contains no embedded borrower data. Every protected request requires `Authorization: Bearer <credential>`. Credentials are provisioned/revoked locally, not by a client-selected role.

| Resource | Methods / purpose | Authorization |
|---|---|---|
| /health/live, /health/ready | GET; service / schema+model+config health | Public, no data |
| /api/v1/me, /gates | GET; identity and production blockers | Authenticated |
| /api/v1/datasets | GET / POST canonical snapshots | Read all scoped roles / analyst, manager |
| /api/v1/borrowers, /facilities | GET paged source snapshots | Read |
| /api/v1/borrowers/{id}/history | GET with as_of, known_at | Read, dates filter business and knowledge time |
| /api/v1/runs | GET / POST reference or bank-purpose request | Read / analyst, manager; bank request stored BLOCKED |
| /api/v1/runs/{id}/portfolio | GET reconciled aggregates and concentrations | Read |
| /api/v1/runs/{id}/decisions | GET paged results | Read |
| /api/v1/runs/{id}/facilities/{facility_id} | GET full calculation trace | Read |
| /api/v1/runs/{id}/movement/{previous_id} | GET ordered ECL change attribution/migrations | Read |
| /api/v1/runs/{id}/monitoring | GET source-support diagnostics | Read |
| /api/v1/runs/{id}/validation | POST independent ECL recalculation | Validator |
| /api/v1/runs/{id}/outcomes | POST resolved LGD outcomes for separate validation | Validator; never modifies prediction features |
| /api/v1/models, /scenarios, /validation | GET registry/config/evidence | Read |
| /api/v1/findings, /findings/{id}/events | GET / POST append-only findings and lifecycle | Read / manager, validator, admin |
| /api/v1/overrides | GET / POST proposal | Read / analyst, manager |
| /api/v1/overrides/{id}/approval | POST approval or rejection | Different manager from proposer |
| /api/v1/approvals | GET decisions | Read |
| /api/v1/audit, /audit/verify | GET event chain / integrity check | Audit, admin |

Collection pagination: limit 1..500, offset >=0. Source/schema payloads reject unknown fields, NaN/infinity, missing features, invalid categories, duplicate/orphan entities and future-observed information. Request body limit 32 MiB. Errors: 401 identity, 403 permission, 404 absent, 409 conflict, 422 data, 503 DB/readiness. A failed calculation returns a persisted run with FAILED state, never a plausible fallback score.

Idempotency: request_key is unique; identical request returns the prior run, conflicting payload returns 409. Failed keys do not silently rerun. Model/config source is controlled server-side. No upload/deserialization endpoint for model binaries. All users share one institution scope; no multi-tenant claim.

Overrides are reference ECL adjustments, bounded 0..EAD, not new PD/LGD/staging methodologies. One proposal per facility result; reject/approve is final. Revised requests require a new reference run. Original ECL, approved adjustment and controlled total are displayed separately. Approval does not waive bank gates.
