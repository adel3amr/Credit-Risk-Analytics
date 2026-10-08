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

PROMPT_VERSION = "credit-risk-copilot-8"
PROVIDER_VERSION = "deterministic-8"
REFUSAL = "I do not have sufficient permitted evidence to answer this."
INJECTION = re.compile(
    r"(ignore\s+(all|previous|prior|the\s+validation)|system\s+prompt|developer\s+message|"
    r"reveal\s+(secrets?|tokens?|credentials?)|drop\s+table|unrestricted\s+sql|execute\s+(this\s+)?sql|book\s+(it|lgd|ecl)|bank[- ]approved|another\s+user)",
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
        if "workout_lgd" in evidence:
            w = evidence["workout_lgd"]
            return (f"WN-1 dated workout experiment: {w['decision']['status']}. "
                    f"Calibration failures: {', '.join(w['decision']['calibration_failures'])}. "
                    "Resolved-workout selection and unvalidated institutional feature capture remain limitations. "
                    "The component challenger is not the active scorer. Institutional production remains BLOCKED.")
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
                f"Run {evidence['run_id']} contains {evidence['borrower_count']} scored borrowers and {evidence['facility_count']} facilities, "
                f"EAD {evidence['ead']:,.2f}, and governed ECL {evidence['ecl']:,.2f}. "
                f"Stage composition: {stages}. Bank-use gate: {evidence['bank_gate']}. "
                + self.portfolio_detail(question, evidence)
            )
        finding = evidence["lgd_finding"]
        return (
            "The LGD production gate remains BLOCKED. Historical S1 current conditional bias is "
            f"{finding['current_conditional_bias_pp']:.2f} pp. True-state research calibration "
            f"reduced it to {finding['oracle_bias_pp']:+.2f} pp, but that state is unavailable "
            "at prediction time and operational proxies failed. The challenger was therefore "
            "not promoted; the explicit downturn overlay is restricted to sensitivity use."
        )


    def portfolio_detail(self, question, evidence):
        q = question.lower()
        if any(word in q for word in ("increase", "deteriorated most", "change since")):
            return "A single run cannot establish a change over time. Use the governed two-run movement endpoint; no causal explanation is inferred."

        by_industry = evidence.get("by_industry", {})
        broad = any(
            phrase in q
            for phrase in (
                "summarize", "summary", "risk profile", "main risk",
                "important areas", "human review", "portfolio risk",
            )
        )
        if broad and by_industry:
            ranked_ecl = sorted(
                by_industry.items(),
                key=lambda kv: (-float(kv[1].get("ecl", 0.0)), kv[0]),
            )
            highest_pd = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("mean_pd", 0.0)), kv[0]),
            )
            highest_loss = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("loss_intensity", 0.0)), kv[0]),
            )
            top_industries = "; ".join(
                f"{name}: EAD {row['ead']:,.2f}, ECL {row['ecl']:,.2f}, "
                f"mean PD {row.get('mean_pd', 0.0):.2%}, "
                f"ECL/EAD {row.get('loss_intensity', 0.0):.2%}"
                for name, row in ranked_ecl[:3]
            )
            watch = evidence.get("watchlist", {})
            unsecured = evidence.get("unsecured", {})
            guaranteed = evidence.get("guaranteed", {})
            actions = []
            for action in evidence.get("portfolio_review_actions", []):
                typ = action.get("type")
                if typ == "industry_concentration":
                    actions.append(
                        f"review {action['industry']} concentration "
                        f"(mean PD {action['mean_pd']:.2%} vs portfolio "
                        f"{action['portfolio_mean_pd']:.2%}; EAD {action['ead']:,.2f})"
                    )
                elif typ == "deteriorating_high_utilization":
                    actions.append(
                        f"prioritize {action['borrowers']} deteriorating high-utilization "
                        f"borrowers representing EAD {action['ead']:,.2f}"
                    )
                elif typ == "unsecured_stage_2_3":
                    actions.append(
                        f"review collateral/recovery strategy for {action['borrowers']} "
                        f"unsecured Stage 2/3 borrowers, EAD {action['ead']:,.2f}"
                    )
                elif action.get("reason"):
                    actions.append(action["reason"])
            action_text = "; ".join(actions[:5]) if actions else evidence.get("review_basis", "")
            return (
                f"Portfolio review: leading industries by ECL are {top_industries}. "
                f"Highest mean-PD industry is {highest_pd[0]} "
                f"({highest_pd[1].get('mean_pd', 0.0):.2%}); highest loss intensity is "
                f"{highest_loss[0]} ({highest_loss[1].get('loss_intensity', 0.0):.2%}). "
                f"Watchlist: {watch.get('borrowers', 0)} borrowers / EAD {watch.get('ead', 0.0):,.2f}. "
                f"Unsecured: {unsecured.get('borrowers', 0)} borrowers / EAD {unsecured.get('ead', 0.0):,.2f}. "
                f"Guaranteed: {guaranteed.get('borrowers', 0)} borrowers / EAD {guaranteed.get('ead', 0.0):,.2f}. "
                f"Human-review priorities: {action_text}"
            )

        if "industr" in q or "sector" in q:
            ranked = sorted(by_industry.items(), key=lambda kv:(-kv[1]["ecl"],kv[0]))
            return "Industries ranked by reference ECL (not a deterioration forecast): " + "; ".join(
                f"{k}: EAD {v['ead']:,.2f}, ECL {v['ecl']:,.2f}, "
                f"mean PD {v.get('mean_pd', 0.0):.2%}, "
                f"ECL/EAD {v.get('loss_intensity', 0.0):.2%}"
                for k, v in ranked
            )
        for key in ("watchlist", "unsecured", "guaranteed"):
            if key in q or (key=="guaranteed" and "guarantee" in q):
                v=evidence[key]
                return f"{key}: {v['borrowers']} distinct borrowers, {v['facilities']} facilities, EAD {v['ead']:,.2f}, ECL {v['ecl']:,.2f}."
        if "top" in q or "attention" in q:
            return evidence["review_basis"] + " " + "; ".join(
                f"{r['facility_id']}: ECL {r['ecl']:,.2f}"
                for r in evidence["top_risk_cases"]
            )
        return evidence["count_basis"]


