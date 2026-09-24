"""V5 method adapter. No challenger promotion and no hidden missing-value defaults."""

import math
import numpy as np
import pandas as pd
from .common import ROOT, digest, file_hash
from .contracts import PD_FEATURES
from src.ecl import assign_stage, macro_odds_multiplier, _shift_pd_odds
from src.scorecard import add_score, add_risk_rating

CCF = {"Import LC": 0.2, "Performance Guarantee": 0.5, "Financial Guarantee": 1.0}


def validated_lgd_prediction(model, features):
    """Preserve V5 finite clipping, reject corrupt or incomplete model output first."""
    raw = np.asarray(model.predict(features), dtype=float)
    if raw.shape != (len(features),) or not np.isfinite(raw).all():
        raise ValueError("LGD model must return one finite prediction per facility")
    return np.clip(raw, 0.0, 1.0)


def ead(f):
    if f["product"] == "Term Loan":
        return f["drawn"]
    if f["product"] == "OVD":
        return f["limit"]
    return float(np.round(f["face"] * CCF[f["product"]], 2))


def policy():
    scenarios = pd.read_csv(ROOT / "config/macro_scenarios.csv").to_dict("records")
    if len([s for s in scenarios if s["scenario"] == "baseline"]) != 1:
        raise ValueError("Exactly one baseline required")
    if len({s["scenario"] for s in scenarios}) != len(scenarios):
        raise ValueError("Duplicate scenarios")
    if not math.isclose(sum(s["weight"] for s in scenarios), 1, abs_tol=1e-12):
        raise ValueError("Invalid scenario weights")
    for s in scenarios:
        if s["weight"] < 0 or any(
            not math.isfinite(v) for k, v in s.items() if k != "scenario"
        ):
            raise ValueError("Invalid scenario")
    return {
        "id": "v5-reference-policy-1",
        "staging": "v5-internal-nine-month",
        "ead": "v5-ccf-1",
        "ews": "v5-three-signals",
        "ecl": "v5-facility-hazard-1",
        "rating": "v5-rating-1",
        "ccf": CCF,
        "scenarios": scenarios,
        "scenario_source_hash": file_hash(ROOT / "config/macro_scenarios.csv"),
    }


def reasons(row):
    triggers = []
    conditions = {
        "credit_impaired": row.current_credit_impaired == 1,
        "dpd_90": row.days_past_due >= 90,
        "dpd_30": row.days_past_due >= 30,
        "multiple_delinquencies": row.delinquencies_12m >= 2,
        "utilization_with_arrears": row.credit_utilization >= 0.85
        and row.days_past_due > 0,
        "prior_default_pd": row.previous_defaults >= 1 and row.predicted_pd >= 0.05,
        "persistent_ews_9_months": row.ews_sicr_flag == 1
        and row.consecutive_ews_months >= 9,
    }
    triggers = [k for k, v in conditions.items() if v]
    return triggers or ["no_stage2_or_stage3_trigger"]


def score(dataset, models, manifest, configuration):
    raw = pd.DataFrame(
        [
            {
                "customer_id": b["id"],
                "industry": b["industry"],
                "collateral_type": b["collateral_type"],
                **b["features"],
            }
            for b in dataset["borrowers"]
        ]
    )
    unknown = set(raw.industry) - set(manifest["industries"])
    if unknown:
        raise ValueError(f"Industry outside training support: {sorted(unknown)}")
    x = raw[PD_FEATURES].copy()
    for col in manifest["pd_columns"]:
        if col.startswith("industry_"):
            x[col] = raw.industry.eq(col[len("industry_") :]).astype(int)
    raw["predicted_pd"] = models["pd"].predict_proba(x[manifest["pd_columns"]])[:, 1]
    if (
        not np.isfinite(raw.predicted_pd).all()
        or not raw.predicted_pd.between(0, 1).all()
    ):
        raise ValueError("Model returned invalid PD")
    raw = assign_stage(raw)
    raw = add_score(raw)
    raw = add_risk_rating(raw)
    baseline = next(
        s for s in configuration["scenarios"] if s["scenario"] == "baseline"
    )
    scenario_pds = {
        s["scenario"]: _shift_pd_odds(
            raw.predicted_pd, macro_odds_multiplier(s, baseline)
        )
        for s in configuration["scenarios"]
    }
    raw["forward_pd"] = sum(
        s["weight"] * scenario_pds[s["scenario"]] for s in configuration["scenarios"]
    )
    scenario_by_borrower = {
        key: dict(zip(raw.customer_id, values)) for key, values in scenario_pds.items()
    }
    borrowers = raw.set_index("customer_id")
    source = {b["id"]: b for b in dataset["borrowers"]}
    frows = []
    for f in dataset["facilities"]:
        b = borrowers.loc[f["borrower_id"]]
        frows.append(
            {
                "facility_id": f["id"],
                "customer_id": f["borrower_id"],
                "ead_at_default": ead(f),
                "collateral_type": f["collateral_type"],
                "collateral_coverage": f["collateral_coverage"],
                "guarantee_coverage": f["guarantee_coverage"],
                "product_type": f["product"],
                "lien_rank": f["lien_rank"],
                "industry": b.industry,
                "leverage_at_default": b.leverage_ratio,
                "current_ratio_at_default": b.current_ratio,
                "management_quality": b.management_quality,
            }
        )
    if not frows:
        return []
    features = pd.DataFrame(frows)
    predictions = validated_lgd_prediction(models["lgd"], features)
    traces = []
    for f, feat, lgd in zip(dataset["facilities"], frows, predictions):
        b = borrowers.loc[f["borrower_id"]]
        p = float(b.forward_pd)
        e = feat["ead_at_default"]
        lgd = float(lgd)
        lifetime = 1 - (1 - p) ** (f["remaining_months"] / 12)
        effective = (
            1 if b.stage == "Stage 3" else lifetime if b.stage == "Stage 2" else p
        )
        signals = [
            {
                "id": k,
                "triggered": bool(b[k]),
                "effective_date": dataset["effective_date"],
                "source": "borrower conduct",
                "policy_version": configuration["ews"],
            }
            for k in [
                "ews_rising_utilization",
                "ews_persistent_high_utilization",
                "ews_limit_breach",
            ]
        ]
        trace = {
            "facility_id": f["id"],
            "borrower_id": f["borrower_id"],
            "reporting_date": dataset["effective_date"],
            "stage": b.stage,
            "stage_reasons": reasons(b),
            "sicr": bool(b.sicr_flag),
            "watchlist": int(b.risk_rating) == 7,
            "risk_rating": int(b.risk_rating),
            "risk_direction": b.risk_direction,
            "ews": signals,
            "pd": p,
            "pit_pd": float(b.predicted_pd),
            "scenario_pd": {
                k: float(v[b.name]) for k, v in scenario_by_borrower.items()
            },
            "remaining_months": f["remaining_months"],
            "lifetime_pd": lifetime,
            "effective_pd": effective,
            "lgd": lgd,
            "ead": e,
            "ecl": effective * lgd * e,
            "lgd_features": feat,
            "source_facility": f,
            "source_borrower": source[f["borrower_id"]],
            "model_version": manifest["version"],
            "artifact_hashes": manifest["artifacts"],
            "configuration_hash": digest(configuration),
            "use": "REFERENCE ONLY; bank gate BLOCKED",
        }
        traces.append(trace)
    return traces
