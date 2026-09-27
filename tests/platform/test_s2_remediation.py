"""Independent controls for the focused successor; original tests stay unchanged."""
import json
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
import pytest
from credit_platform.common import ROOT,file_hash
from credit_platform.risk import policy
from economic_lgd.economics import scenario_frame
from economic_lgd.recovery import simulate,BUCKETS
from s2_remediation.model import features,predict,FEATURES,SIGNS
from s2_remediation.support import UnsupportedDomain
from s2_remediation.generate import history


@lru_cache
def artifacts():
    directory=ROOT/'s2_remediation/results'
    return (joblib.load(directory/'model.joblib'),joblib.load(directory/'support.joblib'))


def sample():
    return pd.read_csv(ROOT/'economic_lgd/data/current_inputs.csv.gz').head(30)


class FixedDraws:
    """Deterministic workout: no shocks, no cure, zero extra delay."""
    def normal(self,loc,scale,size): return np.full(size,loc,dtype=float)
    def gamma(self,shape,scale,size): return np.zeros(size)
    def integers(self,low,high,size): return np.full(size,low)
    def random(self,size): return np.ones(size)


@pytest.mark.parametrize('guarantee',[0,.35,1])
def test_independent_guarantee_waterfall_and_cashflows(guarantee):
    f=sample().iloc[:1].copy()
    for key,value in dict(ead_at_default=100,interest_rate=.05,collateral_type='Unsecured',
        collateral_coverage=0,lien_rank='First',guarantee_coverage=guarantee,
        guarantor_strength=.6,leverage_at_default=2.8,current_ratio_at_default=1,
        management_quality=3,output_growth_pct=2,unemployment_pct=5.5,
        liquidity=.8,collateral_change_pct=0).items(): f[key]=value
    lgd,cf=simulate(f,FixedDraws(),cashflows=True)
    eligible_guarantee=min(100,100*guarantee*.64)
    unsecured=(100-eligible_guarantee)*.30
    gross=eligible_guarantee+unsecured
    weights=np.exp(-np.abs(BUCKETS-17)/9); weights/=weights.sum()
    expected=gross*weights; expected[2]-=1.2
    np.testing.assert_allclose(cf[0,0],expected,atol=1e-12)
    expected_lgd=1-sum(expected/(1.05**(BUCKETS/12)))/100
    assert lgd[0,0]==pytest.approx(expected_lgd)
    assert gross<=100


def test_collateral_guarantee_no_double_counting():
    f=sample().iloc[:1].copy()
    for key,value in dict(ead_at_default=100,interest_rate=.05,collateral_type='Cash',
        collateral_coverage=10,lien_rank='First',guarantee_coverage=1,security_quality=1,
        output_growth_pct=2,unemployment_pct=5.5,liquidity=.8).items(): f[key]=value
    _,cf=simulate(f,FixedDraws(),cashflows=True)
    assert cf.sum()==pytest.approx(98.8)  # full 100 recovery minus 1.2 cost, never 200
    f['guarantee_coverage']=0
    _,without=simulate(f,FixedDraws(),cashflows=True)
    np.testing.assert_array_equal(cf,without)


def test_guarantee_continuity_and_direction():
    f=sample()
    values=[]
    for coverage in [0,1e-7,.35,.8,1-1e-7,1]:
        changed=f.assign(guarantee_coverage=coverage)
        values.append(simulate(changed,np.random.default_rng(5),32))
    for left,right in zip(values[:-1],values[1:]): assert (right<=left+1e-12).all()
    assert np.max(np.abs(values[0]-values[1]))<1e-6
    assert np.max(np.abs(values[-1]-values[-2]))<1e-6
    model,_=artifacts()
    p1=predict(model,f.assign(guarantee_coverage=1-1e-7))
    p2=predict(model,f.assign(guarantee_coverage=1))
    np.testing.assert_allclose(p1,p2,atol=1e-10)


def test_structural_scenario_order_and_bounds():
    model,_=artifacts(); f=sample()
    baseline=next(s for s in policy()['scenarios'] if s['scenario']=='baseline')
    results={s['scenario']:predict(model,scenario_frame(f,s,baseline)) for s in policy()['scenarios']}
    assert (results['upside']<=results['baseline']+1e-12).all()
    assert (results['baseline']<=results['downside']+1e-12).all()
    assert all(((p>=0)&(p<=1)).all() for p in results.values())
    # Each raw economic coordinate has the constrained sign, not just the one
    # three-scenario combination used by the presentation.
    for field,sign in SIGNS.items():
        changed=f.copy()
        if field=='guarantee_coverage': changed[field]=np.minimum(1,changed[field]+.01)
        elif field=='liquidity': changed[field]=np.minimum(1,changed[field]+.01)
        else: changed[field]+=.01
        assert (sign*(predict(model,changed)-predict(model,f))>=-1e-12).all()


