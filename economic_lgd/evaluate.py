"""Single-candidate execution with frozen data, independent diagnostics and shadow ECL."""
import argparse
import gzip
import json
import joblib
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,file_hash,atomic_json
from credit_platform import artifacts,risk
from .generate import DEST
from .model import build,features,predict,VERSION
from .recovery import conditional,BUCKETS
from .scenarios import shadow

OUT=ROOT/'economic_lgd/results'


def verify():
    manifest=json.loads((DEST/'manifest.json').read_text())
    for p,h in {**manifest['files'],**manifest['sources']}.items():
        if file_hash(ROOT/p)!=h:
            raise ValueError('Frozen source/data mismatch: '+p)


def load(name):
    x=pd.read_csv(DEST/f'{name}_inputs.csv.gz')
    y=pd.read_csv(DEST/f'{name}_outcomes.csv.gz')
    if not x.facility_id.equals(y.facility_id):
        raise ValueError('Target identity mismatch')
    # Independent target reconstruction from stored cashflows.
    pv=np.zeros(len(x))
    for m in BUCKETS:
        pv+=y[f'net_cf_{m}m'].to_numpy()/np.power(1+x.interest_rate.to_numpy(),m/12)
    expected=np.clip(1-pv/x.ead_at_default.to_numpy(),0,1)
    if np.max(np.abs(expected-y.economic_lgd.to_numpy()))>1e-9:
        raise ValueError('Cashflow target reconciliation failed')
    return x,y


def groups(x,p,y):
    yield 'all',np.ones(len(x),dtype=bool)
    for state in (0,1):
        yield 'regime:'+str(state),x.latent_regime.eq(state).to_numpy()
    for field in ['collateral_type','product_type','industry','lien_rank','reporting_date']:
        for value in sorted(x[field].unique()):
            yield field+':'+str(value),x[field].eq(value).to_numpy()
    for field,edges in [('collateral_coverage',[0,.5,1,np.inf]),
                        ('ead_at_default',[0,100000,500000,np.inf])]:
        for lo,hi in zip(edges[:-1],edges[1:]):
            yield f'{field}:{lo}-{hi}',((x[field]>=lo)&(x[field]<hi)).to_numpy()
    for name,mask in [('zero',x.guarantee_coverage==0),('partial',x.guarantee_coverage.between(0,1,inclusive='neither')),('full',x.guarantee_coverage==1)]:
        yield 'guarantee:'+name,mask.to_numpy()
    for lo in [0,.2,.4,.6,.8]:
        yield f'predicted:{lo:.1f}',(p>=lo)&((p<lo+.2) if lo<.8 else (p<=1))
    for threshold in [.6,.75,.9]:
        yield 'realized_gt:'+str(threshold),y>threshold


def metrics(x,y,p,mu,name,cohort):
    rows=[]
    for group,mask in groups(x,p,y):
        if not mask.any(): continue
        err=p[mask]-mu[mask]
        clusters=x.loc[mask,'industry']+'|'+x.loc[mask,'reporting_date']
        g=pd.DataFrame({'cluster':clusters.to_numpy(),'e':err}).groupby('cluster').e.agg(['sum','size'])
        count=len(g); n=len(err); avg=float(err.mean())
        se=float(np.sqrt(count/(count-1)*np.sum((g['sum']-g['size']*avg)**2))/n) if count>1 else None
        rows.append(dict(cohort=cohort,model=name,group=group,n=n,macro_clusters=count,
            mean_prediction=float(p[mask].mean()),mean_realized=float(y[mask].mean()),
            mean_conditional=float(mu[mask].mean()),conditional_bias=avg,
            conditional_bias_se=se,conditional_rmse=float(np.sqrt(np.mean(err**2))),
            mae=float(np.abs(p[mask]-y[mask]).mean()),rmse=float(np.sqrt(np.mean((p[mask]-y[mask])**2))),
            bias=float((p[mask]-y[mask]).mean())))
    return rows


