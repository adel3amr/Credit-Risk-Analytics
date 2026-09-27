"""Portable relational schema. Payloads are immutable, versioned source snapshots."""

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Float,
    JSON,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    CheckConstraint,
)

metadata = MetaData()


def c(name, type_=String, **kw):
    return Column(name, type_, nullable=False, **kw)


principals = Table(
    "principals",
    metadata,
    c("id", primary_key=True),
    c("name", unique=True),
    c("role"),
    c("token_hash", unique=True),
    c("active", Integer),
    c("expires_at"),
    c("created_at"),
    CheckConstraint("role in ('analyst','manager','validator','audit','admin')"),
    CheckConstraint("active in (0,1)"),
)
datasets = Table(
    "datasets",
    metadata,
    c("id", primary_key=True),
    c("name"),
    c("effective_date"),
    c("recorded_at"),
    c("source"),
    c("hash", unique=True),
    c("schema_version"),
    c("status"),
    c("dq", JSON),
    c("actor", ForeignKey("principals.id")),
)
borrowers = Table(
    "borrowers",
    metadata,
    c("dataset_id", ForeignKey("datasets.id"), primary_key=True),
    c("id", primary_key=True),
    c("industry"),
    c("payload", JSON),
    c("source_hash"),
)
facilities = Table(
    "facilities",
    metadata,
    c("dataset_id", primary_key=True),
    c("id", primary_key=True),
    c("borrower_id"),
    c("product"),
    c("payload", JSON),
    c("source_hash"),
    ForeignKeyConstraint(
        ["dataset_id", "borrower_id"], ["borrowers.dataset_id", "borrowers.id"]
    ),
)
models = Table(
    "models",
    metadata,
    c("id", primary_key=True),
    c("family"),
    c("version"),
    c("status"),
    c("manifest", JSON),
    c("recorded_at"),
    CheckConstraint("status in ('REFERENCE','BLOCKED','RESEARCH','RETIRED')"),
)
configurations = Table(
    "configurations",
    metadata,
    c("id", primary_key=True),
    c("kind"),
    c("hash"),
    c("payload", JSON),
    c("recorded_at"),
)
runs = Table(
    "runs",
    metadata,
    c("id", primary_key=True),
    c("request_key", unique=True),
    c("request_hash"),
    c("dataset_id", ForeignKey("datasets.id")),
    c("actor", ForeignKey("principals.id")),
    c("status"),
    c("purpose"),
    c("started_at"),
    Column("ended_at", String),
    c("versions", JSON),
    c("summary", JSON),
    Column("output_hash", String),
    CheckConstraint("status in ('RUNNING','SUCCEEDED','FAILED','BLOCKED')"),
    CheckConstraint("purpose in ('reference','bank')"),
)
decisions = Table(
    "decisions",
    metadata,
    c("run_id", ForeignKey("runs.id"), primary_key=True),
    c("facility_id", primary_key=True),
    c("borrower_id"),
    c("stage"),
    c("pd", Float),
    c("lgd", Float),
    c("ead", Float),
    c("ecl", Float),
    c("trace", JSON),
    c("hash"),
    CheckConstraint("stage in ('Stage 1','Stage 2','Stage 3')"),
    CheckConstraint(
        "pd >= 0 and pd <= 1 and lgd >= 0 and lgd <= 1 and ead >= 0 and ecl >= 0"
    ),
)
findings = Table(
    "findings",
    metadata,
    c("id", primary_key=True),
    c("component"),
    c("severity"),
    c("description"),
    c("evidence", JSON),
    c("owner"),
    c("recorded_at"),
)
finding_events = Table(
    "finding_events",
    metadata,
    c("id", primary_key=True),
    c("finding_id", ForeignKey("findings.id")),
    c("status"),
    c("note"),
    c("actor", ForeignKey("principals.id")),
    c("recorded_at"),
)
overrides = Table(
    "overrides",
    metadata,
    c("id", primary_key=True),
    c("run_id"),
    c("facility_id"),
    c("proposer", ForeignKey("principals.id")),
    c("original_ecl", Float),
    c("proposed_ecl", Float),
    c("reason"),
    c("recorded_at"),
    ForeignKeyConstraint(
        ["run_id", "facility_id"], ["decisions.run_id", "decisions.facility_id"]
    ),
    CheckConstraint("proposed_ecl >= 0"),
    UniqueConstraint("run_id", "facility_id"),
)
approvals = Table(
    "approvals",
    metadata,
    c("override_id", ForeignKey("overrides.id"), primary_key=True),
    c("approver", ForeignKey("principals.id")),
    c("decision"),
    c("recorded_at"),
    CheckConstraint("decision in ('APPROVED','REJECTED')"),
)
validations = Table(
    "validations",
    metadata,
    c("id", primary_key=True),
    c("run_id", ForeignKey("runs.id")),
    c("kind"),
    c("payload", JSON),
    c("hash"),
    c("actor", ForeignKey("principals.id")),
    c("recorded_at"),
)
copilot_requests = Table(
    "copilot_requests",
    metadata,
    c("id", primary_key=True),
    c("request_id", unique=True),
    c("actor", ForeignKey("principals.id")),
    c("role"),
    c("use_case"),
    Column("run_id", String, ForeignKey("runs.id")),
    Column("borrower_id", String),
    c("question_hash"),
    c("provider"),
    c("provider_version"),
    c("prompt_version"),
    c("status"),
    c("tool_calls", JSON),
    c("sources", JSON),
    c("response_hash"),
    c("recorded_at"),
    CheckConstraint(
        "use_case in ('borrower','portfolio','model_risk','credit_review')"
    ),
    CheckConstraint("status in ('ANSWERED','REFUSED','INSUFFICIENT_EVIDENCE')"),
)
audit_head = Table(
    "audit_head",
    metadata,
    c("id", Integer, primary_key=True),
    c("sequence", Integer),
    c("hash"),
)
audit_events = Table(
    "audit_events",
    metadata,
    c("sequence", Integer, primary_key=True),
    c("actor"),
    c("action"),
    c("entity"),
    c("recorded_at"),
    c("details", JSON),
    c("previous_hash"),
    c("hash", unique=True),
)

# Lookup paths used by portfolio and point-in-time history.
from sqlalchemy import Index

Index("ix_runs_dataset", runs.c.dataset_id)
Index("ix_decisions_borrower", decisions.c.borrower_id)
Index("ix_facilities_borrower", facilities.c.dataset_id, facilities.c.borrower_id)
Index("ix_datasets_effective", datasets.c.effective_date, datasets.c.recorded_at)
