import copy
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from credit_platform.common import ROOT,file_hash
from credit_platform.risk import policy
from economic_lgd.economics import history,validate,scenario_frame,MACRO
from economic_lgd.model import features,predict,FEATURES
from economic_lgd.recovery import simulate,BUCKETS
from economic_lgd.scenarios import ecl_components


def fixture():
    return pd.read_csv(ROOT/'economic_lgd/data/development_inputs.csv.gz').head(20)


def test_economic_history_deterministic_and_as_of():
    first=history(['Retail','Manufacturing'],'2000-01-01',123)
    pd.testing.assert_frame_equal(first,history(['Retail','Manufacturing'],'2000-01-01',123))
    validate(first)
    first.loc[0,'published_at']='2050-01-01'
    with pytest.raises(ValueError,match='unavailable'): validate(first)


def test_feature_contract_excludes_latent_future_and_quality():
    frame=fixture(); original=features(frame)
    frame['latent_regime']=99
    frame['downturn_at_default']=1
    frame['economic_lgd']=.999
    frame['security_quality']=0
    frame['guarantor_strength']=0
    pd.testing.assert_frame_equal(original,features(frame))
    assert set(MACRO)<=set(FEATURES)
    for prohibited in ['latent_regime','downturn_at_default','economic_lgd','resolved_at','security_quality','guarantor_strength']:
        assert prohibited not in FEATURES
    frame.loc[0,'liquidity']=np.nan
    with pytest.raises(ValueError): features(frame)


def test_recovery_cashflow_identity_bounds_and_latent_independence():
    frame=fixture()
    a,cf=simulate(frame,np.random.default_rng(81),8,cashflows=True)
    frame['latent_regime']=1-frame.latent_regime
    b=simulate(frame,np.random.default_rng(81),8)
    np.testing.assert_array_equal(a,b)
    pv=np.zeros_like(a)
    for j,m in enumerate(BUCKETS):
        pv+=cf[:,:,j]/(1+frame.interest_rate.to_numpy()[:,None])**(m/12)
    independent=np.minimum(1,np.maximum(0,1-pv/frame.ead_at_default.to_numpy()[:,None]))
    np.testing.assert_allclose(a,independent,atol=1e-12)
    assert ((a>=0)&(a<=1)).all()


def test_deterioration_recovery_direction_common_random_numbers():
    frame=fixture(); scenarios=policy()['scenarios']
    baseline=next(s for s in scenarios if s['scenario']=='baseline')
    sims={s['scenario']:simulate(scenario_frame(frame,s,baseline),np.random.default_rng(7),128)
          for s in scenarios}
    assert np.mean(sims['downside']-sims['baseline'])>0
    assert np.mean(sims['baseline']-sims['upside'])>0


@pytest.mark.parametrize('stage,expected',[
    ('Stage 1',100*(.2*.1*.3+.6*.2*.5+.2*.4*.8)),
    ('Stage 2',100*(.2*(1-.9**2)*.3+.6*(1-.8**2)*.5+.2*(1-.6**2)*.8)),
    ('Stage 3',100*(.2*.3+.6*.5+.2*.8))])
def test_scenario_ecl_independent_hand_calculation(stage,expected):
    scenarios=policy()['scenarios']
    rows=ecl_components(stage,100,24,dict(upside=.1,baseline=.2,downside=.4),
                         dict(upside=.3,baseline=.5,downside=.8),scenarios)
    assert sum(r['weighted_ecl'] for r in rows)==pytest.approx(expected)


def test_scenario_ecl_rejects_invalid_inputs():
    scenarios=policy()['scenarios']; p=dict(upside=.1,baseline=.2,downside=.4)
    for stage in ['Stage 0','',None]:
        with pytest.raises(ValueError): ecl_components(stage,100,12,p,p,scenarios)
    bad=copy.deepcopy(scenarios);bad[0]['weight']=-.1;bad[1]['weight']=.9
    with pytest.raises(ValueError): ecl_components('Stage 1',100,12,p,p,bad)
    with pytest.raises(ValueError): ecl_components('Stage 1',100,12,{},p,scenarios)


def test_frozen_separation_and_recovery_maturity():
    borrowers=[]
    for cohort in ['development','selection','final','current']:
        frame=pd.read_csv(ROOT/f'economic_lgd/data/{cohort}_inputs.csv.gz')
        validate(frame)
        ids=set(frame.customer_id)
        assert all(not(ids&previous) for previous in borrowers)
        borrowers.append(ids)
    for earlier,later in [('development','selection'),('selection','final')]:
        targets=pd.read_csv(ROOT/f'economic_lgd/data/{earlier}_outcomes.csv.gz')
        inputs=pd.read_csv(ROOT/f'economic_lgd/data/{later}_inputs.csv.gz')
        assert targets.resolved_at.max()<inputs.reporting_date.min()


def test_frozen_candidate_hash_and_train_score_parity():
    folder=ROOT/'economic_lgd/results'
    lock=json.loads((folder/'LOCK.json').read_text())
    assert file_hash(folder/'model.joblib')==lock['model_hash']
    model=joblib.load(folder/'model.joblib')
    frame=fixture()
    assert list(model.feature_names_in_)==FEATURES
    p=predict(model,frame)
    assert ((p>=0)&(p<=1)).all()
    changed=frame.copy(); changed['latent_regime']=100
    np.testing.assert_array_equal(p,predict(model,changed))
