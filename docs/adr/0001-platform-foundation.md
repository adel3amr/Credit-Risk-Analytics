# ADR 0001 — Modular reference platform

## Context

Validated model research exists, but flat-file runs overwrite results and demo role selection provides no backend identity enforcement. New LGD inputs remain unavailable.

## Alternatives

Retain notebooks only; rewrite all risk methods; adopt microservices; or add a modular monolith around frozen reference engines.

## Decision

Use a modular monolith, SQLAlchemy/PostgreSQL relational snapshots, FastAPI service, static workflow UI and transparent reference-only model status. Preserve source methods and historical branches. Use SQLite for local tests without treating it as PostgreSQL evidence. Immutable JSON feature snapshots preserve exact input lineage while relational keys enforce ownership.

## Consequences

One governed calculation path serves API/CLI. Institution mapping can target the canonical contract. No new algorithm or statistical claim is needed. PostgreSQL/browser/deployment qualification, institution data and independent approval remain gates.
