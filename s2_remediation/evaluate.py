"""One development fit, frozen candidate, then a single promotion opening."""
import argparse
import gzip
import json
import joblib
import numpy as np
import pandas as pd
from credit_platform import artifacts, risk
from credit_platform.common import ROOT, atomic_json, file_hash
from economic_lgd.economics import scenario_frame
from economic_lgd.evaluate import metrics, groups, load as old_load, verify as old_verify
from economic_lgd.recovery import BUCKETS, conditional
from economic_lgd.scenarios import shadow
from .generate import DEST
from .model import build, features, predict, VERSION, FEATURES
from .support import Support

OUT=ROOT/'s2_remediation/results'


def verify():
    old_verify()
    manifest=json.loads((DEST/'manifest.json').read_text())
    for name,h in manifest['files'].items():
        if file_hash(DEST/name)!=h: raise ValueError('Data hash mismatch: '+name)
    for name,h in manifest['sources'].items():
        if file_hash(ROOT/name)!=h: raise ValueError('Source hash mismatch: '+name)
    return manifest


def load(name):
    x=pd.read_csv(DEST/f'{name}_inputs.csv.gz')
    y=pd.read_csv(DEST/f'{name}_outcomes.csv.gz')
    if not x.facility_id.equals(y.facility_id): raise ValueError('Cashflow identity mismatch')
    pv=np.zeros(len(x))
    for m in BUCKETS:
        pv+=y[f'net_cf_{m}m'].to_numpy()/(1+x.interest_rate.to_numpy())**(m/12)
    if np.max(np.abs(np.clip(1-pv/x.ead_at_default.to_numpy(),0,1)-y.economic_lgd))>1e-9:
        raise ValueError('Independent cashflow reconciliation failed')
    return x,y


