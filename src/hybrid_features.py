"""Hybrid SME PD feature engineering.

The original portfolio is synthetic. This module deterministically derives additional
behavioural-trend and qualitative/relationship features from existing borrower
attributes so the experiment is reproducible without representing the fields as
observed bank data.

These features are for methodology demonstration, not production calibration.
"""
import numpy as np
import pandas as pd


FINANCIAL_FEATURES = [
    "ebitda_margin", "leverage_ratio", "current_ratio", "debt_to_income",
    "collateral_coverage", "years_in_business",
]

BEHAVIORAL_FEATURES = [
    "credit_utilization", "delinquencies_12m", "previous_defaults",
    "days_past_due", "utilization_6m_change", "avg_utilization_6m",
    "months_above_80_utilization", "limit_breach_count",
]

QUALITATIVE_FEATURES = [
    "relationship_years", "management_quality", "financial_reporting_quality",
    "information_cooperation", "account_conduct", "covenant_compliance",
]


def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def add_hybrid_features(df, random_state=42):
    """Add reproducible synthetic trend, relationship and qualitative features.

    No target/default field is used to construct these variables. They are based
    only on contemporaneous borrower characteristics plus seeded noise, reducing
    direct target leakage in the demonstration.
    """
    out = df.copy()
    rng = np.random.default_rng(random_state)
    n = len(out)

    util = out["credit_utilization"].astype(float)
    # Handle either 0-1 or 0-100 representations.
    util01 = util / 100.0 if util.quantile(.95) > 1.5 else util
    util01 = _clip01(util01)

    dpd = out["days_past_due"].fillna(0).astype(float)
    delinq = out["delinquencies_12m"].fillna(0).astype(float)
    prev_def = out["previous_defaults"].fillna(0).astype(float)
    leverage = out["leverage_ratio"].fillna(out["leverage_ratio"].median()).astype(float)
    liquidity = out["current_ratio"].fillna(out["current_ratio"].median()).astype(float)
    margin = out["ebitda_margin"].fillna(out["ebitda_margin"].median()).astype(float)
    years_business = out["years_in_business"].fillna(0).astype(float)

    # Behavioural direction: percentage-point change over an illustrative 6M window.
    stress = (
        0.35 * util01
        + 0.20 * np.clip(dpd / 90, 0, 1)
        + 0.15 * np.clip(delinq / 3, 0, 1)
        + 0.15 * np.clip(leverage / max(leverage.quantile(.95), 1e-6), 0, 1)
        + 0.15 * np.clip(1 - liquidity / max(liquidity.quantile(.95), 1e-6), 0, 1)
    )
    util_change = np.clip(rng.normal((stress - .40) * .22, .08, n), -.35, .45)
    out["utilization_6m_change"] = util_change
    out["avg_utilization_6m"] = _clip01(util01 - util_change / 2)
    out["months_above_80_utilization"] = np.clip(
        np.rint(6 * _clip01((out["avg_utilization_6m"] - .55) / .35)
                + rng.normal(0, .8, n)), 0, 6
    ).astype(int)
    out["limit_breach_count"] = np.clip(
        rng.poisson(_clip01((util01 - .78) / .18) * 1.5), 0, 5
    ).astype(int)

    # Relationship tenure cannot exceed business age in this synthetic framework.
    relationship_fraction = rng.beta(2.2, 2.0, n)
    out["relationship_years"] = np.floor(
        np.maximum(0, years_business * relationship_fraction)
    ).astype(int)

    # Ordinal qualitative assessments: 1=weak, 2=adequate, 3=strong.
    financial_strength = (
        .35 * np.clip((margin - margin.quantile(.10)) /
                      max(margin.quantile(.90) - margin.quantile(.10), 1e-6), 0, 1)
        + .35 * np.clip(liquidity / max(liquidity.quantile(.90), 1e-6), 0, 1)
        + .30 * (1 - np.clip(leverage / max(leverage.quantile(.90), 1e-6), 0, 1))
    )
    conduct_strength = _clip01(
        1 - (.40 * util01 + .30 * np.clip(dpd / 60, 0, 1)
             + .20 * np.clip(delinq / 3, 0, 1) + .10 * np.clip(prev_def, 0, 1))
    )

    def ordinal(latent):
        noisy = _clip01(latent + rng.normal(0, .13, n))
        return np.select([noisy < .36, noisy < .68], [1, 2], default=3).astype(int)

    out["management_quality"] = ordinal(.60 * financial_strength + .40 * conduct_strength)
    out["financial_reporting_quality"] = ordinal(
        .45 * financial_strength + .35 * conduct_strength
        + .20 * np.clip(years_business / 15, 0, 1)
    )
    out["information_cooperation"] = ordinal(
        .70 * conduct_strength + .30 * np.clip(out["relationship_years"] / 10, 0, 1)
    )
    out["account_conduct"] = ordinal(conduct_strength)
    out["covenant_compliance"] = (
        (dpd < 30) & (out["limit_breach_count"] == 0) & (prev_def == 0)
    ).astype(int)

    return out


def feature_sets(df):
    """Return available columns for nested information-set experiments."""
    financial = [c for c in FINANCIAL_FEATURES if c in df.columns]
    behavioural = financial + [c for c in BEHAVIORAL_FEATURES if c in df.columns]
    hybrid = behavioural + [c for c in QUALITATIVE_FEATURES if c in df.columns]

    # Industry is known at underwriting and is retained in each information set.
    industry_cols = [c for c in df.columns if c.startswith("industry_")]
    return {
        "Financial only": financial + industry_cols,
        "Financial + Behavioral": behavioural + industry_cols,
        "Hybrid": hybrid + industry_cols,
    }
