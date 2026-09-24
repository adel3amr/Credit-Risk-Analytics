# Security review and residual exposure

Scope: new API/persistence reference service, static UI and trusted artifact boundary. Review is source inspection and automated adverse tests, not independent penetration testing.

Implemented: high-entropy expiring/revocable credentials hashed at rest; backend permissions; distinct proposal/approval identity; parameterized SQLAlchemy queries; strict schemas; finite/range/source-time checks; no arbitrary upload paths or model loading; source/artifact hash checks; public UI contains no data; DOM rendering uses textContent; no browser credential persistence; no CORS relaxation; no debug setting; private database network; loopback API binding; non-root application image; dropped container capabilities; read-only API filesystem; append-only evidence triggers and restricted API DB grants; structured logs exclude payloads, credentials and borrower-specific URL strings.

Tests cover unauthenticated calls, invalid/expired/revoked credentials, forbidden roles, same-person approval, duplicate approval, immutable source/results/terminal runs, schema failures, missing/corrupted model path, failed DB readiness and audit integrity. Dependency scan completed with no known vulnerabilities reported at scan time; see platform_evidence/dependency_audit.json. This is not proof of absence of vulnerabilities and transitive versions should be rescanned at deployment.

Not qualified: TLS, SSO/MFA, institutional network policy, external secret manager, perimeter request/rate controls, external audit anchoring, penetration test, tenant isolation, backup confidentiality and database administrator controls. The legacy Streamlit app still has a demo role selector and must not host confidential data. Public or institutional production deployment remains blocked.

An API token with correct scope authorizes all records in this one institutional workspace. Scope partitioning must be added and independently tested before serving multiple institutions. Model hashes detect corruption, not malicious replacement by a trusted system administrator. Only locally built, trusted joblib artifacts may be loaded.