def evaluate(cohort, candidate, original, incumbent, support, seed, scenarios=False):
    x,y=old_load('current') if cohort=='current' else load(cohort)
    scenario_list=risk.policy()['scenarios'] if scenarios else [next(s for s in risk.policy()['scenarios'] if s['scenario']=='baseline')]
    baseline=next(s for s in risk.policy()['scenarios'] if s['scenario']=='baseline')
    rows=[]; outputs=[]; supported=[]; ordering={}
    for i,s in enumerate(scenario_list):
        frame=scenario_frame(x,s,baseline)
        mu,se=conditional(frame,draws=512,seed=seed+i)
        # Nonbaseline scenario truth is an independent simulated outcome, never
        # the baseline realized label paired with a different economic vintage.
        if s['scenario']=='baseline': actual=y.economic_lgd.to_numpy()
        else:
            from economic_lgd.recovery import simulate
            actual=simulate(frame,np.random.default_rng(seed+100+i))[:,0]
        preds={'incumbent':np.clip(incumbent.predict(frame),0,1),
               'original_s2':np.clip(original.predict(features(frame)),0,1),
               'corrected':predict(candidate,frame)}
        ordering[s['scenario']]=preds
        sr=support.inspect(frame); sr['scenario']=s['scenario']; sr['cohort']=cohort
        supported.append(sr)
        out=frame[['facility_id','customer_id','industry','reporting_date','latent_regime',
                   'collateral_type','guarantee_coverage','product_type','ead_at_default']].copy()
        out['scenario']=s['scenario']; out['actual']=actual
        out['conditional_mean']=mu; out['conditional_mc_se']=se
        for name,p in preds.items():
            out[name]=p
            values=metrics(frame,actual,p,mu,name,cohort)
            # Preserve macro-cluster uncertainty; borrower clustering prevents
            # treating multiple facilities from one borrower as independent.
            masks=dict(groups(frame,p,actual))
            for value in values:
                mask=masks[value['group']]
                errors=p[mask]-mu[mask]
                clustered=pd.DataFrame({'borrower':frame.loc[mask,'customer_id'].to_numpy(),
                    'error':errors}).groupby('borrower').error.agg(['sum','size'])
                count=len(clustered)
                borrower_se=float(np.sqrt(count/(count-1)*np.sum(
                    (clustered['sum']-clustered['size']*errors.mean())**2))/len(errors)) if count>1 else None
                value['borrower_bias_se']=borrower_se
                value['equivalence_se']=max(value['conditional_bias_se'] or 0,borrower_se or 0)
                value['scenario']=s['scenario']
                value['ci95_low']=value['conditional_bias']-1.96*value['equivalence_se']
                value['ci95_high']=value['conditional_bias']+1.96*value['equivalence_se']
            rows.extend(values)
        outputs.append(out)
    pd.concat(outputs).to_csv(OUT/f'{cohort}_predictions.csv',index=False)
    pd.concat(supported).to_csv(OUT/f'{cohort}_support.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/f'{cohort}_metrics.csv',index=False)
    if scenarios:
        shape=[]
        for name in ['incumbent','original_s2','corrected']:
            violation=np.maximum(ordering['upside'][name]-ordering['baseline'][name],
                                 ordering['baseline'][name]-ordering['downside'][name])
            shape.append(dict(model=name,count=int((violation>1e-10).sum()),
                maximum_reversal=float(max(0,violation.max()))))
        atomic_json(OUT/f'{cohort}_shape.json',shape)
    print(pd.DataFrame(rows).query("model=='corrected' and group in ['all','regime:0','regime:1','guarantee:full']")[[
        'cohort','scenario','group','n','conditional_bias','conditional_bias_se','mae','rmse']].to_string(index=False),flush=True)
    return x


def lock():
    paths=[OUT/'model.joblib',OUT/'support.joblib',DEST/'manifest.json',
           ROOT/'s2_remediation/PROTOCOL.md']+sorted((ROOT/'s2_remediation').glob('*.py'))
    return dict(model_version=VERSION,features=FEATURES,
        hashes={str(p.relative_to(ROOT)):file_hash(p) for p in paths},
        status='FROZEN BEFORE PROMOTION; NO RETUNING')


def verify_lock():
    frozen=json.loads((OUT/'LOCK.json').read_text())
    for path,h in frozen['hashes'].items():
        if file_hash(ROOT/path)!=h: raise ValueError('Candidate freeze mismatch: '+path)
    return frozen


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('phase',choices=['develop','final'])
    args=parser.parse_args(); verify()
    models,manifest=artifacts.load()
    original=joblib.load(ROOT/'economic_lgd/results/model.joblib')
    if args.phase=='develop':
        if OUT.exists(): raise ValueError('Existing candidate; no overwrite')
        OUT.mkdir()
        frame,outcomes=load('development')
        candidate=build(frame).fit(features(frame),outcomes.economic_lgd.to_numpy())
        support=Support().fit(frame)
        joblib.dump(candidate,OUT/'model.joblib'); joblib.dump(support,OUT/'support.joblib')
        evaluate('calibration',candidate,original,models['lgd'],support,96001,scenarios=True)
        atomic_json(OUT/'LOCK.json',lock())
    else:
        frozen=verify_lock()
        with (OUT/'FINAL_OPENED.json').open('x') as stream: json.dump(frozen,stream)
        candidate=joblib.load(OUT/'model.joblib'); support=joblib.load(OUT/'support.joblib')
        evaluate('promotion',candidate,original,models['lgd'],support,97001,scenarios=True)
        current=evaluate('current',candidate,original,models['lgd'],support,98001,scenarios=True)
        with gzip.open(ROOT/'synthetic_bank/data/current/canonical.json.gz','rt') as stream:
            data=json.load(stream)
        policy=risk.policy(); traces=risk.score(data,models,manifest,policy)
        original_rows,original_ecl=shadow(current,traces,original,policy['scenarios'])
        rows,reconciliation=shadow(current,traces,candidate,policy['scenarios'])
        rows['original_s2_ecl']=original_rows.corrected_ecl
        rows.to_csv(OUT/'scenario_ecl.csv',index=False)
        reconciliation['original_s2_ecl']=original_ecl['corrected_ecl']
        reconciliation['candidate_minus_original_s2']=reconciliation['corrected_ecl']-original_ecl['corrected_ecl']
        reconciliation['support_rejections']=int((~pd.read_csv(OUT/'current_support.csv').supported).sum())
        reconciliation['status']='UNBOOKED VALIDATION SHADOW; PROMOTION SUBJECT TO ALL GATES'
        atomic_json(OUT/'ecl_reconciliation.json',reconciliation)
        print(json.dumps(reconciliation,indent=2),flush=True)


if __name__=='__main__': main()
