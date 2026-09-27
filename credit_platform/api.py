import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from . import schema as s, service, audit, validation, artifacts, risk, copilot
from .db import engine, require_schema
from .security import allow, principal
from .domain import (
    DatasetInput,
    RunInput,
    OverrideInput,
    ApprovalInput,
    FindingInput,
    FindingEventInput,
    OutcomesInput,
    CopilotInput,
)
from .common import now, uid, digest

log = logging.getLogger("credit_platform")


def create_app(db=None):
    app = FastAPI(
        title="Credit Risk Reference Platform",
        version="0.4.0",
        description="Synthetic reference use. Bank production gate BLOCKED.",
    )
    app.state.db = db or engine()

    @app.middleware("http")
    async def operational(request, call_next):
        correlation = uid()
        start = time.monotonic()
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 32 * 1024 * 1024):
            return JSONResponse(
                {"detail": "Request too large or invalid length"}, status_code=413
            )
        received = 0
        receive = request._receive

        async def limited():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > 32 * 1024 * 1024:
                raise HTTPException(413, "Request too large")
            return message

        request._receive = limited
        response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": correlation,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
            }
        )
        # Route templates avoid logging borrower identifiers, payloads or tokens.
        route = getattr(request.scope.get("route"), "path", "unmatched")
        log.info(
            json.dumps(
                {
                    "request_id": correlation,
                    "route": route,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - start) * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(service.NotFound)
    async def notfound(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(service.Conflict)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(IntegrityError)
    async def integrity(request, exc):
        return JSONResponse(
            {"detail": "Uniqueness or relationship conflict"}, status_code=409
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        log.error(json.dumps({"event": "database_failure", "type": type(exc).__name__}))
        return JSONResponse(
            {"detail": "Database unavailable or schema invalid"}, status_code=503
        )

    @app.exception_handler(RequestValidationError)
    async def bad_request(request, exc):
        errors = [
            {"location": list(e["loc"]), "type": e["type"], "message": e["msg"]}
            for e in exc.errors()
        ]
        # Persist rejection evidence without retaining arbitrary rejected payloads.
        try:
            with app.state.db.begin() as conn:
                audit.append(
                    conn, "request", "INPUT_REJECTED", uid(), {"errors": errors}
                )
        except SQLAlchemyError:
            log.error("DQ rejection audit unavailable")
        return JSONResponse({"detail": errors}, status_code=422)

    @app.get("/health/live")
    def live():
        return {"status": "UP", "version": "0.4.0"}

    @app.get("/health/ready")
    def ready():
        try:
            require_schema(app.state.db)
            artifacts.load()
            risk.policy()
        except Exception:
            return JSONResponse({"status": "NOT_READY"}, status_code=503)
        return {"status": "READY", "bank_gate": "BLOCKED"}

    @app.get("/")
    def ui():
        return FileResponse(Path(__file__).parent / "static/index.html")

    @app.get("/static/{name}")
    def asset(name: str):
        if name not in ("app.js", "style.css"):
            raise HTTPException(404)
        return FileResponse(Path(__file__).parent / "static" / name)

    @app.get("/api/v1/me")
    def me(p=Depends(principal)):
        return {k: p[k] for k in ("id", "name", "role", "expires_at")}

    @app.get("/api/v1/validation-reference")
    def reference_validation(p=Depends(allow("read"))):
        from .common import ROOT, file_hash

        baseline_path = ROOT / "platform_evidence/independent_reconciliation.json"
        research_path = ROOT / "platform_evidence/research_recalculated.json"
        baseline = json.loads(baseline_path.read_text())
        research = json.loads(research_path.read_text())
        rows = [
            {
                "model": "PD V5 logistic",
                "population": "H holdout",
                "n": 3000,
                **baseline["pd_metrics"],
                "status": "REFERENCE, bank BLOCKED",
                "source_hash": file_hash(baseline_path),
            }
        ]
        rows += [
            {
                "model": name,
                "population": "R2 final, synthetic",
                **metrics,
                "status": "RESEARCH, bank BLOCKED",
                "source_hash": file_hash(research_path),
            }
            for name, metrics in research.items()
        ]
        return rows

    @app.get("/api/v1/gates")
    def gates(p=Depends(allow("read"))):
        return {
            "bank_use": "BLOCKED",
            "model_promotion": "BLOCKED",
            "reference_use": "ALLOWED",
            "reasons": [
                "Synthetic-only evidence",
                "Unresolved severe LGD and feature support",
                "No institution qualification or independent deployment approval",
            ],
        }

    @app.post("/api/v1/copilot/query")
    def copilot_query(data: CopilotInput, p=Depends(allow("read"))):
        return copilot.answer(app.state.db, data, p)

    @app.get("/api/v1/lgd-economic-validation")
    def economic_validation(p=Depends(allow("read"))):
        from .economic_evidence import get
        evidence, source = get()
        return [{**row, "status": evidence["status"], "source": source}
                for row in evidence["metrics"]]

    @app.post("/api/v1/datasets", status_code=201)
    def ingest(data: DatasetInput, p=Depends(allow("ingest"))):
        return service.ingest(app.state.db, service.normalized(data), p["id"])

    @app.post("/api/v1/runs")
    def run(data: RunInput, p=Depends(allow("run"))):
        return service.execute(app.state.db, data, p["id"])

    @app.get("/api/v1/runs/{id}")
    def get_run(id: str, p=Depends(allow("read"))):
        with app.state.db.connect() as conn:
            return service.one(conn, s.runs, id)

    @app.get("/api/v1/runs/{id}/portfolio")
    def portfolio(id: str, p=Depends(allow("read"))):
        with app.state.db.connect() as conn:
            return service.portfolio(conn, id)

    @app.get("/api/v1/runs/{id}/decisions")
    def decisions(
        id: str,
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        p=Depends(allow("read")),
    ):
        with app.state.db.connect() as conn:
            service.one(conn, s.runs, id)
            return [
                dict(r)
                for r in conn.execute(
                    select(s.decisions)
                    .where(s.decisions.c.run_id == id)
                    .order_by(s.decisions.c.facility_id)
                    .limit(limit)
                    .offset(offset)
                ).mappings()
            ]

    @app.get("/api/v1/runs/{id}/facilities/{facility_id}")
    def trace(id: str, facility_id: str, p=Depends(allow("read"))):
        with app.state.db.connect() as conn:
            row = (
                conn.execute(
                    select(s.decisions).where(
                        s.decisions.c.run_id == id,
                        s.decisions.c.facility_id == facility_id,
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise service.NotFound("Decision not found")
            return dict(row)

    @app.get("/api/v1/borrowers/{borrower_id}/history")
    def history(
        borrower_id: str,
        as_of: date,
        known_at: datetime,
        limit: int = Query(100, ge=1, le=500),
        p=Depends(allow("read")),
    ):
        if known_at.tzinfo is None:
            raise ValueError("known_at requires timezone")
        from datetime import timezone

        cutoff = known_at.astimezone(timezone.utc).isoformat()
        with app.state.db.connect() as conn:
            query = (
                select(
                    s.decisions.c.run_id,
                    s.decisions.c.facility_id,
                    s.decisions.c.stage,
                    s.decisions.c.trace,
                    s.datasets.c.effective_date,
                    s.datasets.c.recorded_at,
                )
                .join(s.runs, s.runs.c.id == s.decisions.c.run_id)
                .join(s.datasets, s.datasets.c.id == s.runs.c.dataset_id)
                .where(
                    s.decisions.c.borrower_id == borrower_id,
                    s.datasets.c.effective_date <= as_of.isoformat(),
                    s.datasets.c.recorded_at <= cutoff,
                    s.runs.c.ended_at <= cutoff,
                )
                .order_by(
                    s.datasets.c.effective_date,
                    s.datasets.c.recorded_at,
                    s.runs.c.ended_at,
                )
                .limit(limit)
            )
            return [dict(r) for r in conn.execute(query).mappings()]

    @app.get("/api/v1/runs/{id}/monitoring")
    def monitor(id: str, p=Depends(allow("read"))):
        with app.state.db.connect() as conn:
            return validation.monitor(service.traces(conn, id))

    @app.get("/api/v1/runs/{id}/movement/{previous_id}")
    def movement(id: str, previous_id: str, p=Depends(allow("read"))):
        with app.state.db.connect() as conn:
            for rid in (id, previous_id):
                if service.one(conn, s.runs, rid)["status"] != "SUCCEEDED":
                    raise service.Conflict("Successful runs required")
            return validation.movements(
                service.traces(conn, previous_id), service.traces(conn, id)
            )

    @app.post("/api/v1/runs/{id}/validation")
    def validate(id: str, p=Depends(allow("validate"))):
        with app.state.db.begin() as conn:
            payload = validation.reconcile(service.traces(conn, id))
            record = {
                "id": uid(),
                "run_id": id,
                "kind": "independent_ecl",
                "payload": payload,
                "hash": digest(payload),
                "actor": p["id"],
                "recorded_at": now(),
            }
            conn.execute(s.validations.insert().values(**record))
            audit.append(conn, p["id"], "VALIDATION", record["id"], {"run": id})
            return record

    @app.post("/api/v1/runs/{id}/outcomes")
    def outcomes(id: str, data: OutcomesInput, p=Depends(allow("validate"))):
        with app.state.db.begin() as conn:
            traces = {t["facility_id"]: t for t in service.traces(conn, id)}
            ids = [o.facility_id for o in data.outcomes]
            if len(ids) != len(set(ids)) or any(i not in traces for i in ids):
                raise ValueError("Duplicate or unknown outcome facility")
            for o in data.outcomes:
                if o.resolved_at.isoformat() < traces[o.facility_id]["reporting_date"]:
                    raise ValueError("Outcome precedes forecast")
            payload = {
                "metrics": validation.loss_metrics(
                    [o.realized_lgd for o in data.outcomes],
                    [traces[i]["lgd"] for i in ids],
                    [traces[i]["ead"] for i in ids],
                ),
                "outcomes": data.model_dump(mode="json"),
                "coverage": len(ids) / len(traces),
                "outcome_selection": "submitted resolved subset; selection bias possible",
            }
            record = {
                "id": uid(),
                "run_id": id,
                "kind": "lgd_outcomes",
                "payload": payload,
                "hash": digest(payload),
                "actor": p["id"],
                "recorded_at": now(),
            }
            conn.execute(s.validations.insert().values(**record))
            audit.append(
                conn,
                p["id"],
                "OUTCOME_VALIDATION",
                record["id"],
                {"run": id, "n": len(ids)},
            )
            return record

    @app.post("/api/v1/overrides", status_code=201)
    def override(data: OverrideInput, p=Depends(allow("override"))):
        return service.propose(app.state.db, data, p["id"])

    @app.post("/api/v1/overrides/{id}/approval")
    def approval(id: str, data: ApprovalInput, p=Depends(allow("approve"))):
        return service.approve(app.state.db, id, data.decision, p["id"])

    @app.post("/api/v1/findings", status_code=201)
    def finding(data: FindingInput, p=Depends(allow("finding"))):
        record = {**data.model_dump(), "id": uid(), "recorded_at": now()}
        with app.state.db.begin() as conn:
            conn.execute(s.findings.insert().values(**record))
            audit.append(
                conn,
                p["id"],
                "FINDING_CREATED",
                record["id"],
                {"component": data.component, "severity": data.severity},
            )
        return record

    @app.post("/api/v1/findings/{id}/events", status_code=201)
    def finding_event(id: str, data: FindingEventInput, p=Depends(allow("finding"))):
        with app.state.db.begin() as conn:
            service.one(conn, s.findings, id)
            record = {
                **data.model_dump(),
                "id": uid(),
                "finding_id": id,
                "actor": p["id"],
                "recorded_at": now(),
            }
            conn.execute(s.finding_events.insert().values(**record))
            audit.append(conn, p["id"], "FINDING_EVENT", id, {"status": data.status})
        return record

    @app.get("/api/v1/audit/verify")
    def audit_verify(p=Depends(allow("audit"))):
        with app.state.db.connect() as conn:
            return audit.verify(conn)

    def collection(table, permission="read"):
        def endpoint(
            limit: int = Query(100, ge=1, le=500),
            offset: int = Query(0, ge=0),
            p=Depends(allow(permission)),
        ):
            with app.state.db.connect() as conn:
                return [
                    dict(r)
                    for r in conn.execute(
                        select(table)
                        .order_by(*table.primary_key.columns)
                        .limit(limit)
                        .offset(offset)
                    ).mappings()
                ]

        return endpoint

    for name, table in [
        ("datasets", s.datasets),
        ("borrowers", s.borrowers),
        ("facilities", s.facilities),
        ("runs", s.runs),
        ("models", s.models),
        ("scenarios", s.configurations),
        ("findings", s.findings),
        ("finding-events", s.finding_events),
        ("overrides", s.overrides),
        ("approvals", s.approvals),
        ("validation", s.validations),
    ]:
        app.add_api_route(
            "/api/v1/" + name, collection(table), methods=["GET"], name=name
        )
    app.add_api_route(
        "/api/v1/audit", collection(s.audit_events, "audit"), methods=["GET"]
    )
    app.add_api_route(
        "/api/v1/copilot/requests",
        collection(s.copilot_requests, "audit"),
        methods=["GET"],
    )
    return app


app = create_app()
