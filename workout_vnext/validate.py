"""Independent ledger arithmetic and frozen-artifact diagnostics. Never fits a model."""
import ast, gzip, json, math
from collections import defaultdict
import joblib
import numpy as np
import pandas as pd
from .generate import DATA,HERE,CHANNELS,FEATURES,sha,dump,save
from .experiment import OUT,verify,features


def read(name):
    with gzip.open(DATA/(name+'.jsonl.gz'),'rt') as f:return [json.loads(l) for l in f]


def validate():
    verify()
    lock=json.loads((OUT/'LOCK.json').read_text())
    for f,h in lock['models'].items():assert sha(OUT/f)==h
    from .store import ENTITIES
    grouped={n:defaultdict(list) for n in ENTITIES}
    counts={};seen=set()
    for n in ENTITIES:
        for r in read(n):
            assert r['id'] not in seen;seen.add(r['id'])
            assert r['amount']>=0 and r['recorded_at']>=r['effective_date']
            grouped[n][r['facility_id']].append(r)
        counts[n]=sum(map(len,grouped[n].values()))
    facilities={r['id']:r for r in read('facility')}
    borrowers={r['id'] for r in read('borrower')}
    assert all(f['borrower_id'] in borrowers for f in facilities.values())
    assert all(fid in facilities for v in grouped.values() for fid in v)
    split_ids={};max_error=0.;checked=0;clipped=0;open_count=0;guarantees=[];contract=[]
    for split in ['development','validation','final']:
        x=pd.read_csv(DATA/f'{split}_inputs.csv.gz');y=pd.read_csv(DATA/f'{split}_outcomes.csv.gz');assert x.snapshot_id.equals(y.snapshot_id)
        split_ids[split]=set(x.borrower_id)
        for row,target in zip(x.to_dict('records'),y.to_dict('records')):
            f=facilities[row['facility_id']];fid=f['id'];obs=row['observation_date'];base=f['principal']+f['predefault_interest']
            visible={n:[r for r in grouped[n][fid] if r['effective_date']<=obs and r['recorded_at']<=obs] for n in ENTITIES}
            ids={r['id'] for records in visible.values() for r in records}
            known=set(ast.literal_eval(row['known_event_ids']))
            # The snapshot record is written after its input lineage is captured.
            expected=ids-{r['id'] for r in visible['workout_snapshot'] if r['effective_date']==obs}
            assert known==expected
            assert not visible['resolution_event']
            ead=base-math.fsum(r['amount'] for r in visible['recovery_transaction'])
            assert abs(ead-row['ead'])<max(1e-5,ead*1e-10)
            mi=math.fsum(r['amount'] for r in visible['interest_accrual'])
            assert abs(mi/ead-row['mi_ratio'])<1e-8
            assert math.fsum(r['amount'] for r in grouped['recovery_transaction'][fid])<=base+1e-7
            # Independent use of calendar dates, not generator's stored month index.
            if target['resolved']:
                pv={c:0. for c in CHANNELS};cost=0.
                for n in ['recovery_transaction','workout_cost']:
                    for r in grouped[n][fid]:
                        if r['effective_date']<=obs:continue
                        date=pd.Timestamp(r['effective_date']);date0=pd.Timestamp(obs)
                        months=(date.year-date0.year)*12+date.month-date0.month
                        value=r['amount']*math.exp(-math.log1p(f['rate'])*months/12)/ead
                        if n=='workout_cost':cost+=value
                        else:pv[r['payload']['channel']]+=value
                raw=1-math.fsum(pv.values())+cost
                errors=[abs(raw-target['raw_lgd']),abs(max(0,min(1,raw))-target['lgd']),abs(cost-target['pv_cost'])]+[abs(pv[c]-target['pv_'+c]) for c in CHANNELS]
                max_error=max(max_error,*errors);clipped+=int(raw<0 or raw>1)
            else:
                assert math.isnan(target['lgd']) and math.isnan(target['resolution_months']);open_count+=1
            checked+=1
        guarantees.append({'split':split,'n':len(x),'zero_guarantee_share':float(x.guarantee_ratio.eq(0).mean()),'full_guarantee_share':float(x.guarantee_ratio.eq(1).mean())})
        for name in FEATURES:
            contract.append({'split':split,'feature':name,'min':float(x[name].min()),'max':float(x[name].max()),'missing':int(x[name].isna().sum()),'mean':float(x[name].mean()),'std':float(x[name].std())})
    assert max_error<1e-8
    assert not(split_ids['development']&split_ids['validation'] or split_ids['development']&split_ids['final'] or split_ids['validation']&split_ids['final'])
    dump(OUT/'ledger_audit.json',{'observations':checked,'maximum_target_error':max_error,'resolved_targets_clipped':clipped,'open_observations_without_target':open_count,'split_borrowers':{k:len(v) for k,v in split_ids.items()},'asof_lineage_checks':checked,'cash_recovery_cap_checks':checked,'mi_excluded_from_ead_checks':checked,'counts':counts,'status':'PASS'})
    pd.DataFrame(guarantees).to_csv(OUT/'guarantee_support.csv',index=False);pd.DataFrame(contract).to_csv(OUT/'feature_population.csv',index=False)
    # One observation per final-test facility; include censored episodes, no actuals needed.
    x=pd.read_csv(DATA/'final_inputs.csv.gz');x=x[x.age==0].copy();assert x.facility_id.is_unique
    direct=joblib.load(OUT/'direct_new.joblib');component=joblib.load(OUT/'component.joblib')
    old=np.clip(direct.predict(features(x)),0,1);new=component.predict(x);parts,pcure,timing=component.predict_components(x)
    bridge=x[['facility_id','borrower_id','industry','ead','observation_date']].copy();bridge['stage']='Stage 3';bridge['pd']=1;bridge['scenario_weight']=1;bridge['direct_lgd']=old;bridge['component_lgd']=new;bridge['direct_ecl']=x.ead*old;bridge['component_ecl']=x.ead*new;bridge['change']=bridge.component_ecl-bridge.direct_ecl
    save(OUT/'ecl_facilities.csv.gz',bridge)
    a=math.fsum(bridge.direct_ecl);b=math.fsum(bridge.component_ecl)
    dump(OUT/'ecl_bridge.json',{'currency':'EUR','scope':'1600 final default episodes at age zero; multiple reporting dates, vintage cohort not a single-date bank portfolio','facilities':len(x),'ead':math.fsum(x.ead),'direct_ecl':a,'component_ecl':b,'change':b-a,'change_pct':100*(b/a-1),'stage1':'N/A: impaired-only cohort; active platform unchanged','stage2':'N/A: impaired-only cohort; active platform unchanged','stage3_direct':a,'stage3_component':b,'scenario':'baseline weight 1; shadow, unbooked','maximum_facility_error':float(np.max(abs(bridge.component_ecl-bridge.pd*bridge.component_lgd*bridge.ead)))})
    bridge.groupby('industry')[['ead','direct_ecl','component_ecl','change']].sum().to_csv(OUT/'ecl_segments.csv')
    cases=[]
    for label,idx in [('low_prediction',int(np.argmin(new))),('high_prediction',int(np.argmax(new))),('no_guarantee',int(np.flatnonzero(x.guarantee_ratio.to_numpy()==0)[0])),('full_guarantee',int(np.flatnonzero(x.guarantee_ratio.to_numpy()==1)[0]))]:
        row=x.iloc[idx]
        cases.append({'case':label,'input':row.drop('known_event_ids').to_dict(),'lineage_event_ids':ast.literal_eval(row.known_event_ids),'p_cure':float(pcure[idx]),'predicted_resolution_months_resolved_fit':float(timing[idx]),'pv_channel_shares':dict(zip(CHANNELS,map(float,parts[idx,:-1]))),'pv_cost_share':float(parts[idx,-1]),'raw_lgd':float(1-sum(parts[idx,:-1])+parts[idx,-1]),'bounded_lgd':float(new[idx]),'ecl':float(new[idx]*row.ead),'model_hash':sha(OUT/'component.joblib'),'dataset_manifest_hash':sha(DATA/'manifest.json'),'stage':3,'pd':1,'scenario_weight':1})
    dump(OUT/'worked_cases.json',cases)
    # Cluster intervals for absolute error and calibration/cure, independent resampling.
    rng=np.random.default_rng(1073000);rows=[]
    allpred=pd.read_csv(OUT/'predictions.csv.gz');fx=pd.read_csv(DATA/'final_inputs.csv.gz');fy=pd.read_csv(DATA/'final_outcomes.csv.gz');mask=fy.resolved.eq(1);cp=component.predict_components(fx[mask])[1];outcomes=fy[mask].reset_index(drop=True)
    for model in ['direct_new','component']:
        g=allpred[(allpred.split=='final')&(allpred.model==model)].reset_index(drop=True);groups=g.groupby('borrower_id').indices;keys=list(groups);values=[]
        for _ in range(400):
            ix=np.concatenate([groups[keys[i]] for i in rng.integers(0,len(keys),len(keys))]);r=g.iloc[ix];err=r.prediction-r.actual;slope,intercept=np.polyfit(r.prediction,r.actual,1)
            values.append([np.sqrt(np.mean(err**2)),np.mean(abs(err)),np.mean(err),slope,intercept,float(np.mean((cp[ix]-outcomes.future_cure.iloc[ix].to_numpy())**2))])
        bounds=np.quantile(values,[.025,.975],axis=0)
        for j,name in enumerate(['rmse','mae','bias','slope','intercept','cure_brier_component']):rows.append({'model':model,'metric':name,'low':bounds[0,j],'high':bounds[1,j]})
    pd.DataFrame(rows).to_csv(OUT/'absolute_uncertainty.csv',index=False)
    dump(OUT/'cure_validation.json',{'resolved_observations':len(cp),'actual_cure_rate':float(outcomes.future_cure.mean()),'predicted_cure_rate':float(cp.mean()),'brier':float(np.mean((cp-outcomes.future_cure)**2)),'scope':'resolved-only; censored ultimate cure unknown','timing':'log-Ridge diagnostic conditional on resolution; not censor-adjusted'})
    print(json.dumps(json.loads((OUT/'ledger_audit.json').read_text()),indent=2))

if __name__=='__main__':validate()
