import numpy as np
import pandas as pd

from lgd_research.generate_r2 import BUCKETS, DEPLOYABLE, generate
from lgd_research.run_study import LegacyCollateralProxy


def test_recovery_identity_and_prediction_time_separation():
    x = generate(700, 9821, "test")
    pv = sum(x[f"recovery_cf_{t}m"]/(1+x.discount_rate)**(t/12) for t in BUCKETS)
    assert np.allclose(x.pv_net_recovery, pv)
    assert np.allclose(x.economic_lgd, np.clip(1-pv/x.ead_at_default, 0, 1))
    assert x.facility_id.is_unique and not x[DEPLOYABLE].isna().any().any()
    assert (x.guarantee_coverage == 0).any() and (x.economic_lgd > .75).any()
    assert set(DEPLOYABLE).isdisjoint({"cure_flag", "workout_cost", "pv_net_recovery",
                                      "months_to_resolution", "economic_lgd"})


def test_stress_changes_realized_recovery_without_direct_target_assignment():
    ordinary = generate(1000, 441, "baseline")
    stressed = generate(1000, 441, "stress", "combined")
    assert stressed.economic_lgd.mean() > ordinary.economic_lgd.mean()
    assert (stressed.pv_net_recovery < ordinary.pv_net_recovery).mean() > .70
    assert stressed.workout_cost.mean() > ordinary.workout_cost.mean()


def test_original_proxy_transfer_preserves_legacy_collateral_recognition():
    sample = pd.DataFrame({'collateral_type':['Unsecured','Cash','Mortgage','Other'],
                           'collateral_coverage':[0.,1.,1.,1.],
                           'industry':['Services']*4})
    pred = LegacyCollateralProxy().fit(sample).predict(sample)
    assert np.allclose(pred,[.62,0.,.124,.217])
