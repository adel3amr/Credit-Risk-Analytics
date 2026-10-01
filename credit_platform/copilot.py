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
            portfolio = evidence["portfolio"]
            stages = ", ".join(
                f"{row['name']}: {row['facilities']} facilities / ECL {row['ecl']:,.2f}"
                for row in evidence["by_stage"]
            )
            top = evidence.get("by_industry", [])[:3]
            industries = ", ".join(
                f"{row['name']} (ECL {row['ecl']:,.2f})" for row in top
            )
            return (
                f"Run {evidence['run']['run_id']} contains {portfolio['facilities']} facilities, "
                f"EAD {portfolio['ead']:,.2f}, and governed ECL {portfolio['ecl']:,.2f}. "
                f"Stage composition: {stages}. "
                f"Highest-ECL industries: {industries or 'not available'}. "
                f"Bank-use gate: {evidence['run']['bank_gate']}."
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
    version = "ollama-v2"

    def __init__(self):
        self.endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    @staticmethod
    def _focused_evidence(question: str, evidence: dict, use_case: str) -> dict:
        """Reduce prompt noise for small local models while preserving governed facts."""
        if use_case != "portfolio":
            return evidence

        q = question.lower()
        base = {
            "run": evidence.get("run"),
            "portfolio": evidence.get("portfolio"),
            "interpretation_note": evidence.get("interpretation_note"),
        }

        if any(k in q for k in ("industry", "industries", "sector", "sectors")):
            base["by_industry"] = evidence.get("by_industry", [])
            return base
        if any(k in q for k in ("product", "products", "facility type", "facilities type")):
            base["by_product"] = evidence.get("by_product", [])
            return base
        if any(k in q for k in ("stage", "staging", "stage 1", "stage 2", "stage 3")):
            base["by_stage"] = evidence.get("by_stage", [])
            base["stage_reason_counts"] = evidence.get("stage_reason_counts", {})
            return base
        if any(k in q for k in ("rating", "ratings", "risk rating")):
            base["by_risk_rating"] = evidence.get("by_risk_rating", [])
            return base
        if any(k in q for k in ("collateral", "unsecured", "guarantee", "guaranteed")):
            base["by_collateral_type"] = evidence.get("by_collateral_type", [])
            return base
        if any(k in q for k in ("watchlist", "sicr", "ews", "early warning")):
            base["by_risk_direction"] = evidence.get("by_risk_direction", [])
            base["ews_trigger_counts"] = evidence.get("ews_trigger_counts", {})
            base["risk_indicator_counts"] = evidence.get("risk_indicator_counts", {})
            return base
        if any(k in q for k in ("borrower", "borrowers", "customer", "customers")):
            base["top_borrowers_by_ecl"] = evidence.get("top_borrowers_by_ecl", [])
            base["top_borrowers_by_ead"] = evidence.get("top_borrowers_by_ead", [])
            return base
        if any(k in q for k in ("facility", "facilities")):
            base["top_facilities_by_ecl"] = evidence.get("top_facilities_by_ecl", [])
            return base
        if any(k in q for k in ("scenario", "upside", "downside", "macro")):
            base["scenario_mean_pd"] = evidence.get("scenario_mean_pd", {})
            return base
        if any(k in q for k in ("concentration", "concentrations")):
            base["concentrations"] = evidence.get("concentrations", {})
            base["by_industry"] = evidence.get("by_industry", [])
            base["by_product"] = evidence.get("by_product", [])
            return base

        # Broad portfolio-risk questions get the main aggregate dimensions, but not
        # every borrower/facility row. This keeps local inference responsive.
        base.update(
            {
                "by_stage": evidence.get("by_stage", []),
                "by_industry": evidence.get("by_industry", []),
                "by_product": evidence.get("by_product", []),
                "by_risk_rating": evidence.get("by_risk_rating", []),
                "by_risk_direction": evidence.get("by_risk_direction", []),
                "by_collateral_type": evidence.get("by_collateral_type", []),
                "risk_indicator_counts": evidence.get("risk_indicator_counts", {}),
                "risk_patterns": evidence.get("risk_patterns", []),
                "portfolio_review_actions": evidence.get("portfolio_review_actions", []),
                "ews_trigger_counts": evidence.get("ews_trigger_counts", {}),
                "stage_reason_counts": evidence.get("stage_reason_counts", {}),
                "top_borrowers_by_ecl": evidence.get("top_borrowers_by_ecl", [])[:5],
            }
        )
        return base

    @staticmethod
    def _verified_portfolio_facts(question: str, evidence: dict) -> str:
        """Return exact governed facts for common portfolio questions.

        The local LLM may explain these facts, but it must not be the source of
        numerical truth.
        """
        q = question.lower()
        p = evidence.get("portfolio", {})
        lines = []

        if any(k in q for k in ("review action", "main risk", "biggest risk", "key risk", "portfolio risk")):
            actions = evidence.get("portfolio_review_actions", [])
            if actions:
                lines.append("Governed portfolio review actions:")
                for a in actions:
                    if a["type"] == "industry_concentration":
                        lines.append(
                            f"- Review {a['industry']} concentration: mean PD {a['mean_pd']:.2%} "
                            f"versus portfolio {a['portfolio_mean_pd']:.2%}, across "
                            f"{a['borrowers']:,} borrowers and €{a['ead']:,.2f} EAD."
                        )
                    elif a["type"] == "deteriorating_high_utilization":
                        lines.append(
                            f"- Prioritize {a['borrowers']:,} deteriorating borrowers with utilization "
                            f"at or above 80%, representing €{a['ead']:,.2f} EAD."
                        )
                    elif a["type"] == "unsecured_stage_2_3":
                        lines.append(
                            f"- Review collateral/recovery strategy for {a['borrowers']:,} unsecured "
                            f"Stage 2/3 borrowers representing €{a['ead']:,.2f} EAD."
                        )
                    else:
                        lines.append(f"- {a['reason']}")

        if any(k in q for k in ("industry", "industries", "sector", "sectors")):
            rows = evidence.get("by_industry", [])
            if rows:
                lines.append("Governed industry view (sorted by ECL):")
                for r in rows[:7]:
                    lines.append(
                        f"- {r['name']}: ECL €{r['ecl']:,.2f}; EAD €{r['ead']:,.2f}; "
                        f"mean PD {r['mean_pd']:.2%}; mean LGD {r['mean_lgd']:.2%}; "
                        f"loss intensity {r['loss_intensity']:.2%}."
                    )

        if any(k in q for k in ("stage", "staging")):
            rows = evidence.get("by_stage", [])
            if rows:
                lines.append("Governed stage view:")
                for r in rows:
                    lines.append(
                        f"- {r['name']}: {r['facilities']:,} facilities, {r['borrowers']:,} borrowers, "
                        f"EAD €{r['ead']:,.2f}, ECL €{r['ecl']:,.2f}."
                    )

        if any(k in q for k in ("unsecured", "collateral", "guarantee", "guaranteed")) and p:
            lines.append(
                f"Governed security view: unsecured EAD €{p.get('unsecured_ead',0):,.2f} "
                f"({p.get('unsecured_ead_share',0):.2%} of portfolio EAD); guaranteed EAD "
                f"€{p.get('guaranteed_ead',0):,.2f} ({p.get('guaranteed_ead_share',0):.2%})."
            )

        if p and not lines:
            lines.append(
                f"Governed portfolio totals: {p.get('borrowers',0):,} borrowers, "
                f"{p.get('facilities',0):,} facilities, EAD €{p.get('ead',0):,.2f}, "
                f"ECL €{p.get('ecl',0):,.2f}, ECL/EAD {p.get('ecl_to_ead',0):.2%}."
            )

        return "\n".join(lines)

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        evidence = self._focused_evidence(question, evidence, use_case)
        verified = self._verified_portfolio_facts(question, evidence) if use_case == "portfolio" else ""
        instruction = (
            "You are a governed Credit Risk Copilot for a synthetic reference portfolio. "
            "Answer the user's descriptive or analytical credit-risk question directly using only "
            "the supplied governed evidence. Questions about industries, products, stages, ratings, "
            "concentrations, ECL, EAD, PD, LGD, watchlist, SICR, EWS, collateral, guarantees and "
            "borrower/facility rankings are permitted and should be answered when the evidence contains them. "
            "Do not invent facts, do not alter or replace governed PD/LGD/EAD/ECL/SICR/staging, "
            "do not approve overrides, do not promote models, and do not imply bank approval. "
            "You may compare, rank, summarize and calculate simple ratios from supplied values. "
            "Answer the category the user actually asked about: if they ask for industries, rank industries; "
            "if they ask for products, rank products; if they ask for borrowers, rank borrowers. "
            "Do not substitute facilities for industries or another entity type. "
            "Do not describe high ECL as necessarily meaning higher probability of default; ECL reflects "
            "exposure, probability of default and loss severity together. "
            "If the requested field is absent, say specifically which evidence is missing instead of giving "
            "a generic refusal. Distinguish evidence from interpretation and mention material limitations "
            "when relevant. Be concise and directly answer the question. Human review is required."
        )
        prompt = (
            f"{instruction}\n\nUse case: {use_case}\n"
            f"Question: {question}\n\n"
            + (f"VERIFIED GOVERNED FACTS — copy all numbers exactly; do not recompute or alter them:\n{verified}\n\n" if verified else "")
            + f"Governed evidence:\n{json.dumps(evidence, sort_keys=True)}"
        )
        body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.15,
                    "num_predict": 420,
                },
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
        answer = answer.strip()
        if verified:
            return verified + "\n\nCopilot interpretation:\n" + answer
        return answer


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

    dataset_id = run["dataset_id"]
    borrower = (
        conn.execute(
            select(s.borrowers).where(
                s.borrowers.c.dataset_id == dataset_id,
                s.borrowers.c.id == borrower_id,
            )
        )
        .mappings()
        .first()
    )
    if borrower is None:
        raise service.NotFound("Borrower source record not found")

    source = dict(borrower["payload"])
    features = dict(source.get("features", {}))

    facilities = []
    for row in rows:
        trace = row["trace"]
        facility_source = dict(trace.get("source_facility", {}))
        facilities.append(
            {
                "facility_id": row["facility_id"],
                "product": facility_source.get("product"),
                "stage": row["stage"],
                "stage_reasons": trace.get("stage_reasons", []),
                "sicr": trace.get("sicr"),
                "watchlist": trace.get("watchlist"),
                "risk_rating": trace.get("risk_rating"),
                "risk_direction": trace.get("risk_direction"),
                "ews": trace.get("ews", []),
                "pit_pd": trace.get("pit_pd"),
                "forward_pd": row["pd"],
                "scenario_pd": trace.get("scenario_pd", {}),
                "lifetime_pd": trace.get("lifetime_pd"),
                "effective_pd": trace.get("effective_pd"),
                "lgd": row["lgd"],
                "ead": row["ead"],
                "ecl": row["ecl"],
                "remaining_months": trace.get("remaining_months"),
                "collateral_type": facility_source.get("collateral_type"),
                "collateral_coverage": facility_source.get("collateral_coverage"),
                "guarantee_coverage": facility_source.get("guarantee_coverage"),
                "lien_rank": facility_source.get("lien_rank"),
                "drawn": facility_source.get("drawn"),
                "limit": facility_source.get("limit"),
                "face": facility_source.get("face"),
            }
        )

    stages = sorted({f["stage"] for f in facilities})
    total_ead = sum(float(f["ead"] or 0) for f in facilities)
    total_ecl = sum(float(f["ecl"] or 0) for f in facilities)

    evidence = {
        "run_id": run_id,
        "borrower_id": borrower_id,
        "industry": borrower["industry"],
        "stages": stages,
        "total_ead": total_ead,
        "total_ecl": total_ecl,
        "source_profile": {
            "collateral_type": source.get("collateral_type"),
            "observed_at": source.get("observed_at"),
            "features": features,
        },
        "facilities": facilities,
        "bank_gate": "BLOCKED",
    }
    return evidence, [
        {"type": "decision_trace", "run_id": run_id, "borrower_id": borrower_id},
        {"type": "borrower_source", "dataset_id": dataset_id, "borrower_id": borrower_id},
    ]


