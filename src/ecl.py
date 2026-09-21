"""Simplified IFRS 9-style staging and ECL mechanics for synthetic data.

Reporting-date credit impairment is kept separate from the future 12-month
default outcome used to validate the PD model. Stage 2 uses observable SICR
proxies. This is an educational implementation, not an IFRS 9 accounting engine.
"""
import numpy as np

try:
    from early_warning import add_early_warning_signals
except ImportError:
    from src.early_warning import add_early_warning_signals


def assign_stage(df, pd_col="predicted_pd"):
    out = add_early_warning_signals(df)
    dpd = out["days_past_due"].fillna(0)
    impaired = out["current_credit_impaired"].fillna(0).astype(int)
    delinq = out["delinquencies_12m"].fillna(0)
    prev_default = out["previous_defaults"].fillna(0)
    util = out["credit_utilization"].fillna(0)
    watchlist_months = out["months_on_ews_watchlist"].fillna(0)

    # Reporting-date credit-impaired state only. Future default outcome is never
    # consulted in staging.
    stage3 = (impaired == 1) | (dpd >= 90)

    # Simplified SICR proxy / 30-DPD backstop for non-credit-impaired exposures.
    # EWS is not an immediate Stage 2 trigger. Under this explicit synthetic policy,
    # a borrower that remains EWS-deteriorating on the watchlist for >=9 months is
    # transferred to Stage 2. The nine-month threshold is a project policy assumption,
    # not an IFRS 9 requirement. A production IFRS 9 SICR
    # assessment would compare reporting-date default risk with risk at initial
    # recognition and incorporate reasonable/supportable forward-looking information.
    stage2 = (~stage3) & (
        (dpd >= 30)
        | (delinq >= 2)
        | ((util >= 0.85) & (dpd > 0))
        | ((prev_default >= 1) & (out[pd_col] >= 0.05))
        | ((out["ews_sicr_flag"] == 1) & (watchlist_months >= 9))
    )

    out["stage"] = np.select(
        [stage3, stage2], ["Stage 3", "Stage 2"], default="Stage 1"
    )
    out["sicr_flag"] = (out["stage"] == "Stage 2").astype(int)
    return out


def calculate_ecl(df, pd_col="predicted_pd", lgd_col="lgd", ead_col="ead"):
    out = assign_stage(df, pd_col=pd_col)
    pd12 = out[pd_col].clip(0, 1)
    lgd = out[lgd_col].clip(0, 1)
    ead = out[ead_col].clip(lower=0)

    out["ecl_12m"] = pd12 * lgd * ead

    # Approximate cumulative PD under a constant annual hazard over remaining
    # contractual term. This replaces the previous arbitrary 2.5x multiplier.
    # Portfolio-level approximation only: the current synthetic schema has one
    # borrower-level term even when a borrower also has OVD/trade facilities.
    # Cap at the contractual term generated for the borrower; do not impose a
    # minimum one-year remaining life on shorter residual terms.
    remaining_years = np.maximum(out["loan_term_months"].fillna(12) / 12.0, 0.0)
    lifetime_pd = 1.0 - np.power(1.0 - pd12, remaining_years)
    out["lifetime_pd"] = lifetime_pd.clip(0, 1)

    out["ecl"] = out["ecl_12m"]
    s2 = out["stage"] == "Stage 2"
    s3 = out["stage"] == "Stage 3"
    out.loc[s2, "ecl"] = (out["lifetime_pd"] * lgd * ead)[s2]
    # Credit-impaired proxy: PD=100%; discounting/recovery timing is out of scope.
    out.loc[s3, "ecl"] = (lgd * ead)[s3]
    out["lifetime_ecl"] = out["ecl"]
    return out