def _verified_grounding(question: str, evidence: dict, use_case: str) -> str:
    """Deterministic evidence statement that remains the numerical source of truth."""
    return DeterministicProvider().render(question, evidence, use_case)


class OpenAIResponsesProvider:
    """Optional OpenAI narrative provider over governed evidence only."""

    name = "openai-responses"
    version = "responses-v2-grounded"

    def __init__(self):
        self.key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_COPILOT_MODEL", "gpt-5.6-luna")
        if not self.key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI Copilot provider")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        verified = _verified_grounding(question, evidence, use_case)
        instruction = (
            "You are a governed Credit Risk Copilot. Use only supplied governed evidence. "
            "The VERIFIED FACTS block is authoritative. Do not contradict it, invent facts, "
            "recalculate or replace PD/LGD/EAD/ECL/SICR/staging, approve overrides, promote "
            "models, or imply bank approval. Add concise professional interpretation only. "
            "If evidence is insufficient, state that. Human review is required."
        )
        body = json.dumps(
            {
                "model": self.model,
                "instructions": instruction,
                "input": (
                    f"Use case: {use_case}\nQuestion: {question}\n\n"
                    f"VERIFIED FACTS:\n{verified}\n\n"
                    f"Governed evidence:\n{json.dumps(evidence, sort_keys=True)}"
                ),
                "max_output_tokens": 500,
                "store": False,
            }
        ).encode()
        req = Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
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
        answer = "\n".join(p.strip() for p in parts if p and p.strip()).strip()
        if not answer:
            raise ValueError("OpenAI Responses API returned no text answer")
        return verified + "\n\nCopilot interpretation:\n" + answer


