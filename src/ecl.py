"""Simplified IFRS 9-style staging and ECL mechanics for synthetic data.

This module demonstrates the distinction between:
- Stage 1: performing exposures, 12-month ECL;
- Stage 2: performing exposures with significant increase in credit risk (SICR),
  represented here by observable deterioration proxies, lifetime ECL;
- Stage 3: credit-impaired/defaulted exposures, lifetime ECL.

It is educational and deliberately simplified; it is not an IFRS 9 accounting engine.
"""
import numpy as np


def assign_stage(df, pd_col="predicted_pd"):
    out = df.copy()

    dpd = out["days_past_due"].fillna(0)
    defaults = out["default"].fillna(0).astype(int)
    delinq = out["delinquencies_12m"].fillna(0)
    prev_default = out["previous_defaults"].fillna(0)
    util = out["credit_utilization"].fillna(0)

    # Stage 3: credit-impaired/default proxy. Default observations take precedence;
    # 90+ DPD is used as a conventional synthetic backstop.
    stage3 = (defaults == 1) | (dpd >= 90)

    # Stage 2: simplified SICR proxy for non-credit-impaired borrowers.
    # We use deterioration/conduct indicators rather than an absolute PD threshold.
    stage2 = (~stage3) & (
        (dpd >= 30)
        | (delinq >= 2)
        | ((util >= 0.85) & (dpd > 0))
        | ((prev_default >= 1) & (out[pd_col] >= 0.05))
    )

    out["stage"] = np.select(
        [stage3, stage2],
        ["Stage 3", "Stage 2"],
        default="Stage 1",
    )
    out["sicr_flag"] = (out["stage"] == "Stage 2").astype(int)
    return out


def calculate_ecl(
    df,
    pd_col="predicted_pd",
    lgd_col="lgd",
    ead_col="ead",
    lifetime_pd_multiplier=2.5,
):
    out = assign_stage(df, pd_col=pd_col)

    pd12 = out[pd_col].clip(0, 1)
    lgd = out[lgd_col].clip(0, 1)
    ead = out[ead_col].clip(lower=0)

    out["ecl_12m"] = pd12 * lgd * ead

    # Simplified cumulative lifetime PD proxy for Stage 2. Stage 3 uses PD=100%
    # because the exposure is already credit-impaired/defaulted in this demo.
    lifetime_pd = (pd12 * lifetime_pd_multiplier).clip(upper=1.0)
    out["ecl"] = out["ecl_12m"]
    out.loc[out["stage"] == "Stage 2", "ecl"] = (
        lifetime_pd * lgd * ead
    )[out["stage"] == "Stage 2"]
    out.loc[out["stage"] == "Stage 3", "ecl"] = (
        lgd * ead
    )[out["stage"] == "Stage 3"]

    out["lifetime_ecl"] = out["ecl"]
    return out
