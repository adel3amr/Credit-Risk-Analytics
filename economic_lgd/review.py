"""Independent result review; reads frozen predictions, never fits or rescales them."""
import json
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,atomic_json,file_hash
from .economics import MACRO,scenario_frame
from credit_platform.risk import policy

OUT=ROOT/'economic_lgd/results'


def main():
    support=[]
    dev=pd.read_csv(ROOT/'economic_lgd/data/development_inputs.csv.gz')
    current=pd.read_csv(ROOT/'economic_lgd/data/current_inputs.csv.gz')
    scenarios=policy()['scenarios']; baseline=next(s for s in scenarios if s['scenario']=='baseline')
    for s in scenarios:
        frame=scenario_frame(current,s,baseline)
        for field in MACRO+['interest_rate']:
            lo,hi=dev[field].min(),dev[field].max()
            support.append(dict(scenario=s['scenario'],feature=field,development_min=lo,
                development_max=hi,scoring_min=frame[field].min(),scoring_max=frame[field].max(),
                outside_fraction=float(((frame[field]<lo)|(frame[field]>hi)).mean())))
    pd.DataFrame(support).to_csv(OUT/'support.csv',index=False)
    rows=[]
    for cohort in ['selection','final','current']:
        p=pd.read_csv(OUT/f'{cohort}_predictions.csv')
        recorded=pd.read_csv(OUT/f'{cohort}_metrics.csv')
        for model in ['incumbent','corrected']:
            for group,mask in [('all',np.ones(len(p),dtype=bool)),('regime:0',p.latent_regime.eq(0)),('regime:1',p.latent_regime.eq(1))]:
                error=p.loc[mask,model]-p.loc[mask,'conditional_mean']
                selected=recorded[(recorded.model==model)&(recorded.group==group)].iloc[0]
                assert abs(float(error.sum()/len(error))-selected.conditional_bias)<1e-12
                rows.append(dict(cohort=cohort,model=model,group=group,n=len(error),
                    bias_pp=float(error.mean()*100),mae_pp=float(selected.mae*100),
                    rmse_pp=float(selected.rmse*100),realized_bias_pp=float(selected.bias*100)))
    ecl=pd.read_csv(OUT/'scenario_ecl.csv')
    violations=np.maximum(ecl.lgd_upside-ecl.lgd_baseline,0)+np.maximum(ecl.lgd_baseline-ecl.lgd_downside,0)
    ecl.loc[violations>1e-12].assign(violation_pp=violations[violations>1e-12]*100).to_csv(OUT/'scenario_exceptions.csv',index=False)
    summary=dict(model_version='s2-observable-gb-1',status='CHALLENGER_NOT_PROMOTED',
        bank_gate='BLOCKED',historical_s1_bias_pp=-12.6538,
        population_comparison='S2 before/after only; S1 historical bias is not a comparable S2 baseline',
        metrics=rows,scenario=json.loads((OUT/'scenario_validation.json').read_text()),
        ecl=json.loads((OUT/'ecl_reconciliation.json').read_text()),
        reversal_count=int((violations>1e-12).sum()),maximum_reversal_pp=float(violations.max()*100),
        economic_variables=MACRO,calibration_overlay=None,moc=0,
        remaining_deficiencies=[
            '78 facility scenario order reversals; up to 0.9342 pp, not economically justified',
            'Downside conditional bias -2.3177 pp; stress support extrapolation must be qualified',
            'Final full-guarantee segment conditional bias +4.6460 pp, n=135',
            'Current economic validation has seven sector clusters, not 8695 independent economies',
            'Synthetic fixtures and assumed economic coefficients do not establish institutional suitability'],
        decision='Aggregate current transfer improved on S2; strict scenario and segment promotion conditions not met. No retuning after final opening.',
        source_hashes={str(p.relative_to(ROOT)):file_hash(p) for p in sorted(OUT.glob('*.csv'))})
    atomic_json(OUT/'decision.json',summary)
    registry=json.loads((OUT/'registry.json').read_text())
    registry['promotion']='NOT_PROMOTED'
    registry['limitations']=summary['remaining_deficiencies']
    atomic_json(OUT/'registry.json',registry)
    print(json.dumps({k:summary[k] for k in ['status','reversal_count','maximum_reversal_pp','remaining_deficiencies']},indent=2))


if __name__=='__main__': main()