def _portfolio(conn, run_id: str) -> tuple[dict, list[dict]]:
    base = service.portfolio(conn, run_id)
    run = service.one(conn, s.runs, run_id)
    dataset = service.one(conn, s.datasets, run["dataset_id"])
    traces = service.traces(conn, run_id)

    def bucket(key_fn):
        out = {}
        for t in traces:
            key = str(key_fn(t))
            row = out.setdefault(
                key,
                {"facilities": 0, "borrowers": set(), "ead": 0.0, "ecl": 0.0, "pd_sum": 0.0, "lgd_sum": 0.0},
            )
            row["facilities"] += 1
            row["borrowers"].add(t["borrower_id"])
            row["ead"] += float(t["ead"])
            row["ecl"] += float(t["ecl"])
            row["pd_sum"] += float(t["pd"])
            row["lgd_sum"] += float(t["lgd"])
        result = []
        for key, row in out.items():
            n = row["facilities"]
            result.append(
                {
                    "name": key,
                    "facilities": n,
                    "borrowers": len(row["borrowers"]),
                    "ead": row["ead"],
                    "ecl": row["ecl"],
                    "mean_pd": row["pd_sum"] / n if n else 0.0,
                    "mean_lgd": row["lgd_sum"] / n if n else 0.0,
                }
            )
        return result

    total_ead = float(base["ead"] or 0.0)
    total_ecl = float(base["ecl"] or 0.0)

    def enrich(rows):
        for row in rows:
            row["ead_share"] = row["ead"] / total_ead if total_ead else 0.0
            row["ecl_share"] = row["ecl"] / total_ecl if total_ecl else 0.0
            row["loss_intensity"] = row["ecl"] / row["ead"] if row["ead"] else 0.0
        return rows

    by_stage = enrich(bucket(lambda t: t["stage"]))
    by_industry = enrich(bucket(lambda t: t["source_borrower"]["industry"]))
    by_product = enrich(bucket(lambda t: t["source_facility"]["product"]))
    by_rating = enrich(bucket(lambda t: t.get("risk_rating")))
    by_direction = enrich(bucket(lambda t: t.get("risk_direction")))
    by_collateral = enrich(bucket(lambda t: t["source_facility"].get("collateral_type")))

    borrower_rollup = {}
    for t in traces:
        bid = t["borrower_id"]
        row = borrower_rollup.setdefault(
            bid,
            {
                "borrower_id": bid,
                "industry": t["source_borrower"]["industry"],
                "stage": t["stage"],
                "risk_rating": t.get("risk_rating"),
                "risk_direction": t.get("risk_direction"),
                "watchlist": bool(t.get("watchlist")),
                "sicr": bool(t.get("sicr")),
                "facilities": 0,
                "ead": 0.0,
                "ecl": 0.0,
                "max_pd": 0.0,
                "max_lgd": 0.0,
            },
        )
        row["facilities"] += 1
        row["ead"] += float(t["ead"])
        row["ecl"] += float(t["ecl"])
        row["max_pd"] = max(row["max_pd"], float(t["pd"]))
        row["max_lgd"] = max(row["max_lgd"], float(t["lgd"]))
        if t["stage"] == "Stage 3" or (t["stage"] == "Stage 2" and row["stage"] == "Stage 1"):
            row["stage"] = t["stage"]

    top_borrowers_ecl = sorted(borrower_rollup.values(), key=lambda x: x["ecl"], reverse=True)[:15]
    top_borrowers_ead = sorted(borrower_rollup.values(), key=lambda x: x["ead"], reverse=True)[:15]
    top_facilities_ecl = sorted(
        [
            {
                "facility_id": t["facility_id"],
                "borrower_id": t["borrower_id"],
                "industry": t["source_borrower"]["industry"],
                "product": t["source_facility"]["product"],
                "stage": t["stage"],
                "risk_rating": t.get("risk_rating"),
                "risk_direction": t.get("risk_direction"),
                "pd": float(t["pd"]),
                "lgd": float(t["lgd"]),
                "ead": float(t["ead"]),
                "ecl": float(t["ecl"]),
                "collateral_type": t["source_facility"].get("collateral_type"),
                "guarantee_coverage": t["source_facility"].get("guarantee_coverage"),
            }
            for t in traces
        ],
        key=lambda x: x["ecl"],
        reverse=True,
    )[:15]

    stage_counts = {r["name"]: r["facilities"] for r in by_stage}
    watchlist_count = len({t["borrower_id"] for t in traces if t.get("watchlist")})
    sicr_count = len({t["borrower_id"] for t in traces if t.get("sicr")})
    deteriorating_count = len({t["borrower_id"] for t in traces if t.get("risk_direction") == "Deteriorating"})
    unsecured_ead = sum(
        float(t["ead"])
        for t in traces
        if t["source_facility"].get("collateral_type") == "Unsecured"
    )
    guaranteed_ead = sum(
        float(t["ead"])
        for t in traces
        if float(t["source_facility"].get("guarantee_coverage") or 0) > 0
    )

    ews_counts = {}
    stage_reason_counts = {}
    for t in traces:
        for signal in t.get("ews", []):
            if signal.get("triggered"):
                ews_counts[signal.get("id", "unknown")] = ews_counts.get(signal.get("id", "unknown"), 0) + 1
        for reason in t.get("stage_reasons", []):
            stage_reason_counts[reason] = stage_reason_counts.get(reason, 0) + 1

    borrower_features = {}
    for t in traces:
        bid = t["borrower_id"]
        if bid not in borrower_features:
            borrower_features[bid] = dict(t["source_borrower"].get("features", {}))

    def borrower_count(predicate):
        return sum(1 for features in borrower_features.values() if predicate(features))

    risk_indicators = {
        "high_utilization_ge_80pct_borrowers": borrower_count(
            lambda f: float(f.get("credit_utilization", 0)) >= 0.80
        ),
        "days_past_due_gt_0_borrowers": borrower_count(
            lambda f: float(f.get("days_past_due", 0)) > 0
        ),
        "days_past_due_ge_30_borrowers": borrower_count(
            lambda f: float(f.get("days_past_due", 0)) >= 30
        ),
        "days_past_due_ge_90_borrowers": borrower_count(
            lambda f: float(f.get("days_past_due", 0)) >= 90
        ),
        "recent_delinquency_borrowers": borrower_count(
            lambda f: float(f.get("delinquencies_12m", 0)) > 0
        ),
        "previous_default_borrowers": borrower_count(
            lambda f: float(f.get("previous_defaults", 0)) > 0
        ),
        "current_credit_impaired_borrowers": borrower_count(
            lambda f: float(f.get("current_credit_impaired", 0)) == 1
        ),
        "limit_breach_borrowers": borrower_count(
            lambda f: float(f.get("limit_breach_count", 0)) > 0
        ),
        "persistent_high_utilization_borrowers": borrower_count(
            lambda f: float(f.get("months_above_80_utilization", 0)) > 0
        ),
        "high_leverage_ge_3x_borrowers": borrower_count(
            lambda f: float(f.get("leverage_ratio", 0)) >= 3.0
        ),
    }

    scenarios = {}
    for t in traces:
        for name, value in t.get("scenario_pd", {}).items():
            row = scenarios.setdefault(name, {"count": 0, "pd_sum": 0.0})
            row["count"] += 1
            row["pd_sum"] += float(value)
    scenario_pd = {
        name: row["pd_sum"] / row["count"] if row["count"] else 0.0
        for name, row in scenarios.items()
    }

    # Reproduce the original Portfolio Cockpit's transparent review logic
    # as governed evidence for the Copilot rather than asking the LLM to invent it.
    borrower_level = list(borrower_rollup.values())
    borrower_count_total = max(len(borrower_level), 1)

    portfolio_pd = (
        sum(float(t["pd"]) for t in traces) / len(traces) if traces else 0.0
    )
    portfolio_loss = total_ecl / total_ead if total_ead else 0.0
    min_group = max(30, int(borrower_count_total * 0.01))

    risk_patterns = []
    borrower_trace = {}
    for t in traces:
        borrower_trace.setdefault(t["borrower_id"], t)

    def borrower_subset(predicate):
        ids = []
        for bid, t in borrower_trace.items():
            features = t["source_borrower"].get("features", {})
            if predicate(t, features):
                ids.append(bid)
        return ids

    checks = [
        ("High utilization", borrower_subset(lambda t, f: float(f.get("credit_utilization", 0)) >= 0.80)),
        ("Recent delinquency", borrower_subset(lambda t, f: float(f.get("delinquencies_12m", 0)) > 0)),
        ("Previous default", borrower_subset(lambda t, f: float(f.get("previous_defaults", 0)) > 0)),
        ("Deteriorating EWS", borrower_subset(lambda t, f: t.get("risk_direction") == "Deteriorating")),
        ("Unsecured", borrower_subset(lambda t, f: t["source_facility"].get("collateral_type") == "Unsecured")),
        (
            "High utilization + deterioration",
            borrower_subset(
                lambda t, f: float(f.get("credit_utilization", 0)) >= 0.80
                and t.get("risk_direction") == "Deteriorating"
            ),
        ),
    ]

    for label, ids in checks:
        if len(ids) < min_group:
            continue
        idset = set(ids)
        subset = [t for t in traces if t["borrower_id"] in idset]
        ead_sum = sum(float(t["ead"]) for t in subset)
        ecl_sum = sum(float(t["ecl"]) for t in subset)
        pd_values = [float(t["pd"]) for t in subset]
        mean_pd = sum(pd_values) / len(pd_values) if pd_values else 0.0
        loss_intensity = ecl_sum / ead_sum if ead_sum else 0.0
        risk_patterns.append(
            {
                "pattern": label,
                "borrowers": len(idset),
                "ead": ead_sum,
                "mean_pd": mean_pd,
                "pd_vs_portfolio": mean_pd / portfolio_pd if portfolio_pd else 0.0,
                "ecl_to_ead": loss_intensity,
                "loss_vs_portfolio": loss_intensity / portfolio_loss if portfolio_loss else 0.0,
            }
        )

    risk_patterns.sort(key=lambda x: x["loss_vs_portfolio"], reverse=True)

    portfolio_review_actions = []

    # Industry concentration rule from the original Portfolio Cockpit:
    # mean PD >= 1.25x portfolio mean and sufficient group size.
    for row in by_industry:
        if row["borrowers"] >= min_group and row["mean_pd"] >= portfolio_pd * 1.25:
            portfolio_review_actions.append(
                {
                    "type": "industry_concentration",
                    "industry": row["name"],
                    "borrowers": row["borrowers"],
                    "ead": row["ead"],
                    "mean_pd": row["mean_pd"],
                    "portfolio_mean_pd": portfolio_pd,
                    "reason": "Mean PD is at least 1.25x the portfolio mean with sufficient population.",
                }
            )

    det_ids = borrower_subset(
        lambda t, f: t.get("risk_direction") == "Deteriorating"
        and float(f.get("credit_utilization", 0)) >= 0.80
    )
    if len(det_ids) >= min_group:
        idset = set(det_ids)
        ead_sum = sum(float(t["ead"]) for t in traces if t["borrower_id"] in idset)
        portfolio_review_actions.append(
            {
                "type": "deteriorating_high_utilization",
                "borrowers": len(idset),
                "ead": ead_sum,
                "reason": "Deteriorating borrowers with utilization at or above 80%.",
            }
        )

    s2u_ids = borrower_subset(
        lambda t, f: t["stage"] in ("Stage 2", "Stage 3")
        and t["source_facility"].get("collateral_type") == "Unsecured"
    )
    if s2u_ids:
        idset = set(s2u_ids)
        ead_sum = sum(float(t["ead"]) for t in traces if t["borrower_id"] in idset)
        portfolio_review_actions.append(
            {
                "type": "unsecured_stage_2_3",
                "borrowers": len(idset),
                "ead": ead_sum,
                "reason": "Unsecured Stage 2/3 borrowers require collateral/recovery review.",
            }
        )

    if not portfolio_review_actions:
        portfolio_review_actions.append(
            {
                "type": "routine_monitoring",
                "reason": "No broad portfolio trigger exceeds the current review thresholds.",
            }
        )

    evidence = {
        "run": {
            "run_id": run_id,
            "purpose": run["purpose"],
            "status": run["status"],
            "effective_date": dataset["effective_date"],
            "dataset_name": dataset["name"],
            "dataset_status": dataset["status"],
            "dataset_dq": dataset["dq"],
            "bank_gate": base["bank_gate"],
        },
        "portfolio": {
            "borrowers": len(borrower_rollup),
            "facilities": base["facility_count"],
            "ead": total_ead,
            "ecl": total_ecl,
            "ecl_to_ead": total_ecl / total_ead if total_ead else 0.0,
            "reference_ecl": float(base.get("reference_ecl", total_ecl)),
            "controlled_reference_ecl": float(base.get("controlled_reference_ecl", total_ecl)),
            "override_adjustment": float(base.get("override_adjustment", 0.0)),
            "approved_override_count": len(base.get("approved_overrides", [])),
            "watchlist_borrowers": watchlist_count,
            "sicr_borrowers": sicr_count,
            "deteriorating_borrowers": deteriorating_count,
            "unsecured_ead": unsecured_ead,
            "unsecured_ead_share": unsecured_ead / total_ead if total_ead else 0.0,
            "guaranteed_ead": guaranteed_ead,
            "guaranteed_ead_share": guaranteed_ead / total_ead if total_ead else 0.0,
            "stage_counts": stage_counts,
        },
        "by_stage": sorted(by_stage, key=lambda x: x["ecl"], reverse=True),
        "by_industry": sorted(by_industry, key=lambda x: x["ecl"], reverse=True),
        "by_product": sorted(by_product, key=lambda x: x["ecl"], reverse=True),
        "by_risk_rating": sorted(by_rating, key=lambda x: (x["name"] == "None", x["name"])),
        "by_risk_direction": sorted(by_direction, key=lambda x: x["ecl"], reverse=True),
        "by_collateral_type": sorted(by_collateral, key=lambda x: x["ecl"], reverse=True),
        "scenario_mean_pd": scenario_pd,
        "ews_trigger_counts": ews_counts,
        "stage_reason_counts": stage_reason_counts,
        "risk_indicator_counts": risk_indicators,
        "risk_patterns": risk_patterns,
        "portfolio_review_actions": portfolio_review_actions,
        "top_borrowers_by_ecl": top_borrowers_ecl,
        "top_borrowers_by_ead": top_borrowers_ead,
        "top_facilities_by_ecl": top_facilities_ecl,
        "concentrations": base.get("concentrations", {}),
        "interpretation_note": (
            "All values are governed outputs from the selected successful synthetic reference run. "
            "Rankings are descriptive portfolio analytics, not credit decisions."
        ),
    }

    return evidence, [
        {"type": "portfolio_run", "run_id": run_id},
        {"type": "portfolio_aggregations", "run_id": run_id},
        {"type": "governed_decision_traces", "run_id": run_id},
    ]


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
