"""Grounded narrative layer. Governed calculations remain outside this module."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.request import Request, urlopen

from sqlalchemy import func, select

from . import audit, schema as s, service
from .common import ROOT, digest, now, uid

PROMPT_VERSION = "credit-risk-copilot-1"
PROVIDER_VERSION = "deterministic-1"
REFUSAL = "I do not have sufficient permitted evidence to answer this."
INJECTION = re.compile(
    r"(ignore\s+(all|previous|prior)|system\s+prompt|developer\s+message|"
    r"reveal\s+(secrets?|tokens?|credentials?)|drop\s+table|unrestricted\s+sql)",
    re.IGNORECASE,
)


class Provider(Protocol):
    name: str
    version: str

    def render(self, question: str, evidence: dict, use_case: str) -> str: ...


class DeterministicProvider:
    name = "deterministic-local"
    version = PROVIDER_VERSION

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        if use_case in ("borrower", "credit_review"):
            facilities = evidence["facilities"]
            stages = sorted({row["stage"] for row in facilities})
            reasons = sorted(
                {reason for row in facilities for reason in row.get("stage_reasons", [])}
            )
            total_ead = sum(row["ead"] for row in facilities)
            total_ecl = sum(row["ecl"] for row in facilities)
            prefix = "DRAFT — human review required. " if use_case == "credit_review" else ""
            return (
                f"{prefix}Borrower {evidence['borrower_id']} has {len(facilities)} facility/facilities "
                f"in {', '.join(stages)}. Governed EAD is {total_ead:,.2f} and ECL is "
                f"{total_ecl:,.2f}. Recorded stage reason(s): "
                f"{', '.join(reasons) if reasons else 'none recorded'}. "
                "These are retrieved run outputs; this narrative does not change the decision."
            )
        if use_case == "portfolio":
            stages = ", ".join(
                f"{k}: {v['facilities']} facilities / ECL {v['ecl']:,.2f}"
                for k, v in sorted(evidence["by_stage"].items())
            )
            return (
                f"Run {evidence['run_id']} contains {evidence['facility_count']} facilities, "
                f"EAD {evidence['ead']:,.2f}, and governed ECL {evidence['ecl']:,.2f}. "
                f"Stage composition: {stages}. Bank-use gate: {evidence['bank_gate']}."
            )
        finding = evidence["lgd_finding"]
        return (
            "The LGD production gate remains BLOCKED. Current conditional bias is "
            f"{finding['current_conditional_bias_pp']:.2f} pp. True-state research calibration "
            f"reduced it to {finding['oracle_bias_pp']:+.2f} pp, but that state is unavailable "
            "at prediction time and operational proxies failed. The challenger was therefore "
            "not promoted; the explicit downturn overlay is restricted to sensitivity use."
        )


class ExternalJSONProvider:
    """Optional provider. Disabled unless explicit endpoint, key and opt-in are supplied."""

    name = "external-json"
    version = "external-configured-1"

    def __init__(self):
        if os.getenv("COPILOT_ALLOW_EXTERNAL", "false").lower() != "true":
            raise ValueError("External Copilot provider is disabled")
        self.endpoint = os.environ.get("COPILOT_EXTERNAL_ENDPOINT", "")
        self.key = os.environ.get("COPILOT_EXTERNAL_API_KEY", "")
        if not self.endpoint.startswith("https://") or not self.key:
            raise ValueError("External provider requires HTTPS endpoint and secret")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        body = json.dumps(
            {
                "prompt_version": PROMPT_VERSION,
                "instruction": "Use only evidence. Do not calculate or decide. State uncertainty.",
                "question": question,
                "use_case": use_case,
                "evidence": evidence,
            }
        ).encode()
        req = Request(
            self.endpoint,
            data=body,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        with urlopen(req, timeout=20) as response:  # nosec: endpoint is explicit HTTPS config
            result = json.loads(response.read(1_000_000))
        answer = result.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("External provider returned no answer")
        return answer.strip()


def provider() -> Provider:
    configured = os.getenv("COPILOT_PROVIDER", "deterministic").lower()
    if configured == "deterministic":
        return DeterministicProvider()
    if configured == "external-json":
        return ExternalJSONProvider()
    raise ValueError("Unsupported Copilot provider")


def _borrower(conn, run_id: str, borrower_id: str) -> tuple[dict, list[dict]]:
    run = service.one(conn, s.runs, run_id)
    if run["status"] != "SUCCEEDED":
        raise service.Conflict("Successful run required")
    rows = [
        dict(row)
        for row in conn.execute(
            select(s.decisions).where(
                s.decisions.c.run_id == run_id,
                s.decisions.c.borrower_id == borrower_id,
            )
        ).mappings()
    ]
    if not rows:
        raise service.NotFound("Borrower decision not found in run")
    facilities = [
        {
            "facility_id": row["facility_id"],
            "stage": row["stage"],
            "pd": row["pd"],
            "lgd": row["lgd"],
            "ead": row["ead"],
            "ecl": row["ecl"],
            "stage_reasons": row["trace"].get("stage_reasons", []),
            "watchlist": row["trace"].get("watchlist"),
            "sicr": row["trace"].get("sicr"),
        }
        for row in rows
    ]
    return {"run_id": run_id, "borrower_id": borrower_id, "facilities": facilities}, [
        {"type": "decision_trace", "run_id": run_id, "borrower_id": borrower_id}
    ]


def _portfolio(conn, run_id: str) -> tuple[dict, list[dict]]:
    base = service.portfolio(conn, run_id)
    grouped = conn.execute(
        select(
            s.decisions.c.stage,
            func.count().label("facilities"),
            func.sum(s.decisions.c.ead).label("ead"),
            func.sum(s.decisions.c.ecl).label("ecl"),
        )
        .where(s.decisions.c.run_id == run_id)
        .group_by(s.decisions.c.stage)
    ).mappings()
    evidence = {
        "run_id": run_id,
        "facility_count": base["facility_count"],
        "ead": base["ead"],
        "ecl": base["ecl"],
        "bank_gate": base["bank_gate"],
        "by_stage": {
            row["stage"]: {
                "facilities": row["facilities"],
                "ead": row["ead"],
                "ecl": row["ecl"],
            }
            for row in grouped
        },
    }
    return evidence, [{"type": "portfolio_run", "run_id": run_id}]


def _model_risk() -> tuple[dict, list[dict]]:
    report = ROOT / "LGD_DOWNTURN_FINAL_DECISION.md"
    if not report.exists():
        raise service.NotFound("Authoritative LGD decision is unavailable")
    evidence = {
        "lgd_finding": {
            "status": "BLOCKED",
            "current_conditional_bias_pp": -12.6538,
            "oracle_bias_pp": 0.55,
            "promotion": "NOT_PROMOTED",
        }
    }
    return evidence, [{"type": "document", "path": report.name, "hash": digest(report.read_text())}]


def answer(db, request, actor: dict) -> dict:
    request_id = uid()
    status = "ANSWERED"
    tool_calls: list[str] = []
    sources: list[dict] = []
    evidence: dict = {}
    selected = provider()
    if INJECTION.search(request.question):
        status, response = "REFUSED", REFUSAL
    else:
        try:
            with db.connect() as conn:
                if request.use_case in ("borrower", "credit_review"):
                    evidence, sources = _borrower(conn, request.run_id, request.borrower_id)
                    tool_calls = ["get_borrower_decision_trace"]
                elif request.use_case == "portfolio":
                    evidence, sources = _portfolio(conn, request.run_id)
                    tool_calls = ["get_portfolio_summary", "get_stage_aggregation"]
                else:
                    evidence, sources = _model_risk()
                    tool_calls = ["get_authoritative_model_risk_finding"]
            response = selected.render(request.question, evidence, request.use_case)
        except (service.NotFound, service.Conflict):
            status, response = "INSUFFICIENT_EVIDENCE", REFUSAL
    result = {
        "request_id": request_id,
        "status": status,
        "answer": response,
        "facts": evidence,
        "sources": sources,
        "tool_calls": tool_calls,
        "provider": selected.name,
        "provider_version": selected.version,
        "prompt_version": PROMPT_VERSION,
        "human_review_required": True,
        "authoritative_decision": False,
    }
    record = {
        "id": uid(),
        "request_id": request_id,
        "actor": actor["id"],
        "role": actor["role"],
        "use_case": request.use_case,
        "run_id": request.run_id,
        "borrower_id": request.borrower_id,
        "question_hash": digest(request.question),
        "provider": selected.name,
        "provider_version": selected.version,
        "prompt_version": PROMPT_VERSION,
        "status": status,
        "tool_calls": tool_calls,
        "sources": sources,
        "response_hash": digest(result),
        "recorded_at": now(),
    }
    with db.begin() as conn:
        conn.execute(s.copilot_requests.insert().values(**record))
        audit.append(
            conn,
            actor["id"],
            "COPILOT_" + status,
            request_id,
            {"use_case": request.use_case, "tools": tool_calls, "provider": selected.name},
        )
    return result
