import json
import numpy as np
import pandas as pd
import pytest
from credit_platform.common import ROOT,file_hash
from credit_platform.risk import policy
from lgd_hardening.calibration import fit,predict
from lgd_hardening.capture import RecoveryEvidence,require_validated_derivation
from lgd_hardening.domain import scenario_inputs,assess
from lgd_hardening.release import require_promotion


def sample():return pd.read_csv(ROOT/'economic_lgd/data/current_inputs.csv.gz').head(3)


def test_calibration_reproduced_only_from_matured_calibration_data():
    path=ROOT/'s2_remediation/results/calibration_predictions.csv'
    data=pd.read_csv(path).query("scenario=='baseline'")
    saved=json.loads((ROOT/'lgd_hardening/results/calibration.json').read_text())
    rebuilt=fit(data.corrected,data.actual)
    assert saved['fit_source_sha256']==file_hash(path)
    assert saved['x']==rebuilt['x'] and saved['y']==rebuilt['y']
    assert saved['minimum_bin_n']==300
    assert saved['excluded_fit_sources']==['current','promotion','conditional_mean','hidden qualities']


def test_calibration_is_continuous_monotone_not_sorted_per_scenario():
    saved=json.loads((ROOT/'lgd_hardening/results/calibration.json').read_text())
    x=np.linspace(0,1,10001);y=predict(saved,x)
    assert (np.diff(y)>=-1e-12).all() and ((y>=0)&(y<=1)).all()
    for knot in saved['x']:
        assert abs(predict(saved,[knot-1e-8])[0]-predict(saved,[knot+1e-8])[0])<1e-5
    with pytest.raises(ValueError):predict(saved,[float('nan')])


def test_domain_exposes_scenario_outside_bounds_without_clipping():
    f=sample().assign(output_growth_pct=-9.9,liquidity=.051)
    scenarios=policy()['scenarios'];base=next(s for s in scenarios if s['scenario']=='baseline')
    down=next(s for s in scenarios if s['scenario']=='downside')
    out,invalid=scenario_inputs(f,down,base)
    assert invalid.all()
    assert (out.output_growth_pct<-10).all()
    pd.testing.assert_series_equal(f.output_growth_pct,pd.Series([-9.9]*3,name='output_growth_pct'))


def test_ood_bound_is_not_an_expected_lgd():
    class Reject:
        def inspect(self,frame):return pd.DataFrame({'supported':[False]*len(frame)})
    result=assess(sample(),Reject(),policy()['scenarios'])
    assert not result.supported.any()
    assert result.expected_lgd.isna().all()
    assert result.sensitivity_lgd_upper.eq(1).all()
    assert result.bound_status.eq('NONBOOKABLE_BOUND_NOT_EXPECTED_LGD').all()


def evidence(**changes):
    data=dict(facility_id='F1',reporting_date='2026-01-01',recorded_at='2025-12-01',
        effective_date='2025-11-01',source_record_id='R1',source_system='registry',
        evidence_reference='legal/1',evidence_kind='GUARANTEE',nominal_amount=100,
        eligible_amount=80,currency='EUR',provider_or_asset_id='G1',
        enforceability_status='CONFIRMED',legal_review_reference='legal/1',
        valuation_or_financial_date='2025-10-01',valuation_or_financial_reference='accounts/1')
    return {**data,**changes}


@pytest.mark.parametrize('changes',[
    {'recorded_at':'2027-01-01'}, {'eligible_amount':101},
    {'enforceability_status':'UNCONFIRMED'}, {'expiry_date':'2025-12-01'},
    {'guarantor_strength':.8}, {'security_quality':.8}, {'legal_review_reference':' '}])
def test_capture_rejects_future_hidden_or_ineligible_support(changes):
    with pytest.raises(ValueError):RecoveryEvidence(**evidence(**changes))


def test_capture_does_not_invent_a_validated_feature_derivation():
    record=RecoveryEvidence(**evidence())
    with pytest.raises(ValueError,match='independently validated'):
        require_validated_derivation([record],set())
    with pytest.raises(ValueError,match='missing'):require_validated_derivation([],set())


def test_status_string_cannot_override_failed_promotion_gates(tmp_path):
    decision={'model_version':'test','status':'CHALLENGER_NOT_PROMOTED','gates':{'model_support':False}}
    d=tmp_path/'decision.json';d.write_text(json.dumps(decision))
    registry={'model_id':'test','status':'PROMOTED_SYNTHETIC_REFERENCE','decision_sha256':file_hash(d)}
    (tmp_path/'registry.json').write_text(json.dumps(registry))
    with pytest.raises(ValueError,match='not been promoted'):require_promotion(tmp_path)
    decision['status']='PROMOTED_SYNTHETIC_REFERENCE';d.write_text(json.dumps(decision))
    registry['decision_sha256']=file_hash(d);(tmp_path/'registry.json').write_text(json.dumps(registry))
    with pytest.raises(ValueError,match='incomplete or failed'):require_promotion(tmp_path)


def test_controlled_runtime_keeps_unpromoted_model_blocked():
    from lgd_hardening.runtime import score
    with pytest.raises(ValueError,match='not been promoted'):score(sample())


def test_old_holdouts_explicitly_remain_known_engineering_evidence():
    audit=json.loads((ROOT/'lgd_hardening/results/baseline_audit.json').read_text())
    trial=json.loads((ROOT/'lgd_hardening/results/calibration_engineering.json').read_text())
    assert audit['final_holdout_generated'] is False
    assert audit['final_holdout_opened'] is False
    assert trial['new_final_holdout_used'] is False
    metrics=pd.read_csv(ROOT/'lgd_hardening/results/calibration_engineering_metrics.csv')
    assert metrics.role.eq('KNOWN ENGINEERING ONLY').all()


def test_latest_decision_does_not_claim_new_final_validation():
    from credit_platform.economic_evidence import get
    evidence,source=get()
    assert evidence['hardening']['final_independent_validation']=='NOT_RUN_PREFLIGHT_BLOCKED'
    assert evidence['hardening']['retained_model']=='s2-r1-monotone-gb-1'
    assert evidence['status']=='CHALLENGER_NOT_PROMOTED'
    assert source['path']=='lgd_hardening/results/decision.json'


def test_scenario_contract_does_not_accept_invalid_weight_or_duplicate():
    import copy
    scenarios=copy.deepcopy(policy()['scenarios']);scenarios[0]['weight']=float('nan')
    with pytest.raises(ValueError,match='weights'):assess(sample(),None,scenarios)
    scenarios=copy.deepcopy(policy()['scenarios']);scenarios[0]['scenario']='baseline'
    with pytest.raises(ValueError,match='identities'):assess(sample(),None,scenarios)
