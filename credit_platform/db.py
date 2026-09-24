import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool


def engine(url=None):
    url = url or os.environ.get("DATABASE_URL", "sqlite:///platform.db")
    kw = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if ":memory:" in url:
            kw["poolclass"] = StaticPool
    result = create_engine(url, **kw)
    if url.startswith("sqlite"):

        @event.listens_for(result, "connect")
        def sqlite_setup(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")

    return result


def require_schema(db):
    with db.connect() as conn:
        version = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        if version != "0001":
            raise RuntimeError("Unsupported schema version; apply migrations")
