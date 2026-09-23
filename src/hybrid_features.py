"""Nested SME PD information sets for incremental-information testing.

All variables are generated upstream as distinct reporting-date information.
No feature in this module is reconstructed from the holdout distribution or
re-encoded from the quantitative variables it is meant to challenge.
"""

FINANCIAL_FEATURES = [
    "ebitda_margin", "leverage_ratio", "current_ratio", "debt_to_income",
    "collateral_coverage", "years_in_business",
]

CURRENT_BEHAVIOR_FEATURES = [
    "credit_utilization", "delinquencies_12m", "previous_defaults", "days_past_due",
]

TRAJECTORY_FEATURES = [
    "utilization_6m_change", "avg_utilization_6m",
    "months_above_80_utilization", "limit_breach_count",
]

QUALITATIVE_FEATURES = [
    "management_quality", "governance_quality", "financial_reporting_quality",
    "market_position", "sponsor_support", "customer_concentration",
    "supplier_concentration", "key_person_dependency", "audit_quality",
]


def add_hybrid_features(df):
    """Validate presence of separately generated information; do not derive it."""
    out = df.copy()
    required = TRAJECTORY_FEATURES + QUALITATIVE_FEATURES
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(
            "Missing generated hybrid information: " + ", ".join(missing)
            + ". Regenerate the portfolio with scripts/generate_sme_portfolio.py."
        )
    return out


def feature_sets(df):
    """Return nested information sets using only reporting-date observed fields."""
    financial = [c for c in FINANCIAL_FEATURES if c in df.columns]
    current_behavior = financial + [c for c in CURRENT_BEHAVIOR_FEATURES if c in df.columns]
    trajectory = current_behavior + [c for c in TRAJECTORY_FEATURES if c in df.columns]
    hybrid = trajectory + [c for c in QUALITATIVE_FEATURES if c in df.columns]
    industry_cols = [c for c in df.columns if c.startswith("industry_")]
    return {
        "Financial only": financial + industry_cols,
        "Financial + Current Behavior": current_behavior + industry_cols,
        "Financial + Current Behavior + Trajectory": trajectory + industry_cols,
        "Full Hybrid + Independent Qualitative": hybrid + industry_cols,
    }
