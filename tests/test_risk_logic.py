import numpy as np
import pandas as pd
import pytest

from src.scorecard import pd_to_score, add_risk_rating
from src.ecl import calculate_ecl
from src.governance import has_permission


def test_pd_to_score_is_strictly_decreasing_in_pd():
    p = np.array([0.001, 0.005, 0.01, 0.03, 0.08, 0.20])
    scores = pd_to_score(p)
    assert np.all(np.diff(scores) < 0)


def test_all_documented_risk_ratings_are_reachable():
    df = pd.DataFrame({
        "predicted_pd": [0.002, 0.007, 0.015, 0.03, 0.10, 0.02, 0.02, 0.02, 0.02, 0.002],
        "stage": ["Stage 1"] * 7 + ["Stage 3"] * 3,
        "days_past_due": [0, 0, 0, 0, 0, 0, 0, 90, 120, 180],
        "ews_monitoring_flag": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        "collateral_type": ["Mortgage"] * 6 + ["Cash"] + ["Unsecured"] * 3,
        "recognized_collateral_coverage": [0.5] * 6 + [1.0] + [0.0] * 3,
    })
    out = add_risk_rating(df)
    assert set(out["risk_rating"]) == set(range(1, 11))


def _base_ecl_row(**overrides):
    row = {
        "predicted_pd": 0.05,
        "lgd": 0.50,
        "ead": 100_000.0,
        "loan_ead": 100_000.0,
        "ovd_ead": 0.0,
        "trade_ead": 0.0,
        "loan_remaining_months": 24,
        "ovd_remaining_months": 0,
        "trade_remaining_months": 0,
        "recognized_collateral": 0.0,
        "unsecured_ead": 100_000.0,
        "unsecured_lgd": 0.50,
        "utilization_6m_change": 0.0,
        "avg_utilization_6m": 0.50,
        "months_above_80_utilization": 0,
        "limit_breach_count": 0,
        "days_past_due": 30,
        "current_credit_impaired": 0,
        "delinquencies_12m": 0,
        "previous_defaults": 0,
        "credit_utilization": 0.50,
        "consecutive_ews_months": 0,
    }
    row.update(overrides)
    return row


def test_stage2_full_lifetime_ecl_is_not_below_12m_ecl():
    out = calculate_ecl(pd.DataFrame([_base_ecl_row()]))
    assert out.loc[0, "stage"] == "Stage 2"
    assert out.loc[0, "full_lifetime_ecl"] >= out.loc[0, "ecl_12m"]
    assert out.loc[0, "ecl"] == pytest.approx(out.loc[0, "full_lifetime_ecl"])


def test_unsecured_stage3_uses_unsecured_loss_severity_not_100pct_loss():
    out = calculate_ecl(pd.DataFrame([_base_ecl_row(
        days_past_due=90,
        current_credit_impaired=1,
        unsecured_lgd=0.62,
        lgd=0.62,
    )]))
    assert out.loc[0, "stage"] == "Stage 3"
    assert out.loc[0, "ecl"] == pytest.approx(62_000.0)
    assert out.loc[0, "ecl"] < out.loc[0, "ead"]


def test_duplicate_role_index_fails_closed():
    roles = pd.DataFrame(
        {"propose_override": [1, 1]},
        index=pd.Index(["Credit Analyst", "Credit Analyst"], name="role"),
    )
    assert not has_permission("Credit Analyst", "propose_override", roles=roles)


def test_null_pd_is_rejected_for_rating():
    df = pd.DataFrame({
        "predicted_pd": [np.nan],
        "stage": ["Stage 1"],
        "days_past_due": [0],
        "ews_monitoring_flag": [0],
        "collateral_type": ["Unsecured"],
        "recognized_collateral_coverage": [0.0],
    })
    with pytest.raises(ValueError):
        add_risk_rating(df)
