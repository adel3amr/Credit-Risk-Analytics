import numpy as np
import pandas as pd
import pytest
from synthetic_bank.generate import generate_cohort,recoveries
from research_diagnostics.s1_resolution.conditional import simulate,integrate,FEATURES
from research_diagnostics.s1_resolution.analyze import summarize,groups


def fixture():
    b,f,*_=generate_cohort('fixture',40,891,'2005-01-01')
    f=f.drop_duplicates('customer_id').reset_index(drop=True)
    b=b.set_index('customer_id').loc[f.customer_id].reset_index()
    b['default_date']='2005-06-01'
    f=f.merge(b[['customer_id','interest_rate']],on='customer_id',validate='one_to_one')
    return b,f


def test_s1_independent_recovery_equations_exact_replay():
    b,f=fixture()
    expected=recoveries(f,b,np.random.default_rng(921)).economic_lgd
    actual=simulate(f,np.random.default_rng(921),1)[:,0]
    np.testing.assert_allclose(actual,expected,atol=1e-14,rtol=0)


def test_s1_integration_no_future_information_and_repeatable():
    _,f=fixture()
    baseline=integrate(f[FEATURES],draws=32,seed=8)
    f['economic_lgd']=999; f['cure_flag']=999; f['workout_cost']=999
    for x,y in zip(baseline,integrate(f,draws=32,seed=8)):
        np.testing.assert_array_equal(x,y)
    assert ((baseline[0]>=0)&(baseline[0]<=1)).all()


def test_s1_decomposition_identity_and_exante_groups():
    _,f=fixture(); mu,var,se=integrate(f,draws=32,seed=8)
    p=np.clip(mu-.02,0,1); actual=np.clip(mu+.1,0,1)
    rows=summarize(f,p,mu,var,se,actual,'test','test')
    assert max(x.get('identity_error',0) for x in rows)<1e-12
    a=dict(groups(f,p,mu,actual)); b=dict(groups(f,p,mu,1-actual))
    for name in a:
        if not name.startswith('realized'):
            np.testing.assert_array_equal(a[name],b[name])
    assert 'realized_gt75' in a and 'conditional_gt75' in a


def test_s1_diagnostic_rejects_nonfinite():
    _,f=fixture(); f.loc[0,'interest_rate']=np.inf
    with pytest.raises(ValueError,match='Finite'):
        integrate(f,draws=32)
