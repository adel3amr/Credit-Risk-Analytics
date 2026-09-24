"""Transaction boundaries for source, calculation, governance and evidence."""

from sqlalchemy import select, update
from . import schema as s, audit, artifacts, risk, validation
from .common import now, uid, digest, application_hash
from .domain import DatasetInput


class Conflict(ValueError):
    pass


class NotFound(ValueError):
    pass


def one(conn, table, id):
    row = conn.execute(select(table).where(table.c.id == id)).mappings().first()
    if row is None:
        raise NotFound("Record not found")
    return dict(row)


def ingest(db, payload, actor):
    payload = normalized(payload)
    data = payload.model_dump(mode="json")
    sha = digest(data)
    warnings = []
    linked = {f["borrower_id"] for f in data["facilities"]}
    for b in data["borrowers"]:
        if b["id"] not in linked:
            warnings.append(
                {"entity": b["id"], "rule": "NO_FACILITIES", "severity": "INFO"}
            )
        if b["observed_at"] < data["effective_date"]:
            warnings.append(
                {"entity": b["id"], "rule": "OLDER_INFORMATION", "severity": "REVIEW"}
            )
    for f in data["facilities"]:
        if f["drawn"] > f["limit"]:
            warnings.append(
                {"entity": f["id"], "rule": "LIMIT_BREACH", "severity": "REVIEW"}
            )
    with db.begin() as conn:
        existing = (
            conn.execute(select(s.datasets).where(s.datasets.c.hash == sha))
            .mappings()
            .first()
        )
        if existing:
            return dict(existing)
        id = uid()
        entry = {
            "id": id,
            "name": data["name"],
            "effective_date": data["effective_date"],
            "recorded_at": now(),
            "source": data["source"],
            "hash": sha,
            "schema_version": "canonical-1",
            "status": "VALID_WITH_WARNINGS" if warnings else "VALID",
            "dq": {"errors": [], "warnings": warnings},
            "actor": actor,
        }
        conn.execute(s.datasets.insert().values(**entry))
        conn.execute(
            s.borrowers.insert(),
            [
                {
                    "dataset_id": id,
                    "id": b["id"],
                    "industry": b["industry"],
                    "payload": b,
                    "source_hash": digest(b),
                }
                for b in data["borrowers"]
            ],
        )
        if data["facilities"]:
            conn.execute(
                s.facilities.insert(),
                [
                    {
                        "dataset_id": id,
                        "id": f["id"],
                        "borrower_id": f["borrower_id"],
                        "product": f["product"],
                        "payload": f,
                        "source_hash": digest(f),
                    }
                    for f in data["facilities"]
                ],
            )
        audit.append(
            conn,
            actor,
            "DATASET_INGEST",
            id,
            {
                "hash": sha,
                "borrowers": len(data["borrowers"]),
                "facilities": len(data["facilities"]),
                "warnings": len(warnings),
            },
        )
    return entry


def dataset(conn, id):
    d = one(conn, s.datasets, id)
    bs = [
        r.payload
        for r in conn.execute(
            select(s.borrowers)
            .where(s.borrowers.c.dataset_id == id)
            .order_by(s.borrowers.c.id)
        )
    ]
    fs = [
        r.payload
        for r in conn.execute(
            select(s.facilities)
            .where(s.facilities.c.dataset_id == id)
            .order_by(s.facilities.c.id)
        )
    ]
    # Input order is normalized at API/CLI ingestion so hashes reconstruct exactly.
    payload = {
        "name": d["name"],
        "effective_date": d["effective_date"],
        "source": d["source"],
        "borrowers": bs,
        "facilities": fs,
    }
    if digest(payload) != d["hash"]:
        raise ValueError("Stored dataset hash mismatch")
    return DatasetInput.model_validate(payload).model_dump(mode="json")


def normalized(payload):
    payload.borrowers.sort(key=lambda b: b.id)
    payload.facilities.sort(key=lambda f: f.id)
    return payload