class OllamaProvider:
    """Optional local conversational provider; deterministic facts remain authoritative."""

    name = "ollama-local"
    version = "ollama-v3-grounded"

    def __init__(self):
        self.endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        verified = _verified_grounding(question, evidence, use_case)
        prompt = (
            "You are a governed Credit Risk Copilot for a synthetic reference portfolio. "
            "Use only the supplied evidence. VERIFIED FACTS are authoritative: do not alter "
            "their numbers or claims. Do not approve credit decisions, overrides, model "
            "promotion or imply institutional approval. Add concise interpretation only. "
            "Human review is required.\n\n"
            f"Use case: {use_case}\nQuestion: {question}\n\n"
            f"VERIFIED FACTS:\n{verified}\n\n"
            f"Governed evidence:\n{json.dumps(evidence, sort_keys=True)}"
        )
        body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {"temperature": 0.15, "num_predict": 420},
            }
        ).encode()
        req = Request(self.endpoint, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:  # nosec: explicit local/configured endpoint
            result = json.loads(response.read(2_000_000))
        answer = result.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Ollama returned no answer")
        return verified + "\n\nCopilot interpretation:\n" + answer.strip()


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
        # Arbitrary provider prose cannot establish numerical or causal grounding.
        # Only exact deterministic evidence rendering is eligible for release.
        grounded = DeterministicProvider().render(question, evidence, use_case)
        return answer.strip() if answer.strip() == grounded else grounded


def provider() -> Provider:
    configured = os.getenv("COPILOT_PROVIDER", "deterministic").lower()
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
        row for row in service.decision_rows(conn, run_id)
        if row["borrower_id"] == borrower_id
    ]
    if not rows:
        raise service.NotFound("Borrower decision not found in run")

    facilities = []
    source_borrower = None
    for row in rows:
        trace = row["trace"]
        source_borrower = source_borrower or trace.get("source_borrower", {})
        source_facility = trace.get("source_facility", {})
        facilities.append(
            {
                "facility_id": row["facility_id"],
                "product": source_facility.get("product"),
                "stage": row["stage"],
                "pd": row["pd"],
                "pit_pd": trace.get("pit_pd"),
                "scenario_pd": trace.get("scenario_pd", {}),
                "lifetime_pd": trace.get("lifetime_pd"),
                "effective_pd": trace.get("effective_pd"),
                "risk_rating": trace.get("risk_rating"),
                "risk_direction": trace.get("risk_direction"),
                "lgd": row["lgd"],
                "ead": row["ead"],
                "ecl": row["ecl"],
                "stage_reasons": trace.get("stage_reasons", []),
                "watchlist": trace.get("watchlist"),
                "sicr": trace.get("sicr"),
                "ews": trace.get("ews", []),
                "remaining_months": trace.get("remaining_months"),
                "collateral_type": source_facility.get("collateral_type"),
                "collateral_coverage": trace.get("lgd_features", {}).get("collateral_coverage"),
                "guarantee_coverage": trace.get("lgd_features", {}).get("guarantee_coverage"),
                "lien_rank": source_facility.get("lien_rank"),
                "drawn": source_facility.get("drawn"),
                "limit": source_facility.get("limit"),
                "face": source_facility.get("face"),
            }
        )
    evidence = {
        "run_id": run_id,
        "borrower_id": borrower_id,
        "industry": (source_borrower or {}).get("industry"),
        "source_profile": {
            "observed_at": (source_borrower or {}).get("observed_at"),
            "features": (source_borrower or {}).get("features", {}),
        },
        "facilities": facilities,
        "bank_gate": "BLOCKED",
    }
    return evidence, [
        {"type": "decision_trace", "run_id": run_id, "borrower_id": borrower_id}
    ]

def _portfolio(conn, run_id: str) -> tuple[dict, list[dict]]:
    base = service.portfolio(conn, run_id)
    return base, [{"type": "portfolio_run", "run_id": run_id}]


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
                    if re.search(r"\b(wn-1|workout|vnext)\b", request.question, re.IGNORECASE):
                        from .workout_evidence import get
                        result, source = get()
                        evidence, sources = {"workout_lgd": result}, [source]
                        tool_calls = ["get_workout_lgd_validation"]
                    elif re.search(r"\b(s2|economic|observable|successor)\b", request.question, re.IGNORECASE):
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
                        from .workout_evidence import get as workout_get
                        result, source = workout_get()
                        evidence['workout_lgd'] = result
                        sources.append(source)
                        tool_calls.append('get_workout_lgd_validation')
            try:
                response = selected.render(request.question, evidence, request.use_case)
            except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
                # Conversational providers are optional. A provider outage must never
                # remove the deterministic governed explanation.
                selected = DeterministicProvider()
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
        # Missing identifiers must not make refusal evidence violate its FK.
        if record["run_id"] and conn.execute(
            select(s.runs.c.id).where(s.runs.c.id == record["run_id"])
        ).first() is None:
            record["run_id"] = None
        conn.execute(s.copilot_requests.insert().values(**record))
        audit.append(
            conn,
            actor["id"],
            "COPILOT_" + status,
            request_id,
            {"use_case": request.use_case, "tools": tool_calls, "provider": selected.name},
        )
    return result
