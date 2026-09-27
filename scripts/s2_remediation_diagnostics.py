"""Post-freeze explanatory tables; no candidate/data/threshold modification."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from credit_platform.risk import policy
from economic_lgd.economics import MACRO,scenario_frame
from s2_remediation.evaluate import OUT,DEST,verify,verify_lock


def main():
    verify();verify_lock()
    development=pd.read_csv(DEST/'development_inputs.csv.gz')
    scenarios=policy()['scenarios']
    baseline=next(s for s in scenarios if s['scenario']=='baseline')
    support=[];quality=[]
    for cohort,path in [('development',DEST/'development_inputs.csv.gz'),
                        ('promotion',DEST/'promotion_inputs.csv.gz'),
                        ('current',ROOT/'economic_lgd/data/current_inputs.csv.gz')]:
        frame=pd.read_csv(path)
        for group,mask in [('zero',frame.guarantee_coverage==0),
                           ('partial',frame.guarantee_coverage.between(0,1,inclusive='neither')),
                           ('full',frame.guarantee_coverage==1)]:
            quality.append(dict(cohort=cohort,guarantee=group,n=int(mask.sum()),
                mean_guarantor_strength=float(frame.loc[mask,'guarantor_strength'].mean()),
                mean_security_quality=float(frame.loc[mask,'security_quality'].mean()),
                purpose='NONDEPLOYABLE DIAGNOSTIC ONLY; NOT MODEL FEATURES; NO CAUSAL ATTRIBUTION'))
        if cohort=='development': continue
        for scenario in scenarios:
            f=scenario_frame(frame,scenario,baseline)
            for field in MACRO:
                low=development[field].min(); high=development[field].max()
                support.append(dict(cohort=cohort,scenario=scenario['scenario'],feature=field,
                    development_min=float(low),development_max=float(high),
                    scoring_min=float(f[field].min()),scoring_max=float(f[field].max()),
                    below=int((f[field]<low).sum()),above=int((f[field]>high).sum())))
    pd.DataFrame(support).to_csv(OUT/'support_diagnosis.csv',index=False)
    pd.DataFrame(quality).to_csv(OUT/'quality_diagnostic.csv',index=False)
    corrected=pd.read_csv(OUT/'scenario_ecl.csv').set_index('facility_id')
    original=pd.read_csv(ROOT/'economic_lgd/results/scenario_ecl.csv').set_index('facility_id').loc[corrected.index]
    current=pd.read_csv(ROOT/'economic_lgd/data/current_inputs.csv.gz').set_index('facility_id').loc[corrected.index]
    movement=[]
    groups=[('all',np.ones(len(current),dtype=bool)),
            ('guarantee:zero',current.guarantee_coverage==0),
            ('guarantee:partial',current.guarantee_coverage.between(0,1,inclusive='neither')),
            ('guarantee:full',current.guarantee_coverage==1)]
    for label,mask in groups:
        for scenario in scenarios:
            col='ecl_'+scenario['scenario'];weight=scenario['weight']
            old=float(original.loc[mask,col].sum()*weight)
            new=float(corrected.loc[mask,col].sum()*weight)
            movement.append(dict(group=label,scenario=scenario['scenario'],n=int(np.sum(mask)),
                original_s2_weighted_ecl=old,corrected_weighted_ecl=new,change=new-old))
    movement=pd.DataFrame(movement)
    assert abs(movement[movement.group=='all'].change.sum()-
        (corrected.corrected_ecl.sum()-original.corrected_ecl.sum()))<1e-6
    movement.to_csv(OUT/'ecl_movement.csv',index=False)
    print(pd.DataFrame(support).query('below>0 or above>0').to_string(index=False))
    print(pd.DataFrame(quality).query("guarantee=='full'").to_string(index=False))
    print(movement.query("group=='all'").to_string(index=False))


if __name__=='__main__':main()
