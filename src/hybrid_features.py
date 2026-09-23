"""Governed nested information sets for incremental PD experiments.

All variables used here already exist in the synthetic portfolio generated upstream.
No holdout-wide quantiles or synthetic qualitative re-encodings are created here.
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


def feature_sets(df):
    """Return three nested, economically distinct information sets."""
    financial = [c for c in FINANCIAL_FEATURES if c in df.columns]
    current_behavior = financial + [
        c for c in CURRENT_BEHAVIOR_FEATURES if c in df.columns
    ]
    trajectory = current_behavior + [
        c for c in TRAJECTORY_FEATURES if c in df.columns
    ]

    industry_cols = [c for c in df.columns if c.startswith("industry_")]
    return {
        "Financial only": financial + industry_cols,
        "Financial + Current Behavior": current_behavior + industry_cols,
        "Financial + Current Behavior + Trajectory": trajectory + industry_cols,
    }
