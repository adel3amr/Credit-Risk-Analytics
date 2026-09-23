import numpy as np
import pandas as pd
import pytest

from src.scorecard import pd_to_score, add_risk_rating
from src.ecl import calculate_ecl
from src.governance import has_permission


def test_pd_to_score_is_strictly_decreasing_in_pd():
    p = np.array([0.001, 0.005, 0.01, 0.03, 0.08, 0.20])
    assert np.all(np.diff(pd_to_score(p)) < 0)


def _base_ecl_row(**overrides):
    row = {
        "predicted_pd": 0.05,
        "lgd": 0.50,
        "ead": 100_000.0,
        "recognized_collateral": 20_000.0,
        "loan_term_months": 24,
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


def test_stage2_ecl_is_at_least_12m_for_two_year_term():
    out = calculate_ecl(pd.DataFrame([_base_ecl_row()]))
    assert out.loc[0, "stage"] == "Stage 2"
    assert out.loc[0, "ecl"] >= out.loc[0, "ecl_12m"]


def test_stage3_matches_existing_discounted_recovery_policy():
    out = calculate_ecl(pd.DataFrame([_base_ecl_row(
        days_past_due=90,
        current_credit_impaired=1,
    )]))
    discounted_recovery = 20_000 * (1 - 0.10) / ((1 + 0.05) ** 2)
    expected = 100_000 - discounted_recovery
    assert out.loc[0, "stage"] == "Stage 3"
    assert out.loc[0, "ecl"] == pytest.approx(expected)


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
        "risk_direction": ["Stable"],
        "collateral_type": ["Unsecured"],
        "recognized_collateral_coverage": [0.0],
    })
    with pytest.raises(ValueError):
        add_risk_rating(df)


def test_stage2_defaults_to_rating7_without_forcing_stage():
    df = pd.DataFrame({
        "predicted_pd": [0.03, 0.03],
        "stage": ["Stage 2", "Stage 1"],
        "days_past_due": [0, 0],
        "write_off_flag": [0, 0],
        "ews_monitoring_flag": [0, 0],
        "risk_direction": ["Stable", "Stable"],
        "collateral_type": ["Unsecured", "Unsecured"],
        "recognized_collateral_coverage": [0.0, 0.0],
    })
    out = add_risk_rating(df)
    assert out.loc[0, "risk_rating"] == 7
    assert out.loc[1, "risk_rating"] != 7


def test_rating10_requires_explicit_writeoff():
    df = pd.DataFrame({
        "predicted_pd": [0.20, 0.20],
        "stage": ["Stage 3", "Stage 3"],
        "days_past_due": [120, 120],
        "write_off_flag": [0, 1],
        "ews_monitoring_flag": [0, 0],
        "risk_direction": ["Deteriorating", "Deteriorating"],
        "collateral_type": ["Unsecured", "Unsecured"],
        "recognized_collateral_coverage": [0.0, 0.0],
    })
    out = add_risk_rating(df)
    assert out.loc[0, "risk_rating"] == 9
    assert out.loc[1, "risk_rating"] == 10
