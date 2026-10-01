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

PROMPT_VERSION = "credit-risk-copilot-4"
PROVIDER_VERSION = "deterministic-4"
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
        if "economic_lgd" in evidence:
            result = evidence["economic_lgd"]
            rows = result["metrics"]
            old = next(r for r in rows if r["cohort"]=="current" and r["model"]=="incumbent" and r["group"]=="all" and r.get('scenario','baseline')=='baseline')
            new = next(r for r in rows if r["cohort"]=="current" and r["model"]=="corrected" and r["group"]=="all" and r.get('scenario','baseline')=='baseline')
            return (
                f"{result['model_version']} synthetic evidence: same-population current conditional LGD bias "
                f"{old['bias_pp']:+.2f} pp → {new['bias_pp']:+.2f} pp. "
                "Output growth, unemployment, collateral-price change and liquidity now link "
                "reporting-date economics to recoveries and scenario LGD. Hidden state is excluded. "
                "The historical S1 -12.65 pp result is a different population/DGP. "
                f"Decision: {result['status']}. Remaining findings: "
                + "; ".join(result["remaining_deficiencies"])
                + (". Latest hardening stopped before a new final holdout; R1 remains the retained candidate."
                   if 'hardening' in result else '')
                + ". No MoC or booked adjustment. Bank use remains BLOCKED."
            )
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
            "The LGD production gate remains BLOCKED. Historical S1 current conditional bias is "
            f"{finding['current_conditional_bias_pp']:.2f} pp. True-state research calibration "
            f"reduced it to {finding['oracle_bias_pp']:+.2f} pp, but that state is unavailable "
            "at prediction time and operational proxies failed. The challenger was therefore "
            "not promoted; the explicit downturn overlay is restricted to sensitivity use."
        )


class OpenAIResponsesProvider:
    """Optional OpenAI Responses API provider. Governed evidence remains the only context."""

    name = "openai-responses"
    version = "responses-v1"

    def __init__(self):
        self.key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_COPILOT_MODEL", "gpt-5.6-luna")
        if not self.key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI Copilot provider")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        instruction = (
            "You are a governed Credit Risk Copilot. Use only the supplied evidence. "
            "Do not invent facts, recalculate or replace PD/LGD/EAD/ECL/SICR/staging, "
            "approve overrides, promote models, or imply bank approval. "
            "Clearly distinguish observed evidence, validation findings and limitations. "
            "If the evidence is insufficient, say so. Keep the answer concise and useful "
            "for a credit-risk professional. Human review is required."
        )
        body = json.dumps(
            {
                "model": self.model,
                "instructions": instruction,
                "input": (
                    f"Use case: {use_case}\\nQuestion: {question}\\n"
                    f"Governed evidence:\\n{json.dumps(evidence, sort_keys=True)}"
                ),
                "max_output_tokens": 700,
                "store": False,
            }
        ).encode()
        req = Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=30) as response:  # nosec: fixed HTTPS OpenAI endpoint
            result = json.loads(response.read(2_000_000))
        parts = [
            part.get("text", "")
            for item in result.get("output", [])
            if item.get("type") == "message"
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        ]
        answer = "\\n".join(p.strip() for p in parts if p and p.strip()).strip()
        if not answer:
            raise ValueError("OpenAI Responses API returned no text answer")
        return answer


class OllamaProvider:
    """Local conversational provider using Ollama. Governed evidence stays on the machine."""

    name = "ollama-local"
    version = "ollama-v1"

    def __init__(self):
        self.endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        instruction = (
            "You are a governed Credit Risk Copilot. Answer the user's question using only "
            "the supplied governed evidence. Do not invent facts, do not recalculate or replace "
            "PD/LGD/EAD/ECL/SICR/staging, do not approve overrides, do not promote models, and "
            "do not imply bank approval. Distinguish evidence from interpretation and mention "
            "material limitations when relevant. Be concise but directly answer the question. "
            "Human review is required."
        )
        prompt = (
            f"{instruction}\n\nUse case: {use_case}\n"
            f"Question: {question}\n\nGoverned evidence:\n"
            f"{json.dumps(evidence, sort_keys=True)}"
        )
        body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
        ).encode()
        req = Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=120) as response:  # nosec: local configurable endpoint
            result = json.loads(response.read(2_000_000))
        answer = result.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Ollama returned no answer")
        return answer.strip()


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
    configured = os.getenv("COPILOT_PROVIDER", "auto").lower()
    if configured == "auto":
        if os.getenv("OPENAI_API_KEY"):
            return OpenAIResponsesProvider()
        if os.getenv("OLLAMA_MODEL"):
            return OllamaProvider()
        return DeterministicProvider()
    if configured == "deterministic":
        return DeterministicProvider()
    if configured == "ollama":
        return OllamaProvider()
    if configured == "openai":
        return OpenAIResponsesProvider()
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
                    if re.search(r"\b(s2|economic|observable|successor)\b", request.question, re.IGNORECASE):
                        from .economic_evidence import get
                        result, source = get()
                        evidence, sources = {"economic_lgd": result}, [source]
                        tool_calls = ["get_economic_lgd_validation"]
                    else:
                        evidence, sources = _model_risk()
                        tool_calls = ["get_authoritative_model_risk_finding"]
                        # Keep historical facts for lineage, but answer from the
                        # latest completed validation instead of stale S1 alone.
                        from .economic_evidence import get
                        result, source = get()
                        evidence['economic_lgd']=result
                        sources.append(source)
                        tool_calls.append('get_economic_lgd_validation')
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
