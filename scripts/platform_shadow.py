"""Rebuildable full reference shadow comparison and worked facility cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import time
import pandas as pd
from sqlalchemy import select
from credit_platform import service, security, schema as s, audit
from credit_platform.db import engine, require_schema
from credit_platform.cli import map_reference
from credit_platform.domain import RunInput
from credit_platform.common import atomic_json, ROOT, uid


def main():
    start = time.monotonic()
    db = engine()
    require_schema(db)
    name = "shadow-" + uid()
    security.issue(db, name, "analyst")
    with db.connect() as c:
        actor = c.execute(
            select(s.principals.c.id).where(s.principals.c.name == name)
        ).scalar_one()
    data = map_reference()
    d = service.ingest(db, data, actor)
    r = service.execute(
        db, RunInput(dataset_id=d["id"], request_key="shadow-" + uid()), actor
    )
    if r["status"] != "SUCCEEDED":
        raise RuntimeError(r["summary"])
    with db.connect() as c:
        traces = service.traces(c, r["id"])
        audit_result = audit.verify(c)
    new = pd.DataFrame(traces).set_index("facility_id")
    old = (
        pd.read_csv(ROOT / "outputs/facility_ecl_predictions.csv")
        .set_index("facility_id")
        .reindex(new.index)
    )
    b = pd.read_csv(ROOT / "outputs/borrower_audit_trace.csv").set_index("customer_id")
    pd_error = max(
        abs(t["pit_pd"] - b.loc[t["borrower_id"], "predicted_pd"]) for t in traces
    )
    report = {
        "run_id": r["id"],
        "dataset_hash": d["hash"],
        "elapsed_seconds": time.monotonic() - start,
        "facilities": len(new),
        "ead": float(new.ead.sum()),
        "ecl": float(new.ecl.sum()),
        "max_ead_difference": float((new.ead - old.ead_at_default).abs().max()),
        "max_ecl_difference": float((new.ecl - old.facility_ecl).abs().max()),
        "max_lgd_difference": float((new.lgd - old.predicted_lgd).abs().max()),
        "max_pd_difference": float(pd_error),
        "stage_mismatches": int((new.stage != old.stage).sum()),
        "audit": audit_result,
        "rounding_note": "Historical face and converted EAD stored independently to two decimals; canonical conversion from stored face can differ by one cent.",
    }
    assert (
        report["stage_mismatches"] == 0
        and pd_error < 1e-12
        and report["max_lgd_difference"] < 1e-12
    )
    assert report["max_ead_difference"] < 0.011 and report["max_ecl_difference"] < 0.011
    atomic_json(ROOT / "platform_evidence/shadow_execution.json", report)
    cases = {}
    for label, predicate in [
        ("healthy_stage1", lambda t: t["stage"] == "Stage 1" and not t["watchlist"]),
        ("watchlist_stage1", lambda t: t["stage"] == "Stage 1" and t["watchlist"]),
        ("stage2", lambda t: t["stage"] == "Stage 2"),
        ("default", lambda t: t["stage"] == "Stage 3"),
        ("secured", lambda t: t["source_facility"]["collateral_coverage"] >= 1),
        ("unsecured", lambda t: t["source_facility"]["collateral_type"] == "Unsecured"),
        ("guaranteed", lambda t: t["source_facility"]["guarantee_coverage"] > 0),
    ]:
        cases[label] = next(t for t in traces if predicate(t))
    cases["high_lgd"] = max(traces, key=lambda t: t["lgd"])
    cases["high_ead"] = max(traces, key=lambda t: t["ead"])
    cases["high_ecl"] = max(traces, key=lambda t: t["ecl"])
    atomic_json(
        ROOT / "platform_evidence/worked_cases.json",
        {"run": r["id"], "dataset_hash": d["hash"], "cases": cases},
    )
    security.revoke(db, name)
    print(report)


if __name__ == "__main__":
    main()
