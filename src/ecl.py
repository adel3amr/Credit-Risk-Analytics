"""Simplified IFRS 9-style staging and ECL mechanics for synthetic data.

Reporting-date credit impairment is kept separate from the future 12-month
default outcome used to validate the PD model. Stage 2 uses observable SICR
proxies. This is an educational implementation, not an IFRS 9 accounting engine.
"""
import numpy as np
import pandas as pd
from pathlib import Path

# Explicit forward-looking macro scenarios. The economic paths and PD odds
# multipliers are transparent synthetic assumptions, fixed independently of the
# holdout outcome. They are not presented as official forecasts or empirically
# estimated macro elasticities.
MACRO_SCENARIO_FILE = Path(__file__).resolve().parents[1] / "config" / "macro_scenarios.csv"


def load_macro_scenarios(path=MACRO_SCENARIO_FILE):
    scenarios = pd.read_csv(path)
    required = {"scenario", "weight", "real_gdp_growth_pct", "unemployment_rate_pct",
                "policy_rate_pct", "inflation_pct"}
    missing = required.difference(scenarios.columns)
    if missing:
        raise ValueError(f"Missing macro scenario fields: {sorted(missing)}")
    if not np.isclose(scenarios["weight"].sum(), 1.0):
        raise ValueError("Macro scenario weights must sum to 1.0")
    if (scenarios["weight"] < 0).any():
        raise ValueError("Scenario weights must be non-negative")
    return scenarios



# Synthetic macro-to-credit sensitivity mapping on log-odds. Coefficients are
# fixed methodology assumptions, not estimated from the holdout or presented as
# empirical elasticities. All shocks are measured relative to the baseline row.
MACRO_LOG_ODDS_SENSITIVITY = {
    "real_gdp_growth_pct": -0.10,
    "unemployment_rate_pct": 0.08,
    "policy_rate_pct": 0.06,
    "inflation_pct": 0.03,
}


def macro_odds_multiplier(row, baseline):
    log_odds_shift = sum(
        beta * (float(row[var]) - float(baseline[var]))
        for var, beta in MACRO_LOG_ODDS_SENSITIVITY.items()
    )
    return float(np.exp(log_odds_shift))

def _shift_pd_odds(pd, multiplier):
    """Apply a scenario multiplier to default odds while keeping PD in (0,1)."""
    p = np.clip(pd, 1e-8, 1 - 1e-8)
    odds = p / (1 - p)
    shifted_odds = odds * multiplier
    return shifted_odds / (1 + shifted_odds)


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
    # Governed model output is a reporting-date, borrower-level 12M PIT-oriented
    # PD. A separate scenario layer adds explicit forward-looking information.
    pit_pd12 = out[pd_col].clip(0, 1)
    out["pit_pd_12m"] = pit_pd12

    macro_scenarios = load_macro_scenarios()
    baseline_rows = macro_scenarios[macro_scenarios["scenario"].str.lower() == "baseline"]
    if len(baseline_rows) != 1:
        raise ValueError("Macro scenario table must contain exactly one baseline row")
    baseline = baseline_rows.iloc[0]

    scenario_pds = {}
    scenario_weights = {}
    for _, row in macro_scenarios.iterrows():
        scenario = str(row["scenario"])
        odds_multiplier = macro_odds_multiplier(row, baseline)
        out[f"macro_odds_multiplier_{scenario}"] = odds_multiplier
        scenario_pd = _shift_pd_odds(pit_pd12, odds_multiplier)
        out[f"pd_12m_{scenario}"] = scenario_pd
        scenario_pds[scenario] = scenario_pd
        scenario_weights[scenario] = float(row["weight"])

    forward_pd12 = sum(
        scenario_weights[s] * scenario_pds[s] for s in scenario_pds
    )
    out["forward_looking_pd_12m"] = forward_pd12.clip(0, 1)

    lgd = out[lgd_col].clip(0, 1)
    ead = out[ead_col].clip(lower=0)

    # Probability-weighted forward-looking 12M ECL. LGD and EAD are held constant
    # across scenarios in V2 so the macro overlay is isolated to PD.
    out["ecl_12m"] = out["forward_looking_pd_12m"] * lgd * ead

    # Approximate cumulative PD under a constant annual hazard over remaining
    # contractual term. This replaces the previous arbitrary 2.5x multiplier.
    # Portfolio-level approximation only: the current synthetic schema has one
    # borrower-level term even when a borrower also has OVD/trade facilities.
    # Cap at the contractual term generated for the borrower; do not impose a
    # minimum one-year remaining life on shorter residual terms.
    remaining_years = np.maximum(out["loan_term_months"].fillna(12) / 12.0, 0.0)
    # Apply the same scenario logic over the simplified constant-hazard term
    # structure, then probability-weight the scenario lifetime PDs.
    scenario_lifetime = {}
    for scenario, scenario_pd in scenario_pds.items():
        lp = 1.0 - np.power(1.0 - scenario_pd, remaining_years)
        out[f"lifetime_pd_{scenario}"] = lp.clip(0, 1)
        scenario_lifetime[scenario] = out[f"lifetime_pd_{scenario}"]
    out["lifetime_pd"] = sum(
        scenario_weights[s] * scenario_lifetime[s] for s in scenario_lifetime
    ).clip(0, 1)

    out["ecl"] = out["ecl_12m"]
    s2 = out["stage"] == "Stage 2"
    s3 = out["stage"] == "Stage 3"
    out.loc[s2, "ecl"] = (out["lifetime_pd"] * lgd * ead)[s2]
    # Credit-impaired proxy: PD=100%; discounting/recovery timing is out of scope.
    out.loc[s3, "ecl"] = (lgd * ead)[s3]
    out["lifetime_ecl"] = out["ecl"]
    return out
