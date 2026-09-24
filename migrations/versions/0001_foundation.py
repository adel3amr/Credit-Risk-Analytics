"""Initial additive platform schema. Recovery uses backup restore, never destructive downgrade."""

from alembic import op
from migrations.schema_v0001 import metadata

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

IMMUTABLE = [
    "datasets",
    "borrowers",
    "facilities",
    "models",
    "configurations",
    "decisions",
    "findings",
    "finding_events",
    "overrides",
    "approvals",
    "validations",
    "audit_events",
]


def upgrade():
    connection = op.get_bind()
    metadata.create_all(connection)
    connection.exec_driver_sql(
        "INSERT INTO audit_head (id, sequence, hash) VALUES (1, 0, 'GENESIS')"
    )
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql("""CREATE FUNCTION deny_evidence_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Evidence is append-only'; END; $$""")
        for table in IMMUTABLE:
            connection.exec_driver_sql(
                f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION deny_evidence_mutation()"
            )
    else:
        for table in IMMUTABLE:
            for action in ("UPDATE", "DELETE"):
                connection.exec_driver_sql(
                    f"CREATE TRIGGER immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Evidence is append-only'); END"
                )

    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql("""CREATE FUNCTION protect_terminal_run() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
          IF TG_OP = 'DELETE' OR OLD.status <> 'RUNNING' THEN
            RAISE EXCEPTION 'Terminal run is immutable';
          END IF;
          RETURN NEW;
        END; $$""")
        connection.exec_driver_sql(
            "CREATE TRIGGER immutable_terminal_run BEFORE UPDATE OR DELETE ON runs FOR EACH ROW EXECUTE FUNCTION protect_terminal_run()"
        )
    else:
        connection.exec_driver_sql(
            "CREATE TRIGGER immutable_terminal_run BEFORE UPDATE ON runs WHEN OLD.status != 'RUNNING' BEGIN SELECT RAISE(ABORT, 'Terminal run is immutable'); END"
        )
        connection.exec_driver_sql(
            "CREATE TRIGGER immutable_run_delete BEFORE DELETE ON runs BEGIN SELECT RAISE(ABORT, 'Run history cannot be deleted'); END"
        )


def downgrade():
    raise RuntimeError("Destructive downgrade prohibited; restore a verified backup")
