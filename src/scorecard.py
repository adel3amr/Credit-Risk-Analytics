import numpy as np
import pandas as pd

def pd_to_score(pd_value, base_score=600, base_odds=20, pdo=50):
    pd_value=np.clip(pd_value,1e-6,1-1e-6)
    odds=(1-pd_value)/pd_value
    return base_score + pdo*np.log2(odds/base_odds)

def risk_band(pd_value):
    if pd_value < .03: return "Low"
    if pd_value < .08: return "Moderate"
    if pd_value < .15: return "High"
    return "Very High"

def add_score(df,pd_col="predicted_pd"):
    out=df.copy()
    out["credit_score"]=pd_to_score(out[pd_col])
    out["risk_band"]=out[pd_col].apply(risk_band)
    return out


def add_risk_rating(df, pd_col="predicted_pd"):
    """Operational 1-10 risk rating, kept distinct from the continuous credit score.

    1: reserved for full eligible cash coverage
    2-6: performing PD grades
    7: operational watchlist / enhanced monitoring
    8-10: non-performing Stage 3 severity grades

    Full eligible cash coverage can produce Rating 1 only in Stage 1.
    It does not override Stage 2 or Stage 3 classification.
    """
    out = df.copy()
    pdv = out[pd_col].clip(0, 1)
    if pdv.isna().any():
        raise ValueError("Risk rating requires non-null predicted PD values")
    # Broad, transparent performing-grade cut points; not fitted on the holdout.
    rating = pd.cut(
        pdv,
        bins=[-np.inf, .005, .01, .02, .04, np.inf],
        labels=[2, 3, 4, 5, 6],
    ).astype(int)

    watch = out.get("ews_monitoring_flag", pd.Series(0, index=out.index)).fillna(0).astype(bool)
    if "risk_direction" in out.columns:
        watch = watch | out["risk_direction"].eq("Deteriorating")
    # Internal policy: Stage 2 normally maps to Rating 7 / Watchlist, while
    # Rating 7 itself does not create Stage 2. A rare Stage-2 Rating-6 case must
    # be a documented human override rather than an automatic model shortcut.
    if "stage" in out.columns:
        watch = watch | out["stage"].eq("Stage 2")
    rating = pd.Series(np.where(watch, 7, rating), index=out.index, dtype=int)

    if "stage" in out.columns:
        npl = out["stage"].eq("Stage 3")
        dpd = out.get("days_past_due", pd.Series(0, index=out.index)).fillna(0)
        # Severity within NPL population only; no PD threshold can create Stage 3.
        # Rating 10 is an explicit write-off state, not a DPD bucket.
        write_off = out.get("write_off_flag", pd.Series(0, index=out.index)).fillna(0).astype(bool)
        npl_rating = np.select([write_off, dpd >= 120], [10, 9], default=8)
        rating = pd.Series(np.where(npl, npl_rating, rating), index=out.index, dtype=int)

    full_cash = pd.Series(False, index=out.index)
    if {"collateral_type", "recognized_collateral_coverage"}.issubset(out.columns):
        full_cash = (
            out["collateral_type"].eq("Cash")
            & out["recognized_collateral_coverage"].fillna(0).ge(.999)
        )
    # Rating 1 is reserved exclusively for full eligible cash coverage.
    # Security strength changes the internal rating but never cures an NPL.
    if "stage" in out.columns:
        full_cash &= out["stage"].eq("Stage 1")
    rating.loc[full_cash] = 1

    out["risk_rating"] = rating
    out["rating_status"] = np.select(
        [out["risk_rating"].le(6), out["risk_rating"].eq(7)],
        ["Performing", "Watchlist"],
        default="Non-performing",
    )
    return out
