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