def test_hidden_outcome_exclusion_and_feature_parity():
    model,_=artifacts(); f=sample(); baseline=predict(model,f)
    for col in ['latent_regime','security_quality','guarantor_strength','economic_lgd','resolved_at','downturn_at_default']:
        f[col]=999
        assert col not in FEATURES
    np.testing.assert_array_equal(baseline,predict(model,f))
    assert list(model.feature_names_in_)==FEATURES
    f.loc[0,'published_at']='2100-01-01'
    with pytest.raises(ValueError,match='unavailable'): features(f)


def test_support_blocks_extreme_and_crossed_economic_inputs():
    _,support=artifacts(); f=sample()
    outside=f.assign(output_growth_pct=-9.9,unemployment_pct=19.9,liquidity=.051)
    with pytest.raises(UnsupportedDomain): support.require(outside)
    # Values inside each marginal range can still have no joint recovery support.
    crossed=f.assign(output_growth_pct=support.high.output_growth_pct-.01,
        unemployment_pct=support.high.unemployment_pct-.01,
        collateral_change_pct=support.low.collateral_change_pct+.01,
        liquidity=support.low.liquidity+.01)
    report=support.inspect(crossed)
    assert not report.outside_macro_range.any()
    assert not report.supported.any()
    with pytest.raises(UnsupportedDomain): support.require(crossed)


def test_cycle_coverage_determinism_and_asof():
    h=history(['Retail','Manufacturing'],'2000-01-01',12,100)
    pd.testing.assert_frame_equal(h,history(['Retail','Manufacturing'],'2000-01-01',12,100))
    assert set(h.cycle_phase)=={'expansion','normal','deterioration','recession','recovery'}
    assert set(h.latent_regime)=={0,1}
    assert (h.economic_period<=h.published_at).all()
    assert (h.published_at<=h.reporting_date).all()


def test_new_holdout_separation_and_maturity():
    path=ROOT/'s2_remediation/data'
    frames={c:pd.read_csv(path/f'{c}_inputs.csv.gz') for c in ['development','calibration','promotion']}
    for a,b in [('development','calibration'),('calibration','promotion'),('development','promotion')]:
        assert not set(frames[a].customer_id)&set(frames[b].customer_id)
    old=pd.read_csv(ROOT/'economic_lgd/data/final_inputs.csv.gz')
    assert not set(frames['promotion'].customer_id)&set(old.customer_id)
    for a,b in [('development','calibration'),('calibration','promotion')]:
        y=pd.read_csv(path/f'{a}_outcomes.csv.gz')
        assert y.resolved_at.max()<frames[b].reporting_date.min()


def test_frozen_artifacts_and_reproducible_prediction():
    from s2_remediation.evaluate import verify,verify_lock
    verify(); lock=verify_lock()
    assert lock['status']=='FROZEN BEFORE PROMOTION; NO RETUNING'
    model,_=artifacts(); f=sample()
    np.testing.assert_array_equal(predict(model,f),predict(model,f))
    for path,h in lock['hashes'].items(): assert file_hash(ROOT/path)==h


def test_final_calculations_reconcile_independently():
    out=ROOT/'s2_remediation/results'
    if not (out/'FINAL_OPENED.json').exists(): pytest.skip('Final not yet opened')
    rows=pd.read_csv(out/'scenario_ecl.csv')
    expected=sum(s['weight']*rows['ecl_'+s['scenario']] for s in policy()['scenarios'])
    np.testing.assert_allclose(rows.corrected_ecl,expected,atol=1e-7,rtol=0)
    assert abs(rows.groupby('borrower_id').corrected_ecl.sum().sum()-rows.corrected_ecl.sum())<1e-6
    predictions=pd.read_csv(out/'current_predictions.csv')
    metrics=pd.read_csv(out/'current_metrics.csv')
    for scenario,g in predictions.groupby('scenario'):
        row=metrics[(metrics.scenario==scenario)&(metrics.model=='corrected')&(metrics.group=='all')].iloc[0]
        assert row.conditional_bias==pytest.approx((g.corrected-g.conditional_mean).mean())
