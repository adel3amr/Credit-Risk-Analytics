"""Failure modes which could otherwise silently misstate ECL or classification."""
import numpy as np
import pandas as pd
import pytest
from src.facility_ecl import calculate_facility_ecl
from src.ecl import assign_stage
from src.lgd_model import gradient_boosting_lgd_model, predict_lgd
from test_risk_logic import _base_ecl_row


def inputs():
    b = pd.DataFrame({'customer_id': ['A'], 'stage': ['Stage 1'], 'forward_looking_pd_12m': [.1]})
    f = pd.DataFrame({'customer_id': ['A'], 'facility_id': ['A1'], 'ead_at_default': [100.],
                      'predicted_lgd': [.5], 'remaining_months': [12.]})
    return b, f


@pytest.mark.parametrize('bad_stage', ['Stage 4', '', None])
def test_invalid_stage_cannot_silently_get_stage1_ecl(bad_stage):
    b, f = inputs()
    b['stage'] = bad_stage
    with pytest.raises(ValueError, match='stage'):
        calculate_facility_ecl(b, f)


@pytest.mark.parametrize('column,bad_value', [('predicted_lgd', np.nan), ('predicted_lgd', 1.1),
    ('ead_at_default', np.inf), ('ead_at_default', -1), ('remaining_months', -1)])
def test_invalid_facility_values_are_rejected(column, bad_value):
    b, f = inputs()
    f[column] = bad_value
    with pytest.raises(ValueError):
        calculate_facility_ecl(b, f)


def test_orphan_and_duplicate_facilities_rejected():
    b, f = inputs()
    with pytest.raises(ValueError):
        calculate_facility_ecl(b, pd.concat([f, f]))
    f['customer_id'] = 'MISSING'
    with pytest.raises(ValueError):
        calculate_facility_ecl(b, f)


def test_existing_missing_maturity_default_and_zero_exposure():
    b, f = inputs()
    f['remaining_months'] = np.nan
    assert calculate_facility_ecl(b, f).facility_ecl.iloc[0] == pytest.approx(5)
    f['ead_at_default'] = 0
    assert calculate_facility_ecl(b, f).facility_ecl.iloc[0] == 0


def test_9_month_policy_boundary_and_stage3_precedence():
    rows = [_base_ecl_row(days_past_due=0, utilization_6m_change=.15,
                         avg_utilization_6m=.85, consecutive_ews_months=m) for m in [8, 9]]
    rows.append({**rows[-1], 'current_credit_impaired': 1})
    rows.append({**rows[-2], 'utilization_6m_change': 0, 'avg_utilization_6m': .5})
    assert assign_stage(pd.DataFrame(rows)).stage.tolist() == ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 1']


def test_lgd_outcomes_cannot_leak_through_extra_columns():
    # A tiny synthetic edge-case dataset exercises the unchanged preprocessors.
    frame = pd.DataFrame({
        'ead_at_default': [100.] * 60, 'collateral_coverage': [0., 1.] * 30,
        'guarantee_coverage': [0.] * 60, 'leverage_at_default': [2.] * 60,
        'current_ratio_at_default': [1.] * 60, 'management_quality': [3.] * 60,
        'product_type': ['Term Loan'] * 60, 'industry': ['Services'] * 60,
        'collateral_type': ['Unsecured', 'Cash'] * 30, 'lien_rank': ['Unsecured', 'First'] * 30,
    })
    model = gradient_boosting_lgd_model().fit(frame, [.95, .01] * 30)
    expected = predict_lgd(model, frame)
    frame['economic_lgd'] = 1000
    frame['cure_flag'] = 1
    np.testing.assert_array_equal(expected, predict_lgd(model, frame))
    frame.loc[0, 'leverage_at_default'] = np.nan
    frame.loc[1, 'industry'] = 'Unseen industry'
    assert np.isfinite(predict_lgd(model, frame)).all()
