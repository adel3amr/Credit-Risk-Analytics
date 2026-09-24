import numpy as np
import pandas as pd
import pytest
from synthetic_bank.generate import generate_cohort, canonical
from synthetic_bank.validate import validate_cohort


def test_s1_reproduction_lineage_and_cashflow_identity():
    a=generate_cohort('test',250,77,'2005-01-01')
    b=generate_cohort('test',250,77,'2005-01-01')
    for left,right in zip(a,b):
        pd.testing.assert_frame_equal(left,right)
    result=validate_cohort(*a)
    assert result['workouts']>0
    assert 0<result['zero_guarantee_share']<1
    contract=canonical(a[0],a[1],'test','2005-01-01')
    assert len(contract.facilities)==len(a[1])


def test_s1_current_has_no_future_targets():
    b,f,h,t,w=generate_cohort('current',30,88,'2026-01-01')
    assert t.empty and w.empty
    assert not {'default','pd_true','lgd'} & set(b)
    assert not {'cure_flag','economic_lgd'} & set(f)
    assert (f.loc[f.guarantee_coverage.eq(0),'guarantor_strength']==0).all()


def test_s1_cashflow_corruption_detected():
    tables=list(generate_cohort('test',250,77,'2005-01-01'))
    tables[-1].loc[0,'recovery_cf_12m']+=100
    with pytest.raises(AssertionError):
        validate_cohort(*tables)
