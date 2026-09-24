"""Prediction-time contract: no targets, future recoveries or unrecognized fields."""

import math
from src.data_preparation import PD_BASE_FEATURES, PD_QUALITATIVE_FEATURES

PD_FEATURES = PD_BASE_FEATURES + PD_QUALITATIVE_FEATURES
EWS_FEATURES = [
    "utilization_6m_change",
    "avg_utilization_6m",
    "months_above_80_utilization",
    "limit_breach_count",
    "consecutive_ews_months",
]
POLICY_FEATURES = [
    "current_credit_impaired",
    "write_off_flag",
    "recognized_collateral_coverage",
]
BORROWER_FEATURES = list(dict.fromkeys(PD_FEATURES + EWS_FEATURES + POLICY_FEATURES))
INDUSTRIES = [
    "Construction",
    "Hospitality",
    "Manufacturing",
    "Retail",
    "Services",
    "Technology",
    "Transport",
]
PRODUCTS = [
    "Term Loan",
    "OVD",
    "Import LC",
    "Performance Guarantee",
    "Financial Guarantee",
]
COLLATERAL = ["Cash", "Mortgage", "Other", "Unsecured"]


def check_features(features):
    missing = set(BORROWER_FEATURES) - set(features)
    extra = set(features) - set(BORROWER_FEATURES)
    if missing or extra:
        raise ValueError(
            f"Feature contract mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    for k, v in features.items():
        if (
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
        ):
            raise ValueError(f"{k}: finite numeric value required")
        if k not in ("ebitda_margin", "utilization_6m_change") and v < 0:
            raise ValueError(f"{k}: negative value prohibited")
        if k in PD_QUALITATIVE_FEATURES[:5] and (v < 1 or v > 5 or int(v) != v):
            raise ValueError(f"{k}: integer assessment 1..5 required")
        if (
            k in ("customer_concentration", "supplier_concentration")
            and not 0 <= v <= 1
        ):
            raise ValueError(f"{k}: fraction 0..1 required")
        if k == "audit_quality" and v not in (1, 2, 3):
            raise ValueError("audit_quality: assessment 1..3 required")
        if k in (
            "current_credit_impaired",
            "write_off_flag",
            "key_person_dependency",
        ) and v not in (0, 1):
            raise ValueError(f"{k}: binary value required")
        if (
            k
            in (
                "months_above_80_utilization",
                "limit_breach_count",
                "consecutive_ews_months",
                "days_past_due",
                "delinquencies_12m",
                "previous_defaults",
            )
            and int(v) != v
        ):
            raise ValueError(f"{k}: integer required")
    if (
        features["months_above_80_utilization"] > 6
        or features["consecutive_ews_months"] > 36
    ):
        raise ValueError("Conduct count exceeds source window")
    return features
