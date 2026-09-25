"""One targeted candidate and paired simulator context diagnostic; no promotion."""
import json
import gzip
import joblib
import numpy as np
import pandas as pd
from credit_platform import artifacts,risk,validation
from credit_platform.domain import DatasetInput
from synthetic_bank.generate import ROOT,DEST,sha
from lgd_research.run_study import model,NEW_NUM
from src.lgd_model import NUMERIC_FEATURES,CATEGORICAL_FEATURES
from research_diagnostics.s1_resolution.conditional import integrate
from research_diagnostics.s1_resolution.analyze import OUT,summarize
from synthetic_bank.evaluate import verify_data


def inputs(cohort):
    b=pd.read_csv(DEST/cohort/'borrowers.csv.gz')
    f=pd.read_csv(DEST/cohort/'facilities.csv.gz')
    f=f.merge(b[['customer_id','interest_rate']],on='customer_id',validate='many_to_one')
    e=pd.read_csv(OUT/(cohort+'_expectations.csv'))
    return f.merge(e,on=['facility_id','customer_id'],validate='one_to_one')


def main():
    verify_data()
    target=OUT/'targeted_candidate.joblib'
    if target.exists(): raise SystemExit('Targeted candidate exists; do not retune')
    d=inputs('development')
    candidate=model(NUMERIC_FEATURES+NEW_NUM+['interest_rate'],[c for c in CATEGORICAL_FEATURES if c!='industry'])
    candidate.fit(d,d.actual)
    joblib.dump(candidate,target)
    rows=[];support=[]
    train_pairs=set(zip(d.industry,d.downturn_at_default))
    for cohort in ['development','selection','final','current']:
        x=inputs(cohort)
        prediction=np.clip(candidate.predict(x),0,1)
        rows.extend(summarize(x,prediction,x.conditional_mean.to_numpy(),x.conditional_variance.to_numpy(),
            x.mc_se.to_numpy(),x.actual.to_numpy() if 'actual' in x else None,cohort,'targeted_context_rate'))
        x['targeted_context_rate']=prediction
        x[['facility_id','customer_id','targeted_context_rate']].to_csv(OUT/(cohort+'_targeted_predictions.csv'),index=False)
        for (industry,context),g in x.groupby(['industry','downturn_at_default']):
            support.append(dict(cohort=cohort,industry=industry,context=int(context),n=len(g),
                seen_in_development=(industry,context) in train_pairs,
                governed_bias=float((g.governed_v5_8000-g.conditional_mean).mean()),
                enhanced_bias=float((g.s1_captured_features-g.conditional_mean).mean()),
                targeted_bias=float((g.targeted_context_rate-g.conditional_mean).mean())))
    pd.DataFrame(rows).to_csv(OUT/'targeted_group_metrics.csv',index=False)
    pd.DataFrame(support).to_csv(OUT/'context_support.csv',index=False)
    current=inputs('current')
    altered=current.copy(); altered['downturn_at_default']=0
    mu,_,_=integrate(altered)
    (OUT/'context_counterfactual.json').write_text(json.dumps(dict(
        interpretation='paired simulator sensitivity; only context changed; no source mutation',
        n=len(current),downturn_share=float(current.downturn_at_default.mean()),
        conditional_mean_current=float(current.conditional_mean.mean()),
        conditional_mean_context_zero=float(mu.mean()),
        difference=float((current.conditional_mean-mu).mean()),
        governed_mean=float(current.governed_v5_8000.mean())),indent=2)+'\n')
    # Actual production path first, then explicit counterfactual LGD replacements.
    with gzip.open(DEST/'current/canonical.json.gz','rt') as stream:
        dataset=DatasetInput.model_validate(json.load(stream)).model_dump(mode='json')
    models,manifest=artifacts.load()
    traces=risk.score(dataset,models,manifest,risk.policy())
    reconciled=validation.reconcile(traces)
    trace=pd.DataFrame(traces)[['facility_id','borrower_id','pd','lgd','ead','stage','effective_pd','ecl']]
    trace=trace.merge(current,on='facility_id',validate='one_to_one',suffixes=('','_source'))
    p=np.clip(candidate.predict(current),0,1)
    mapped=dict(zip(current.facility_id,p))
    trace['targeted_context_rate']=trace.facility_id.map(mapped)
    impacts=[]
    for name in ['governed_v5_8000','frozen_v5','s1_same_spec','s1_captured_features','targeted_context_rate','conditional_mean']:
        trace[name+'_ecl']=trace.effective_pd*trace[name]*trace.ead
        total=float(trace[name+'_ecl'].sum())
        impacts.append(dict(model=name,ecl=total,delta_vs_governed=total-reconciled['ecl'],
            status='SIMULATOR EXPECTATION DIAGNOSTIC' if name=='conditional_mean' else 'GOVERNED' if name=='governed_v5_8000' else 'SHADOW ONLY; NO PROMOTION'))
    assert np.max(np.abs(trace['governed_v5_8000_ecl']-trace.ecl))<1e-7
    # All shadows share the same immutable PD/EAD/stage calculation; facility to
    # borrower and portfolio summation checked independently via grouped sums.
    for item in impacts:
        value=trace.groupby('borrower_id')[item['model']+'_ecl'].sum().sum()
        assert np.isclose(value,item['ecl'],atol=1e-7,rtol=1e-12)
    pd.DataFrame(impacts).to_csv(OUT/'ecl_impacts.csv',index=False)
    trace[['facility_id','borrower_id','pd','ead','stage','effective_pd','ecl']+
        [i['model']+'_ecl' for i in impacts]].to_csv(OUT/'facility_ecl_shadows.csv',index=False)
    (OUT/'current_reconciliation.json').write_text(json.dumps(reconciled,indent=2)+'\n')
    (OUT/'targeted_manifest.json').write_text(json.dumps(dict(
        status='RESEARCH; NO UNTOUCHED PROMOTION TEST; NOT PROMOTED',
        artifact_hash=sha(target),source_hash=sha(__file__),
        development_n=len(d),changed_features='remove industry, add known contractual interest_rate; GB hyperparameters unchanged'),indent=2)+'\n')
    print(pd.DataFrame(rows).query("cohort in ['final','current'] and group in ['all','realized_gt75','conditional_gt75']")[[
        'cohort','group','n','model_bias','conditional_rmse','bias','realization_bias']].to_string(index=False))
    print(pd.DataFrame(impacts).to_string(index=False))


if __name__=='__main__': main()
