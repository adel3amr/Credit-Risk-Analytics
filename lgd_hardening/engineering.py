"""Verify new domain controls on multiple known engineering populations."""
import json
import joblib
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,atomic_json,file_hash
from credit_platform.risk import policy
from economic_lgd.model import FEATURES
from s2_remediation.model import predict
from s2_remediation.evaluate import verify,verify_lock
from .audit import OUT
from .domain import assess


def main():
    verify();verify_lock()
    support=joblib.load(ROOT/'s2_remediation/results/support.joblib')
    summaries=[]
    for cohort in ['calibration','promotion','current']:
        path=ROOT/('economic_lgd/data/current_inputs.csv.gz' if cohort=='current'
                  else f's2_remediation/data/{cohort}_inputs.csv.gz')
        frame=pd.read_csv(path)
        result=assess(frame,support,policy()['scenarios'])
        result.to_csv(OUT/f'{cohort}_domain.csv',index=False)
        for scenario,g in result.groupby('scenario'):
            summaries.append(dict(cohort=cohort,scenario=scenario,n=len(g),
                rejected=int((~g.supported).sum()),reasons=g.reason.value_counts().to_dict(),
                expected_lgd_returned=int(g.expected_lgd.notna().sum())))
    atomic_json(OUT/'domain_engineering.json',summaries)
    current=pd.read_csv(ROOT/'economic_lgd/data/current_inputs.csv.gz')
    predictions=pd.read_csv(ROOT/'s2_remediation/results/current_predictions.csv')
    ecl=pd.read_csv(ROOT/'s2_remediation/results/scenario_ecl.csv').set_index('facility_id')
    model=joblib.load(ROOT/'s2_remediation/results/model.joblib')
    chosen=current.groupby(['collateral_type','guarantee_coverage'],sort=True).head(1)
    traces=[]
    for _,row in chosen.iterrows():
        f=row.to_frame().T
        # Keep original column dtypes for sklearn/economic contract validation.
        f=current[current.facility_id==row.facility_id].copy()
        original=float(predict(model,f)[0])
        responses={}
        for field in ['collateral_coverage','guarantee_coverage']:
            changed=f.copy();delta=.1
            changed[field]=np.minimum(1,changed[field]+delta) if field=='guarantee_coverage' else changed[field]+delta
            eligible=bool(support.inspect(changed).supported.iloc[0])
            responses[field]=dict(original_input=float(f[field].iloc[0]),changed_input=float(changed[field].iloc[0]),
                model_response=float(predict(model,changed)[0]-original) if eligible else None,
                supported=eligible,interpretation='Controlled model response, not a causal recovery-component allocation')
        values=predictions[predictions.facility_id==row.facility_id]
        traces.append(dict(facility_id=row.facility_id,features={k:row[k] for k in FEATURES},
            source='economic_lgd/data/current_inputs.csv.gz',
            source_hash=file_hash(ROOT/'economic_lgd/data/current_inputs.csv.gz'),
            model_version='s2-r1-monotone-gb-1',model_hash=file_hash(ROOT/'s2_remediation/results/model.joblib'),
            scenario_lgd=dict(zip(values.scenario,values.corrected)),
            protection_responses=responses,shadow_ecl=float(ecl.loc[row.facility_id,'corrected_ecl']),
            use='DIAGNOSTIC_ONLY_NOT_PROMOTED',unobserved_quality_not_included=True))
    atomic_json(OUT/'facility_traces.json',traces)
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
