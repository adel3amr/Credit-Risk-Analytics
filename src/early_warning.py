"""Early-warning / risk-direction layer for synthetic SME monitoring.

This module is intentionally separate from the core 12-month PD model. It uses
behavioural trajectory indicators to flag deterioration for monitoring and as a
simplified SICR input. Thresholds are transparent demonstration assumptions,
not empirically calibrated production triggers.
"""
import numpy as np


def add_early_warning_signals(df):
    out = df.copy()

    util_change = out["utilization_6m_change"].fillna(0.0)
    avg_util = out["avg_utilization_6m"].fillna(0.0)
    months_high = out["months_above_80_utilization"].fillna(0)
    breaches = out["limit_breach_count"].fillna(0)

    out["ews_rising_utilization"] = (util_change >= 0.10).astype(int)
    out["ews_persistent_high_utilization"] = (
        (avg_util >= 0.80) | (months_high >= 3)
    ).astype(int)
    out["ews_limit_breach"] = (breaches >= 1).astype(int)

    signal_cols = [
        "ews_rising_utilization",
        "ews_persistent_high_utilization",
        "ews_limit_breach",
    ]
    out["ews_signal_count"] = out[signal_cols].sum(axis=1)

    # Monitoring classification, not a PD/rating grade.
    out["risk_direction"] = np.select(
        [out["ews_signal_count"] >= 2, out["ews_signal_count"] == 1],
        ["Deteriorating", "Watch"],
        default="Stable",
    )
    out["ews_sicr_flag"] = (out["risk_direction"] == "Deteriorating").astype(int)
    return out
