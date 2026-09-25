import numpy as np
import pandas as pd
import pytest
from research_diagnostics.downturn_resolution.calibration import RegimeCalibration,scenario_control
from research_diagnostics.downturn_resolution.mechanisms import simulate as switched
from research_diagnostics.s1_resolution.conditional import simulate as original
from synthetic_bank.generate import generate_cohort


def calibrated():
    base=np.linspace(.02,.98,200); c=np.array(['Cash','Mortgage','Other','Unsecured']*50)
    state=np.arange(200)%2; y=np.clip(base+.1*state-.03,0,1)
    return RegimeCalibration().fit(base,c,state,y),base,c


def test_regime_calibration_bounded_reproducible_mixture():
    fit,b,c=calibrated(); other,_,_=calibrated()
    np.testing.assert_allclose(fit.coefficients,other.coefficients,rtol=0,atol=0)
    normal=fit.predict(b,c,np.zeros(len(b))); adverse=fit.predict(b,c,np.ones(len(b)))
    mixture=fit.mixture(b,c,np.full(len(b),.3))
    np.testing.assert_allclose(mixture,.7*normal+.3*adverse)
    assert ((mixture>=0)&(mixture<=1)).all()


@pytest.mark.parametrize('purpose',['expected_loss','booking','production'])
def test_oracle_or_scenario_cannot_be_booked(purpose):
    fit,b,c=calibrated()
    with pytest.raises(ValueError,match='Not approved'):
        scenario_control(fit,b,c,np.ones(len(b)),np.ones(len(b)),scenario='downturn',source='test',run_id='test',purpose=purpose)


def test_control_preserves_originals_and_reconciles():
    fit,b,c=calibrated(); saved=b.copy()
    out=scenario_control(fit,b,c,np.full(len(b),.2),np.full(len(b),100),scenario='downturn',source='declared',run_id='test')
    np.testing.assert_array_equal(b,saved)
    np.testing.assert_allclose(out['base_ecl'],20*b)
    np.testing.assert_allclose(out['scenario_ecl'],20*np.array(out['scenario_lgd']))
    assert np.min(out['incremental_sensitivity'])>=0


@pytest.mark.parametrize('bad',[np.nan,np.inf,-.1,1.1])
def test_invalid_probability_rejected(bad):
    fit,b,c=calibrated()
    with pytest.raises(ValueError): fit.mixture(b,c,np.full(len(b),bad))


def test_mechanism_switches_match_frozen_equations():
    b,f,*_=generate_cohort('test',40,891,'2005-01-01')
    f=f.merge(b[['customer_id','interest_rate']],on='customer_id')
    actual=switched(f,np.random.default_rng(1),32)
    expected=original(f,np.random.default_rng(1),32)
    np.testing.assert_array_equal(actual,expected)
    zero=f.copy();zero['downturn_at_default']=0
    np.testing.assert_array_equal(switched(f,np.random.default_rng(1),32,enabled=[]),original(zero,np.random.default_rng(1),32))


def test_explicit_scenario_required():
    fit,b,c=calibrated()
    with pytest.raises(ValueError,match='Explicit'):
        scenario_control(fit,b,c,np.ones(len(b)),np.ones(len(b)),scenario='automatic',source='test',run_id='test')
