"""Publish the preflight disposition without claiming a new independent final."""
import json
from credit_platform.common import ROOT,atomic_json,file_hash
from .audit import OUT


def main():
    previous_path=ROOT/'s2_remediation/results/decision.json'
    previous=json.loads(previous_path.read_text())
    audit=json.loads((OUT/'baseline_audit.json').read_text())
    trial=json.loads((OUT/'calibration_engineering.json').read_text())
    # Best retained candidate is R1. The additional calibration is rejected,
    # never relabelled as a new independently validated model.
    hardening=dict(status='PREFLIGHT_BLOCKED',retained_model=previous['model_version'],
        rejected_candidate=trial['version'],
        reason='Unavailable prediction-time recovery-quality evidence; imported latent quality shifts persist. Global calibration worsened downside and original high bands.',
        quality_sensitivity_pp=audit['quality_shift_mean_pp'],
        final_holdout_generated=False,final_independent_validation='NOT_RUN_PREFLIGHT_BLOCKED',
        unchanged_acceptance_tolerances=True,no_holdout_fit=True,
        data_requirement='Dated independently sourced security/guarantor evidence AND a validated feature derivation; simulator truth is prohibited',
        qualification='Does not prove all statistical approximations are impossible; does prevent asserting a validated recovery-information contract without evidence')
    evidence={**previous,'hardening':hardening,
        'remaining_deficiencies':[
            'Residual recovery-quality population shift lacks validated prediction-time capture/derivation',
            'R1 downside uncertainty, guarantee and prediction-band gates remain failed',
            'R1 retired holdout still has 327/6000 downside support exceptions; new domain controls do not waive them',
            'Global continuous calibration rejected: current downside bias deteriorates to -1.59 pp',
            'No new independent final holdout opened because preflight requirements remain unmet',
            'Institutional data, external validation, security and deployment qualification remain unavailable'],
        'historical_decision':str(previous_path.relative_to(ROOT))}
    sources={**previous['source_hashes'],str(previous_path.relative_to(ROOT)):file_hash(previous_path)}
    for p in sorted(OUT.iterdir()):
        if p.suffix in ['.json','.csv','.txt'] and p.name not in ['decision.json','registry.json']:
            sources[str(p.relative_to(ROOT))]=file_hash(p)
    evidence['source_hashes']=sources
    atomic_json(OUT/'decision.json',evidence)
    atomic_json(OUT/'registry.json',dict(model_id=previous['model_version'],status=previous['status'],
        decision_sha256=file_hash(OUT/'decision.json'),gates=previous['gates'],bank_gate='BLOCKED',
        rejected_candidate=trial['version'],final_independent_validation='NOT_RUN_PREFLIGHT_BLOCKED'))
    print(json.dumps(hardening,indent=2))


if __name__=='__main__':main()
