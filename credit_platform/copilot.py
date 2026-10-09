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

PROMPT_VERSION = "credit-risk-copilot-11"
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
            return self.borrower_detail(question, evidence, use_case)
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


    def borrower_detail(self, question, evidence, use_case):
        q = question.lower()
        facilities = evidence["facilities"]
        features = evidence.get("source_profile", {}).get("features", {})
        stages = sorted({row["stage"] for row in facilities})
        reasons = sorted(
            {reason for row in facilities for reason in row.get("stage_reasons", [])}
        )
        total_ead = sum(float(row["ead"]) for row in facilities)
        total_ecl = sum(float(row["ecl"]) for row in facilities)
        max_pd = max((float(row["pd"]) for row in facilities), default=0.0)
        max_lgd = max((float(row["lgd"]) for row in facilities), default=0.0)
        ratings = sorted({str(row.get("risk_rating")) for row in facilities if row.get("risk_rating") is not None})
        directions = sorted({str(row.get("risk_direction")) for row in facilities if row.get("risk_direction")})
        watchlist = any(bool(row.get("watchlist")) for row in facilities)
        sicr = any(bool(row.get("sicr")) for row in facilities)

        adverse = []
        utilization = float(features.get("credit_utilization", 0.0))
        delinq = int(features.get("delinquencies_12m", 0) or 0)
        dpd = int(features.get("days_past_due", 0) or 0)
        leverage = float(features.get("leverage_ratio", 0.0))
        previous_defaults = int(features.get("previous_defaults", 0) or 0)
        limit_breaches = int(features.get("limit_breach_count", 0) or 0)
        months_high_util = int(features.get("months_above_80_utilization", 0) or 0)

        if utilization >= 0.80:
            adverse.append(f"high utilization {utilization:.1%}")
        if delinq > 0:
            adverse.append(f"{delinq} delinquency event(s) in the last 12 months")
        if dpd > 0:
            adverse.append(f"{dpd} days past due")
        if leverage >= 3.0:
            adverse.append(f"leverage {leverage:.1f}x")
        if previous_defaults > 0:
            adverse.append(f"{previous_defaults} previous default(s)")
        if limit_breaches > 0:
            adverse.append(f"{limit_breaches} limit breach(es)")
        if months_high_util > 0:
            adverse.append(f"{months_high_util} month(s) above 80% utilization")

        ews_triggered = sorted({
            str(signal.get("id"))
            for row in facilities
            for signal in row.get("ews", [])
            if signal.get("triggered") and signal.get("id")
        })

        adverse_question = any(
            token in q
            for token in (
                "adverse", "indicator", "driver", "risk factor", "warning",
                "utilization", "delinquen", "past due", "dpd", "leverage",
            )
        )
        if adverse_question:
            if adverse:
                detail = "; ".join(adverse)
                ews_text = (
                    f" Triggered EWS signal(s): {', '.join(ews_triggered)}."
                    if ews_triggered else ""
                )
                return (
                    f"Borrower {evidence['borrower_id']} key adverse indicators: {detail}."
                    f"{ews_text} Current risk direction: "
                    f"{', '.join(directions) if directions else 'not recorded'}; "
                    f"Watchlist={'yes' if watchlist else 'no'}; SICR={'yes' if sicr else 'no'}. "
                    f"Governed max facility PD {max_pd:.2%}, max LGD {max_lgd:.2%}, "
                    f"total EAD {total_ead:,.2f}, total ECL {total_ecl:,.2f}. "
                    f"Current stage(s): {', '.join(stages)}. "
                    f"Stage reason(s): {', '.join(reasons) if reasons else 'none recorded'}."
                )
            return (
                f"Borrower {evidence['borrower_id']} has no adverse indicator crossing the "
                "workbench thresholds for utilization, delinquency, DPD, leverage, previous "
                "defaults or limit breaches. "
                f"Current stage(s): {', '.join(stages)}; total EAD {total_ead:,.2f}; "
                f"total ECL {total_ecl:,.2f}."
            )

        prefix = "DRAFT — human review required. " if use_case == "credit_review" else ""
        adverse_text = "; ".join(adverse) if adverse else "no workbench adverse threshold is triggered"
        return (
            f"{prefix}Borrower {evidence['borrower_id']} has {len(facilities)} facility/facilities "
            f"in {', '.join(stages)} with rating(s) {', '.join(ratings) if ratings else 'not recorded'}. "
            f"Governed EAD is {total_ead:,.2f}, ECL is {total_ecl:,.2f}, "
            f"max facility PD is {max_pd:.2%}, and max LGD is {max_lgd:.2%}. "
            f"Key adverse indicators: {adverse_text}. "
            f"Risk direction: {', '.join(directions) if directions else 'not recorded'}; "
            f"Watchlist={'yes' if watchlist else 'no'}; SICR={'yes' if sicr else 'no'}. "
            f"Recorded stage reason(s): {', '.join(reasons) if reasons else 'none recorded'}."
        )


    def portfolio_detail(self, question, evidence):
        q = question.lower()
        if any(word in q for word in ("increase", "deteriorated most", "change since")):
            return "A single run cannot establish a change over time. Use the governed two-run movement endpoint; no causal explanation is inferred."

        customer_concentration = (
            ("customer" in q or "borrower" in q or "counterparty" in q)
            and (
                "concentration" in q
                or "top 5" in q
                or "top five" in q
                or "riskiest" in q
                or "largest" in q
            )
        )
        if customer_concentration:
            rows = evidence.get("top_borrowers_by_ecl", [])[:5]
            if not rows:
                return "No borrower-level concentration evidence is available for this run."
            total_ead = float(evidence.get("ead", 0.0) or 0.0)
            total_ecl = float(evidence.get("ecl", 0.0) or 0.0)
            top5_ead = sum(float(row.get("ead", 0.0)) for row in rows)
            top5_ecl = sum(float(row.get("ecl", 0.0)) for row in rows)
            ranked = []
            for idx, row in enumerate(rows, start=1):
                ead = float(row.get("ead", 0.0))
                ecl = float(row.get("ecl", 0.0))
                ranked.append(
                    f"{idx}) {row['borrower_id']} ({row.get('industry', 'n/a')}): "
                    f"Stage {str(row.get('stage', 'n/a')).replace('Stage ', '')}, "
                    f"rating {row.get('risk_rating', 'n/a')}, "
                    f"max PD {float(row.get('max_pd', 0.0)):.2%}, "
                    f"max LGD {float(row.get('max_lgd', 0.0)):.2%}, "
                    f"EAD {ead:,.2f} ({ead / total_ead:.2%} of portfolio), "
                    f"ECL {ecl:,.2f} ({ecl / total_ecl:.2%} of portfolio)"
                    if total_ead and total_ecl else
                    f"{idx}) {row['borrower_id']}: EAD {ead:,.2f}, ECL {ecl:,.2f}"
                )
            return (
                "For 'riskiest customers', this view ranks borrowers by governed reference ECL, "
                "which combines probability/severity with exposure rather than ranking by PD alone. "
                + " | ".join(ranked)
                + (
                    f" | Top-5 concentration: {top5_ead / total_ead:.2%} of portfolio EAD and "
                    f"{top5_ecl / total_ecl:.2%} of portfolio ECL."
                    if total_ead and total_ecl else ""
                )
            )

        by_industry = evidence.get("by_industry", {})
        broad = any(
            phrase in q
            for phrase in (
                "summarize", "summary", "risk profile", "main risk",
                "important areas", "human review", "portfolio risk",
            )
        )
        risk_industry_question = (
            ("risk" in q or "riskiest" in q or "risky" in q)
            and ("industr" in q or "sector" in q)
        )
        if risk_industry_question and by_industry:
            highest_pd = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("mean_pd", 0.0)), kv[0]),
            )
            highest_loss = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("loss_intensity", 0.0)), kv[0]),
            )
            highest_lgd = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("mean_lgd", 0.0)), kv[0]),
            )
            highest_ecl = max(
                by_industry.items(),
                key=lambda kv: (float(kv[1].get("ecl", 0.0)), kv[0]),
            )
            return (
                "There is no single universal definition of 'riskiest industry', so the answer "
                "depends on the risk measure. "
                f"Highest mean PD: {highest_pd[0]} at {highest_pd[1].get('mean_pd', 0.0):.2%}. "
                f"Highest ECL/EAD loss intensity: {highest_loss[0]} at "
                f"{highest_loss[1].get('loss_intensity', 0.0):.2%}. "
                f"Highest mean LGD: {highest_lgd[0]} at {highest_lgd[1].get('mean_lgd', 0.0):.2%}. "
                f"Largest absolute ECL concentration: {highest_ecl[0]} with "
                f"ECL {highest_ecl[1].get('ecl', 0.0):,.2f} on EAD "
                f"{highest_ecl[1].get('ead', 0.0):,.2f}. "
                "Use PD/loss intensity for relative credit risk and absolute ECL for portfolio "
                "loss concentration; do not treat those as the same concept."
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


def _flatten_context(value, prefix="", depth=0, max_depth=4):
    """Convert nested governed evidence into compact business-readable lines."""
    if depth > max_depth:
        return []
    lines = []
    if isinstance(value, dict):
        for key in sorted(value):
            child = value[key]
            name = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(child, (dict, list)):
                lines.extend(_flatten_context(child, name, depth + 1, max_depth))
            else:
                lines.append(f"{name}={child}")
    elif isinstance(value, list):
        for idx, child in enumerate(value[:40]):
            name = f"{prefix}[{idx}]"
            if isinstance(child, (dict, list)):
                lines.extend(_flatten_context(child, name, depth + 1, max_depth))
            else:
                lines.append(f"{name}={child}")
        if len(value) > 40:
            lines.append(f"{prefix}.additional_items={len(value) - 40}")
    else:
        lines.append(f"{prefix}={value}")
    return lines


def _llm_evidence_text(question: str, evidence: dict, use_case: str) -> str:
    """Comprehensive governed context for narrative reasoning; no raw JSON dump."""
    if use_case == "portfolio":
        lines = [
            "PORTFOLIO TOTALS",
            f"run_id={evidence.get('run_id')}",
            f"borrowers={evidence.get('borrower_count', 0)}",
            f"facilities={evidence.get('facility_count', 0)}",
            f"EAD={evidence.get('ead', 0.0):.2f}",
            f"ECL={evidence.get('ecl', 0.0):.2f}",
            f"reference_ECL={evidence.get('reference_ecl', evidence.get('ecl', 0.0))}",
            f"override_adjustment={evidence.get('override_adjustment', 0.0)}",
            f"controlled_reference_ECL={evidence.get('controlled_reference_ecl', evidence.get('ecl', 0.0))}",
            f"research_gate={evidence.get('bank_gate')}",
            "",
        ]

        dimensions = (
            ("STAGE", "by_stage"),
            ("INDUSTRY", "by_industry"),
            ("PRODUCT", "by_product"),
            ("RATING", "by_rating"),
            ("RISK DIRECTION", "by_risk_direction"),
            ("COLLATERAL TYPE", "by_collateral_type"),
        )
        for title, key in dimensions:
            lines.append(title)
            for name, row in sorted(evidence.get(key, {}).items()):
                lines.append(
                    f"{name}: borrowers={row.get('borrowers', 0)}, "
                    f"facilities={row.get('facilities', 0)}, "
                    f"EAD={row.get('ead', 0.0):.2f}, ECL={row.get('ecl', 0.0):.2f}, "
                    f"mean_PD={row.get('mean_pd', 0.0):.6f}, "
                    f"mean_LGD={row.get('mean_lgd', 0.0):.6f}, "
                    f"EAD_share={row.get('ead_share', 0.0):.6f}, "
                    f"ECL_share={row.get('ecl_share', 0.0):.6f}, "
                    f"ECL_to_EAD={row.get('loss_intensity', 0.0):.6f}"
                )
            lines.append("")

        lines.append("SPECIAL SEGMENTS")
        for key in ("watchlist", "unsecured", "guaranteed"):
            row = evidence.get(key, {})
            lines.append(
                f"{key}: borrowers={row.get('borrowers', 0)}, "
                f"facilities={row.get('facilities', 0)}, EAD={row.get('ead', 0.0):.2f}, "
                f"ECL={row.get('ecl', 0.0):.2f}, mean_PD={row.get('mean_pd', 0.0):.6f}, "
                f"mean_LGD={row.get('mean_lgd', 0.0):.6f}, "
                f"ECL_to_EAD={row.get('loss_intensity', 0.0):.6f}"
            )

        lines.append("")
        lines.append("SCENARIO PD")
        for name, value in sorted(evidence.get("scenario_mean_pd", {}).items()):
            lines.append(f"{name}={float(value):.6f}")

        lines.append("")
        lines.append("EWS TRIGGERS")
        for name, value in sorted(evidence.get("ews_trigger_counts", {}).items()):
            lines.append(f"{name}={value}")

        lines.append("")
        lines.append("STAGE REASONS")
        for name, value in sorted(evidence.get("stage_reason_counts", {}).items()):
            lines.append(f"{name}={value}")

        lines.append("")
        lines.append("RISK INDICATOR COUNTS")
        for name, value in sorted(evidence.get("risk_indicator_counts", {}).items()):
            lines.append(f"{name}={value}")

        lines.append("")
        lines.append("RISK PATTERNS")
        for row in evidence.get("risk_patterns", []):
            lines.append(
                f"{row.get('pattern')}: borrowers={row.get('borrowers', 0)}, "
                f"EAD={row.get('ead', 0.0):.2f}, mean_PD={row.get('mean_pd', 0.0):.6f}, "
                f"PD_vs_portfolio={row.get('pd_vs_portfolio', 0.0):.6f}, "
                f"ECL_to_EAD={row.get('ecl_to_ead', 0.0):.6f}, "
                f"loss_vs_portfolio={row.get('loss_vs_portfolio', 0.0):.6f}"
            )

        lines.append("")
        lines.append("TOP BORROWERS BY ECL")
        for idx, row in enumerate(evidence.get("top_borrowers_by_ecl", [])[:15], 1):
            lines.append(
                f"{idx}. {row.get('borrower_id')}: industry={row.get('industry')}, "
                f"stage={row.get('stage')}, rating={row.get('risk_rating')}, "
                f"risk_direction={row.get('risk_direction')}, watchlist={row.get('watchlist')}, "
                f"sicr={row.get('sicr')}, facilities={row.get('facilities')}, "
                f"EAD={row.get('ead', 0.0):.2f}, ECL={row.get('ecl', 0.0):.2f}, "
                f"max_PD={row.get('max_pd', 0.0):.6f}, max_LGD={row.get('max_lgd', 0.0):.6f}"
            )

        lines.append("")
        lines.append("TOP BORROWERS BY EAD")
        for idx, row in enumerate(evidence.get("top_borrowers_by_ead", [])[:15], 1):
            lines.append(
                f"{idx}. {row.get('borrower_id')}: industry={row.get('industry')}, "
                f"stage={row.get('stage')}, rating={row.get('risk_rating')}, "
                f"EAD={row.get('ead', 0.0):.2f}, ECL={row.get('ecl', 0.0):.2f}, "
                f"max_PD={row.get('max_pd', 0.0):.6f}, max_LGD={row.get('max_lgd', 0.0):.6f}"
            )

        lines.append("")
        lines.append("TOP FACILITY RISK CASES")
        for idx, row in enumerate(evidence.get("top_risk_cases", [])[:10], 1):
            lines.append(
                f"{idx}. facility={row.get('facility_id')}, borrower={row.get('borrower_id')}, "
                f"industry={row.get('industry')}, product={row.get('product')}, "
                f"stage={row.get('stage')}, rating={row.get('risk_rating')}, "
                f"risk_direction={row.get('risk_direction')}, PD={row.get('pd')}, "
                f"LGD={row.get('lgd')}, EAD={row.get('ead')}, ECL={row.get('ecl')}, "
                f"collateral={row.get('collateral_type')}, "
                f"guarantee_coverage={row.get('guarantee_coverage')}, "
                f"stage_reasons={row.get('stage_reasons')}"
            )

        lines.append("")
        lines.append("REVIEW ACTIONS")
        for idx, action in enumerate(evidence.get("portfolio_review_actions", [])[:10], 1):
            lines.append(f"{idx}. " + "; ".join(_flatten_context(action, max_depth=2)))

        lines.append("")
        lines.append("VALIDATION CONCENTRATIONS")
        for line in _flatten_context(evidence.get("concentrations", {}), max_depth=3):
            lines.append(line)

        if evidence.get("approved_overrides"):
            lines.append("")
            lines.append("APPROVED OVERRIDES")
            for line in _flatten_context(evidence.get("approved_overrides", []), max_depth=3):
                lines.append(line)

        return "\n".join(lines)

    if use_case in ("borrower", "credit_review"):
        profile = evidence.get("source_profile", {})
        features = profile.get("features", {})
        lines = [
            "BORROWER PROFILE",
            f"borrower_id={evidence.get('borrower_id')}",
            f"industry={evidence.get('industry')}",
            f"observed_at={profile.get('observed_at')}",
            f"research_gate={evidence.get('bank_gate')}",
            "",
            "BORROWER FEATURES",
        ]
        for key, value in sorted(features.items()):
            lines.append(f"{key}={value}")

        lines.append("")
        lines.append("FACILITY DECISION TRACES")
        for idx, row in enumerate(evidence.get("facilities", []), 1):
            lines.extend(
                [
                    f"Facility {idx}: id={row.get('facility_id')}, product={row.get('product')}",
                    f"  stage={row.get('stage')}, rating={row.get('risk_rating')}, "
                    f"risk_direction={row.get('risk_direction')}, watchlist={row.get('watchlist')}, "
                    f"sicr={row.get('sicr')}",
                    f"  PD={row.get('pd')}, PIT_PD={row.get('pit_pd')}, "
                    f"lifetime_PD={row.get('lifetime_pd')}, effective_PD={row.get('effective_pd')}",
                    f"  scenario_PD={row.get('scenario_pd')}",
                    f"  LGD={row.get('lgd')}, EAD={row.get('ead')}, ECL={row.get('ecl')}",
                    f"  remaining_months={row.get('remaining_months')}, "
                    f"collateral_type={row.get('collateral_type')}, "
                    f"collateral_coverage={row.get('collateral_coverage')}, "
                    f"guarantee_coverage={row.get('guarantee_coverage')}, lien_rank={row.get('lien_rank')}",
                    f"  drawn={row.get('drawn')}, limit={row.get('limit')}, face={row.get('face')}",
                    f"  stage_reasons={row.get('stage_reasons')}",
                    f"  EWS={row.get('ews')}",
                ]
            )
        return "\n".join(lines)

    lines = ["MODEL-RISK / RESEARCH EVIDENCE"]
    lines.extend(_flatten_context(evidence, max_depth=5))
    return "\n".join(lines)

BAD_NARRATIVE = re.compile(
    r"(json|python|code snippet|programming language|parse the data|data format|"
    r"custom format|import json|load the data)",
    re.IGNORECASE,
)


def _valid_narrative(answer: str) -> bool:
    text = answer.strip()
    return bool(text) and len(text) >= 40 and BAD_NARRATIVE.search(text) is None


class OpenAIResponsesProvider:
    """Optional OpenAI narrative provider over governed evidence only."""

    name = "openai-responses"
    version = "responses-v4-full-context"

    def __init__(self):
        self.key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_COPILOT_MODEL", "gpt-6.1-sol")
        if not self.key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI Copilot provider")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        verified = _verified_grounding(question, evidence, use_case)
        instruction = (
            "You are a senior Credit Risk analyst operating a governed research Copilot. "
            "Use the complete supplied platform evidence across borrower, facility, PD, rating, "
            "EWS, Watchlist, SICR, staging, LGD, EAD, ECL, macro scenarios, concentrations, "
            "risk patterns, validation, model-risk findings and governance. The verified "
            "question-specific facts are authoritative where provided. Do not contradict them, "
            "invent facts, replace governed calculations, approve overrides or promote models. "
            "Reason deeply across the available evidence and answer the actual question directly. "
            "Distinguish relative risk (PD/loss intensity), severity (LGD/security) and absolute "
            "portfolio concentration (EAD/ECL). If evidence is insufficient, say exactly what is missing."
        )
        body = json.dumps(
            {
                "model": self.model,
                "instructions": instruction,
                "input": (
                    f"Use case: {use_case}\nQuestion: {question}\n\n"
                    f"VERIFIED QUESTION-SPECIFIC FACTS:\n{verified}\n\n"
                    f"FULL GOVERNED CONTEXT AVAILABLE FOR REASONING:\n"
                    f"{_llm_evidence_text(question, evidence, use_case)}\n\n"
                    "Answer the question using any relevant evidence above. Preserve the verified "
                    "facts exactly where they apply. You may synthesize relationships, explain risk "
                    "drivers and prioritize review areas, but do not invent facts or override governed "
                    "calculations. For any exact ranking, concentration or arithmetic, rely on the "
                    "verified facts or explicit supplied values."
                ),
                "max_output_tokens": 900,
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
        if not answer or not _valid_narrative(answer):
            return verified
        return answer


class OllamaProvider:
    """Optional local conversational provider; deterministic facts remain authoritative."""

    name = "ollama-local"
    version = "ollama-v5-full-context"

    def __init__(self):
        self.endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    def render(self, question: str, evidence: dict, use_case: str) -> str:
        verified = _verified_grounding(question, evidence, use_case)
        evidence_text = _llm_evidence_text(question, evidence, use_case)
        system = (
            "You are a senior Credit Risk analyst operating a governed research Copilot. "
            "You have access to the full evidence packet for the selected scope: borrower and "
            "facility attributes, PD, internal ratings, EWS, Watchlist, SICR, staging, LGD, EAD, "
            "ECL, macro scenarios, concentrations, collateral/guarantees, risk patterns, model "
            "validation, research findings and governance where available. Use all relevant evidence "
            "needed to answer the user's question. Do not discuss data formats, JSON, parsing, Python, "
            "code, prompts or the mechanics of how evidence was supplied. Never invent a number or "
            "claim. The VERIFIED QUESTION-SPECIFIC FACTS are authoritative for exact calculations, "
            "rankings and policy conclusions. You may synthesize qualitative relationships and explain "
            "why facts matter. Distinguish PD/default risk, LGD/severity, EAD/concentration and ECL. "
            "Do not say Stage 1 means high risk. Do not interpret a research/model gate as a ban on "
            "new lending. Do not approve credit decisions, overrides or model promotion. "
            "Answer directly in concise professional prose or bullets."
        )
        prompt = (
            f"Question: {question}\n\n"
            f"VERIFIED QUESTION-SPECIFIC FACTS:\n{verified}\n\n"
            f"FULL GOVERNED CONTEXT AVAILABLE FOR REASONING:\n{evidence_text}\n\n"
            "Use any relevant evidence above to answer the question. Keep exact quantitative claims "
            "anchored to supplied values and the verified facts."
        )
        body = json.dumps(
            {
                "model": self.model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.08,
                    "num_predict": int(os.environ.get("OLLAMA_NUM_PREDICT", "640")),
                    "num_ctx": int(os.environ.get("OLLAMA_NUM_CTX", "16384")),
                },
            }
        ).encode()
        req = Request(self.endpoint, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=180) as response:  # nosec: explicit local/configured endpoint
            result = json.loads(response.read(4_000_000))
        answer = result.get("response")
        if not isinstance(answer, str) or not _valid_narrative(answer):
            return verified
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


def _exact_analytics_intent(question: str, use_case: str) -> bool:
    q = question.lower()
    if use_case in ("borrower", "credit_review"):
        return any(
            token in q
            for token in (
                "adverse", "indicator", "driver", "risk factor", "warning",
                "utilization", "delinquen", "past due", "dpd", "leverage",
                "governed credit-risk decision", "main drivers",
            )
        )
    if use_case == "portfolio":
        customer_terms = ("customer" in q or "borrower" in q or "counterparty" in q)
        concentration_terms = any(
            token in q
            for token in ("concentration", "top 5", "top five", "riskiest", "largest")
        )
        industry_risk = (
            ("industr" in q or "sector" in q)
            and ("risk" in q or "riskiest" in q or "risky" in q)
        )
        return (customer_terms and concentration_terms) or industry_risk
    return False


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
