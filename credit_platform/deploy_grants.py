"""Migration-owner command, not exposed through the API."""

from .db import engine
from .common import ROOT

with engine().begin() as conn:
    if conn.dialect.name != "postgresql":
        raise RuntimeError("PostgreSQL grants only")
    conn.exec_driver_sql((ROOT / "deployment/grants.sql").read_text())