def evaluate(cohort,model,incumbent):
    x,y=load(cohort)
    mu,se=conditional(x,draws=512,seed=83000+['selection','final','current'].index(cohort))
    old=np.clip(incumbent.predict(x),0,1); new=predict(model,x)
    output=x[['facility_id','customer_id','industry','reporting_date','latent_regime']].copy()
    output['actual']=y.economic_lgd; output['conditional_mean']=mu; output['conditional_mc_se']=se
    output['incumbent']=old; output['corrected']=new
    output.to_csv(OUT/f'{cohort}_predictions.csv',index=False)
    rows=metrics(x,y.economic_lgd.to_numpy(),old,mu,'incumbent',cohort)+metrics(x,y.economic_lgd.to_numpy(),new,mu,'corrected',cohort)
    pd.DataFrame(rows).to_csv(OUT/f'{cohort}_metrics.csv',index=False)
    print(pd.DataFrame(rows).query("group in ['all','regime:0','regime:1']")[[
        'cohort','model','group','n','conditional_bias','mae','rmse']].to_string(index=False),flush=True)
    return x


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('phase',choices=['develop','final'])
    args=parser.parse_args(); verify()
    models,manifest=artifacts.load()
    if args.phase=='develop':
        if OUT.exists(): raise SystemExit('Existing run: no overwrite or retuning')
        OUT.mkdir()
        x,y=load('development')
        model=build().fit(features(x),y.economic_lgd.to_numpy())
        joblib.dump(model,OUT/'model.joblib')
        evaluate('selection',model,models['lgd'])
        atomic_json(OUT/'LOCK.json',dict(model_version=VERSION,
            model_hash=file_hash(OUT/'model.joblib'),data_hash=file_hash(DEST/'manifest.json'),
            evaluator_hash=file_hash(__file__),status='FROZEN; NO TUNING; SHADOW ONLY'))
    else:
        lock=json.loads((OUT/'LOCK.json').read_text())
        if lock['model_hash']!=file_hash(OUT/'model.joblib') or lock['data_hash']!=file_hash(DEST/'manifest.json') or lock['evaluator_hash']!=file_hash(__file__):
            raise ValueError('Evaluation lock mismatch')
        with (OUT/'FINAL_OPENED.json').open('x') as stream: json.dump(lock,stream)
        model=joblib.load(OUT/'model.joblib')
        evaluate('final',model,models['lgd'])
        current=evaluate('current',model,models['lgd'])
        # Reuse governed engine and current canonical inputs; no PD/stage/EAD refit.
        with gzip.open(ROOT/'synthetic_bank/data/current/canonical.json.gz','rt') as stream:
            data=json.load(stream)
        policy=risk.policy()
        traces=risk.score(data,models,manifest,policy)
        rows,reconciliation=shadow(current,traces,model,policy['scenarios'])
        rows.to_csv(OUT/'scenario_ecl.csv',index=False)
        atomic_json(OUT/'ecl_reconciliation.json',reconciliation)
        # Scenario conditional validation uses independent random streams; no refit.
        from .economics import scenario_frame
        baseline=next(s for s in policy['scenarios'] if s['scenario']=='baseline')
        scenario_rows=[]
        for i,s in enumerate(policy['scenarios']):
            sf=scenario_frame(current,s,baseline)
            mu,_=conditional(sf,draws=512,seed=84000+i)
            p=predict(model,sf)
            scenario_rows.append(dict(scenario=s['scenario'],mean_lgd=float(p.mean()),
                conditional_mean=float(mu.mean()),conditional_bias=float((p-mu).mean())))
        atomic_json(OUT/'scenario_validation.json',scenario_rows)
        atomic_json(OUT/'registry.json',dict(model_id=VERSION,status='CHALLENGER',
            promotion='NOT_PROMOTED_PENDING_REVIEW',bank_gate='BLOCKED',
            artifact_sha256=file_hash(OUT/'model.joblib'),data_sha256=file_hash(DEST/'manifest.json'),
            feature_names=list(features(current).columns),moc=0,calibration_overlay=None,
            evidence=[f'economic_lgd/results/{name}_metrics.csv' for name in ['selection','final','current']]))
        print(json.dumps(reconciliation,indent=2),flush=True)


if __name__=='__main__': main()
