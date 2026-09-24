# Deployment, failure recovery and observability

Target: one API/UI process and PostgreSQL 16, with one-off preparation/migration commands. No queue, microservice or Kubernetes requirement is demonstrated. Hosted service integrations are optional adapters, not fabricated deployments.

## Health and logging

`/health/live` indicates process availability. `/health/ready` verifies schema version, trusted artifacts and scenario loading; it does not approve a model. `deployment/logging.json` emits JSON request events with correlation ID, route template, status and latency. API responses carry X-Request-ID. Audit events carry run/entity IDs. Service metrics are operational; outcome metrics/support diagnostics are model monitoring. No Datadog connection or alert delivery has been tested.

## Backup and restore

PostgreSQL owner/operator should run `pg_dump --format=custom` against the private database, encrypt and retain backups according to institutional policy, and restore with `pg_restore` into a **new empty database**. Apply correct role grants, verify Alembic revision, run audit verification, compare dataset/run hashes and perform shadow/readiness checks before cutover. Never restore over the only copy. Nightly backup scheduling, off-site storage, RPO/RTO and a tested PostgreSQL restoration are not implemented claims.

SQLite development backup uses Python sqlite3's connection.backup API, not an unsafe copy of a live file; the local test verifies restored audit/dataset identity. This is not enterprise DR.

## Crash recovery

RUNNING records from an interrupted process are not automatically retried. Investigate process/DB state, retain original run and audit record, and execute a replacement with a new idempotency key. Successful/failed/blocked run rows are immutable. For interrupted RUNNING records, a database owner may mark FAILED with an audit event in one controlled transaction after checking no worker is active. There is no generic automatic restart masquerading as success.

## Migrations and rollback

Migration 0001 uses a frozen schema snapshot, foreign keys, checks, unique indexes and immutable-evidence triggers. API role lacks DDL/delete rights. Back up before migrations; restore to a separate database if rollback is needed. Destructive Alembic downgrade deliberately refuses. No historical V5 table/files are migrated in place; canonical ingestion adds new snapshots.

## Scheduling

For a small reference deployment use an external scheduler to invoke the documented CLI/API with a dedicated analyst credential and a deterministic reporting-date/dataset request key. Operational credentials expire; rotate/revoke them. No scheduler has been deployed here. Long-running batch work should be isolated from request workers before sustained institution workloads. Measured 5,172-facility shadow computation completes in seconds locally; no concurrency/load SLA is claimed.