def execute(db, request, actor):
    req = request.model_dump()
    rh = digest(req)
    with db.begin() as conn:
        old = (
            conn.execute(
                select(s.runs).where(s.runs.c.request_key == request.request_key)
            )
            .mappings()
            .first()
        )
        if old:
            if old["request_hash"] != rh:
                raise Conflict("Idempotency key already used for another request")
            return dict(old)
        one(conn, s.datasets, request.dataset_id)
        run = {
            "id": uid(),
            "request_key": request.request_key,
            "request_hash": rh,
            "dataset_id": request.dataset_id,
            "actor": actor,
            "status": "RUNNING",
            "purpose": request.purpose,
            "started_at": now(),
            "ended_at": None,
            "versions": {
                "application": "0.3.0",
                "application_source_hash": application_hash(),
                "schema": "0001",
                "contract": "canonical-1",
            },
            "summary": {},
            "output_hash": None,
        }
        conn.execute(s.runs.insert().values(**run))
        audit.append(
            conn,
            actor,
            "RUN_START",
            run["id"],
            {"dataset": request.dataset_id, "purpose": request.purpose},
        )
    try:
        if request.purpose == "bank":
            run.update(
                status="BLOCKED",
                summary={
                    "reason": "Synthetic reference models; unresolved LGD findings; no institution qualification"
                },
            )
        else:
            with db.connect() as conn:
                data = dataset(conn, request.dataset_id)
            models, manifest = artifacts.load()
            config = risk.policy()
            traces = risk.score(data, models, manifest, config)
            summary = validation.reconcile(traces)
            summary["monitoring"] = validation.monitor(traces)
            summary["borrowers"] = len(data["borrowers"])
            summary["bank_gate"] = "BLOCKED"
            versions = {
                **run["versions"],
                "models": manifest,
                "configuration": config,
                "configuration_hash": digest(config),
            }
            with db.begin() as conn:
                for family in ("pd", "lgd"):
                    mid = f"{family}:{manifest['artifacts'][family]}"
                    if (
                        conn.execute(
                            select(s.models.c.id).where(s.models.c.id == mid)
                        ).first()
                        is None
                    ):
                        conn.execute(
                            s.models.insert().values(
                                id=mid,
                                family=family,
                                version=manifest["version"],
                                status="REFERENCE",
                                manifest=manifest,
                                recorded_at=now(),
                            )
                        )
                cid = digest(config)
                if (
                    conn.execute(
                        select(s.configurations.c.id).where(
                            s.configurations.c.id == cid
                        )
                    ).first()
                    is None
                ):
                    conn.execute(
                        s.configurations.insert().values(
                            id=cid,
                            kind="policy_and_scenarios",
                            hash=cid,
                            payload=config,
                            recorded_at=now(),
                        )
                    )
                if traces:
                    conn.execute(
                        s.decisions.insert(),
                        [
                            {
                                "run_id": run["id"],
                                **{
                                    k: t[k]
                                    for k in (
                                        "facility_id",
                                        "borrower_id",
                                        "stage",
                                        "pd",
                                        "lgd",
                                        "ead",
                                        "ecl",
                                    )
                                },
                                "trace": t,
                                "hash": digest(t),
                            }
                            for t in traces
                        ],
                    )
                run.update(
                    status="SUCCEEDED",
                    summary=summary,
                    versions=versions,
                    output_hash=digest(traces),
                    ended_at=now(),
                )
                conn.execute(
                    update(s.runs).where(s.runs.c.id == run["id"]).values(**run)
                )
                audit.append(
                    conn,
                    actor,
                    "RUN_SUCCEEDED",
                    run["id"],
                    {"output_hash": run["output_hash"], "facilities": len(traces)},
                )
            return run
    except Exception as exc:
        run.update(
            status="FAILED",
            summary={"error_type": type(exc).__name__, "reason": str(exc)[:500]},
        )
    run["ended_at"] = now()
    with db.begin() as conn:
        conn.execute(update(s.runs).where(s.runs.c.id == run["id"]).values(**run))
        audit.append(conn, actor, "RUN_" + run["status"], run["id"], run["summary"])
    return run


def traces(conn, run_id):
    one(conn, s.runs, run_id)
    rows = (
        conn.execute(
            select(s.decisions)
            .where(s.decisions.c.run_id == run_id)
            .order_by(s.decisions.c.facility_id)
        )
        .mappings()
        .all()
    )
    for row in rows:
        if digest(row["trace"]) != row["hash"]:
            raise ValueError("Decision hash mismatch")
    return [row["trace"] for row in rows]


def propose(db, payload, actor):
    with db.begin() as conn:
        row = (
            conn.execute(
                select(s.decisions).where(
                    s.decisions.c.run_id == payload.run_id,
                    s.decisions.c.facility_id == payload.facility_id,
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise NotFound("Decision not found")
        if payload.proposed_ecl > row["ead"]:
            raise ValueError("Override ECL exceeds EAD")
        entry = {
            **payload.model_dump(),
            "id": uid(),
            "proposer": actor,
            "original_ecl": row["ecl"],
            "recorded_at": now(),
        }
        conn.execute(s.overrides.insert().values(**entry))
        audit.append(
            conn, actor, "OVERRIDE_PROPOSED", entry["id"], {"run": payload.run_id}
        )
    return entry


def approve(db, id, decision, actor):
    with db.begin() as conn:
        proposed = one(conn, s.overrides, id)
        if proposed["proposer"] == actor:
            raise Conflict("A different manager must approve")
        entry = {
            "override_id": id,
            "approver": actor,
            "decision": decision,
            "recorded_at": now(),
        }
        conn.execute(s.approvals.insert().values(**entry))
        audit.append(
            conn, actor, "OVERRIDE_" + decision, id, {"original_preserved": True}
        )
    return entry


def portfolio(conn, run_id):
    run = one(conn, s.runs, run_id)
    if run["status"] != "SUCCEEDED":
        raise Conflict("Run has no successful portfolio")
    t = traces(conn, run_id)
    result = validation.reconcile(t)
    result["concentrations"] = validation.concentrations(t)
    applied = (
        conn.execute(
            select(s.overrides, s.approvals.c.approver)
            .join(s.approvals, s.approvals.c.override_id == s.overrides.c.id)
            .where(s.overrides.c.run_id == run_id, s.approvals.c.decision == "APPROVED")
        )
        .mappings()
        .all()
    )
    result["reference_ecl"] = result["ecl"]
    result["override_adjustment"] = sum(
        x["proposed_ecl"] - x["original_ecl"] for x in applied
    )
    result["controlled_reference_ecl"] = result["ecl"] + result["override_adjustment"]
    result["approved_overrides"] = [dict(x) for x in applied]
    result["bank_gate"] = "BLOCKED"
    return result
