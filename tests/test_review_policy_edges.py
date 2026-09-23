"""Independent policy-boundary cases; model methodology is not altered."""
import numpy as np
import pandas as pd
import pytest

from src.ecl import assign_stage
from src.facility_ecl import calculate_facility_ecl, aggregate_facility_ecl
from src.lgd_model import portfolio_to_facilities
from src.scorecard import add_risk_rating


def row(**changes):
    baseline = dict(predicted_pd=.02, days_past_due=0, current_credit_impaired=0,
                    delinquencies_12m=0, previous_defaults=0, credit_utilization=.50,
                    utilization_6m_change=0., avg_utilization_6m=.50,
                    months_above_80_utilization=0, limit_breach_count=0,
                    consecutive_ews_months=0, collateral_type='Unsecured',
                    recognized_collateral_coverage=0., write_off_flag=0)
    return {**baseline, **changes}


@pytest.mark.parametrize('changes,expected_stage,expected_direction', [
    ({}, 'Stage 1', 'Stable'),
    ({'days_past_due':29}, 'Stage 1', 'Stable'),
    ({'days_past_due':30}, 'Stage 2', 'Stable'),
    ({'days_past_due':89}, 'Stage 2', 'Stable'),
    ({'days_past_due':90}, 'Stage 3', 'Stable'),
    ({'current_credit_impaired':1}, 'Stage 3', 'Stable'),
    ({'utilization_6m_change':.11,'avg_utilization_6m':.83,
      'consecutive_ews_months':8}, 'Stage 1', 'Deteriorating'),
    ({'utilization_6m_change':.11,'avg_utilization_6m':.83,
      'consecutive_ews_months':9}, 'Stage 2', 'Deteriorating'),
    ({'utilization_6m_change':.11,'avg_utilization_6m':.83,
      'consecutive_ews_months':9,'current_credit_impaired':1}, 'Stage 3', 'Deteriorating'),
    ({'delinquencies_12m':2}, 'Stage 2', 'Stable'),
    ({'previous_defaults':1,'predicted_pd':.05}, 'Stage 2', 'Stable'),
    ({'credit_utilization':.85,'days_past_due':1}, 'Stage 2', 'Stable'),
])
def test_source_policy_boundaries(changes, expected_stage, expected_direction):
    got=assign_stage(pd.DataFrame([row(**changes)])).iloc[0]
    assert (got.stage, got.risk_direction)==(expected_stage,expected_direction)


def test_reporting_date_stage_migration_and_separate_watchlist():
    # Four hypothetical reporting dates of one borrower; the application has
    # no stateful migration engine. This tests assignments at each date.
    dates=[row(),row(utilization_6m_change=.11,avg_utilization_6m=.83,
                     consecutive_ews_months=8),
           row(utilization_6m_change=.11,avg_utilization_6m=.83,
               consecutive_ews_months=9),
           row(),row(days_past_due=30),row(current_credit_impaired=1)]
    frame=assign_stage(pd.DataFrame(dates))
    rated=add_risk_rating(frame)
    assert frame.stage.tolist()==['Stage 1','Stage 1','Stage 2','Stage 1','Stage 2','Stage 3']
    assert rated.loc[1,'risk_rating']==7  # monitoring watch, still Stage 1
    assert rated.loc[2,'risk_rating']==7
    assert rated.loc[3,'risk_rating']!=7  # source rules permit exit
    assert rated.loc[5,'risk_rating']>=8


@pytest.mark.parametrize('stage,pd12,lgd,ead,months,expected', [
    ('Stage 1',.10,.50,100.,12,5.),
    ('Stage 2',.10,.50,100.,24,9.5),
    ('Stage 2',.10,.50,100.,6,50*(1-np.sqrt(.90))),
    ('Stage 3',.10,.50,100.,24,50.),
    ('Stage 1',.10,.50,0.,12,0.),
    ('Stage 1',0.,1.,100.,12,0.),
    ('Stage 1',1.,1.,100.,12,100.),
    ('Stage 3',.10,0.,100.,12,0.),
])
def test_stage_specific_ecl_numeric_oracle(stage,pd12,lgd,ead,months,expected):
    b=pd.DataFrame([dict(customer_id='X',stage=stage,forward_looking_pd_12m=pd12)])
    f=pd.DataFrame([dict(customer_id='X',facility_id='X1',predicted_lgd=lgd,
                         ead_at_default=ead,remaining_months=months)])
    result=calculate_facility_ecl(b,f)
    assert result.facility_ecl.iloc[0]==pytest.approx(expected)


def test_product_ead_mapping_and_borrower_aggregation():
    b=pd.DataFrame([dict(customer_id='X',industry='Services',collateral_type='Mortgage',
                         collateral_coverage=.8,leverage_ratio=2,current_ratio=1.2,
                         management_quality=3,loan_ead=100.,ovd_ead=50.,trade_type='Import LC',
                         trade_ead=20.,loan_remaining_months=24,ovd_remaining_months=12,
                         trade_remaining_months=6)])
    f=portfolio_to_facilities(b)
    assert dict(zip(f.product_type,f.ead_at_default))=={'Term Loan':100.,'OVD':50.,'Import LC':20.}
    assert f.guarantee_coverage.tolist()==[0.,0.,.20]
    assert f.lien_rank.tolist()==['First','Second','Second']
    f['predicted_lgd']=[.2,.4,.6]
    base=pd.DataFrame([dict(customer_id='X',stage='Stage 2',forward_looking_pd_12m=.10)])
    got=calculate_facility_ecl(base,f)
    agg=aggregate_facility_ecl(got).iloc[0]
    expected=100*.2*.19+50*.4*.10+20*.6*(1-np.sqrt(.9))
    assert agg.facility_ead==pytest.approx(170.)
    assert agg.ecl_facility==pytest.approx(expected)
