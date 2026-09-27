"""Add immutable, metadata-only Copilot request evidence."""

from alembic import op
from sqlalchemy import Column, String, JSON, ForeignKey, CheckConstraint

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "copilot_requests",
        Column("id", String, primary_key=True, nullable=False),
        Column("request_id", String, unique=True, nullable=False),
        Column("actor", String, ForeignKey("principals.id"), nullable=False),
        Column("role", String, nullable=False),
        Column("use_case", String, nullable=False),
        Column("run_id", String, ForeignKey("runs.id")),
        Column("borrower_id", String),
        Column("question_hash", String, nullable=False),
        Column("provider", String, nullable=False),
        Column("provider_version", String, nullable=False),
        Column("prompt_version", String, nullable=False),
        Column("status", String, nullable=False),
        Column("tool_calls", JSON, nullable=False),
        Column("sources", JSON, nullable=False),
        Column("response_hash", String, nullable=False),
        Column("recorded_at", String, nullable=False),
        CheckConstraint("use_case in ('borrower','portfolio','model_risk','credit_review')"),
        CheckConstraint("status in ('ANSWERED','REFUSED','INSUFFICIENT_EVIDENCE')"),
    )
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "CREATE TRIGGER immutable_copilot_requests BEFORE UPDATE OR DELETE ON copilot_requests FOR EACH ROW EXECUTE FUNCTION deny_evidence_mutation()"
        )
    else:
        for action in ("UPDATE", "DELETE"):
            connection.exec_driver_sql(
                f"CREATE TRIGGER immutable_copilot_requests_{action} BEFORE {action} ON copilot_requests BEGIN SELECT RAISE(ABORT, 'Evidence is append-only'); END"
            )


def downgrade():
    raise RuntimeError("Destructive downgrade prohibited; restore a verified backup")
