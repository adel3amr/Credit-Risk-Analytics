# ADR 0002 — Identity and evidence boundaries

## Context

There is no connected institutional identity provider, and exposing a fake login would misrepresent controls. Model files use Python serialization.

## Alternatives

Client-selected roles; homemade password accounts; external OIDC requiring absent infrastructure; or opaque high-entropy credentials provisioned by a trusted operator.

## Decision

Expiring revocable opaque credentials, hashed at rest; backend permissions; different-manager approval; one institution scope; trusted local model path with SHA checks; append-only evidence and hash-chained audit. No model upload or promotion endpoint.

## Consequences

Credentials are operational access keys, not an SSO/MFA replacement. TLS and perimeter controls must precede public deployment. Hashes detect corruption but are not authenticity signatures against administrators. External audit anchoring and institution identity integration remain qualification work.
