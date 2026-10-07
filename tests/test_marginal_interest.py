"""Independent as-of, exposure, split, freeze and leakage controls for MI-1."""
import json
import numpy as np
import pandas as pd
import pytest
from marginal_interest.experiment import DATA, OUT, EXTRA, ledger_features, features, validate_x, verify_data, sha


def test_interest_uses_opening_principal_and_never_increases_ead():
    r=ledger_features(pd.DataFrame({'month':[1,2,3],'payment':[100.,200.,0.]}),3,1000.,.12)
    assert r['ead_at_default']==700
    assert r['marginal_interest_amount']==pytest.approx(26.)
    assert r['marginal_interest_to_ead']==pytest.approx(26/700)


def test_future_payments_cannot_change_observation_features():
    a=pd.DataFrame({'month':[1,2,3],'payment':[100.,200.,600.]})
    b=a.copy();b.loc[2,'payment']=np.nan
    assert ledger_features(a,2,1000.,.12)==ledger_features(b,2,1000.,.12)


@pytest.mark.parametrize('payments,months', [([-1.],[1]),([1001.],[1]),([0.,0.],[1,1]),([0.],[2]),([np.nan],[1])])
def test_invalid_ledger_fails(payments,months):
    with pytest.raises(ValueError): ledger_features(pd.DataFrame({'month':months,'payment':payments}),1,1000.,.1)


def test_frozen_data_and_disjoint_episodes():
    verify_data(); cohorts=[pd.read_csv(DATA/f'{s}_inputs.csv.gz') for s in ['development','validation','final']]
    for i,x in enumerate(cohorts):
        assert x.facility_id.is_unique
        assert (pd.to_datetime(x.default_date)<pd.to_datetime(x.reporting_date)).all()
        for y in cohorts[i+1:]:
            assert not set(x.customer_id)&set(y.customer_id)
            assert not set(x.facility_id)&set(y.facility_id)
        assert np.allclose(x.ead_at_default,x.default_principal*(1-x.cumulative_recovery_ratio),atol=1e-5)


def test_outcomes_and_latent_states_are_not_features():
    x=pd.read_csv(DATA/'development_inputs.csv.gz').head(20)
    for name in EXTRA:
        a=features(x,name)
        for col in ['actual','cure','resolved_at','security_quality','guarantor_strength','willingness','latent_regime']:
            x[col]=-999
        pd.testing.assert_frame_equal(a,features(x,name))
        assert not set(a)&{'actual','cure','resolved_at','security_quality','guarantor_strength','latent_regime'}


def test_date_and_missing_feature_fail_closed():
    x=pd.read_csv(DATA/'development_inputs.csv.gz').head(2)
    with pytest.raises(ValueError): validate_x(x.assign(default_date='2099-01-01'))
    with pytest.raises(ValueError): validate_x(x.assign(marginal_interest_amount=np.nan))
    with pytest.raises(ValueError): validate_x(x.drop(columns=['interest_rate']))


def test_saved_ledger_independently_reproduces_snapshot():
    x=pd.read_csv(DATA/'development_inputs.csv.gz').head(30)
    h=pd.read_csv(DATA/'development_ledger.csv.gz')
    for r in x.itertuples():
        g=h[h.facility_id==r.facility_id].sort_values('month')
        opening=r.default_principal-g.payment.cumsum().shift(fill_value=0)
        assert (pd.to_datetime(g.event_date)<=pd.Timestamp(r.reporting_date)).all()
        assert np.isclose((opening*r.interest_rate/12).sum(),r.marginal_interest_amount,rtol=1e-9)


def test_model_lock_integrity():
    lock=json.loads((OUT/'LOCK.json').read_text())
    assert lock['data_manifest_sha256']==sha(DATA/'manifest.json')
    for name,h in lock['models'].items(): assert sha(OUT/name)==h


def test_final_cashflow_target_independent_arithmetic():
    x=pd.read_csv(DATA/'final_inputs.csv.gz').set_index('facility_id')
    y=pd.read_csv(DATA/'final_outcomes.csv.gz')
    e=x.loc[y.facility_id,'ead_at_default'].to_numpy();r=x.loc[y.facility_id,'interest_rate'].to_numpy()
    discounted=sum(y[f'net_cf_{m}m'].to_numpy()/(1+r)**(m/12) for m in [1,6,12,24,36,60])
    np.testing.assert_allclose(np.clip(1-discounted/e,0,1),y.actual,atol=1e-9,rtol=0)
    assert (pd.to_datetime(y.resolved_at).to_numpy()>pd.to_datetime(x.loc[y.facility_id,'reporting_date']).to_numpy()).all()


def test_final_ecl_population_and_aggregation():
    p=pd.read_csv(OUT/'predictions.csv.gz');p=p[p.split=='final']
    choice=json.loads((OUT/'LOCK.json').read_text())['selected']
    a=p[p.model=='M0'].sort_values(['facility_id','scenario']);b=p[p.model==choice].sort_values(['facility_id','scenario'])
    for field in ['facility_id','customer_id','ead_at_default','stage','pd','scenario']:
        np.testing.assert_array_equal(a[field].to_numpy(),b[field].to_numpy())
    report=json.loads((OUT/'independent_ecl.json').read_text())
    for n,expected in [('M0',report['benchmark']),(choice,report['challenger'])]:
        z=p[p.model==n].copy(); z['ecl']=z.prediction*z.ead_at_default*z.scenario.map({'upside':.2,'baseline':.6,'downside':.2})
        assert abs(z.groupby('customer_id').ecl.sum().sum()-expected)<=1e-6
        assert z.stage.eq(3).all() and z.pd.eq(1).all()
