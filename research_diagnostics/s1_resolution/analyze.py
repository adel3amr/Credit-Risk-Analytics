"""S1 conditional LGD diagnosis. No training, recalibration or promotion."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from credit_platform import artifacts
from synthetic_bank.generate import ROOT,DEST,sha
from synthetic_bank.evaluate import verify_data
from research_diagnostics.s1_resolution.conditional import integrate

OUT=ROOT/'research_diagnostics/s1_resolution/results'


def groups(x,p,mu,y=None):
    yield 'all',np.ones(len(x),dtype=bool)
    if y is not None:
        for q in [.6,.75,.9]:
            yield f'realized_gt{int(q*100)}',y>q
        yield 'realized_le10',y<=.1
    for label,values in [('predicted',p),('conditional',mu)]:
        for lo,hi in zip([0,.2,.4,.6,.8],[.2,.4,.6,.8,1]):
            yield f'{label}_{lo:.1f}_{hi:.1f}',(values>=lo)&((values<hi) if hi<1 else (values<=hi))
    yield 'conditional_gt60',mu>.6
    yield 'conditional_gt75',mu>.75
    for field in ['collateral_type','lien_rank','product_type','industry']:
        for value in sorted(x[field].unique()):
            yield field+':'+value,x[field].eq(value).to_numpy()
    for name,mask in [('zero',x.guarantee_coverage.eq(0)),('partial',x.guarantee_coverage.between(0,1,inclusive='neither')),('full',x.guarantee_coverage.eq(1))]:
        yield 'guarantee:'+name,mask.to_numpy()
    for name,values,edges in [('coverage',x.collateral_coverage,[0,.5,1,np.inf]),
                              ('ead',x.ead_at_default,[0,100000,500000,np.inf])]:
        for lo,hi in zip(edges[:-1],edges[1:]):
            yield f'{name}:{lo}-{hi}',((values>=lo)&(values<hi)).to_numpy()


def mean_interval(error,borrower):
    error=np.asarray(error,dtype=float)
    if not len(error) or not np.isfinite(error).all():
        raise ValueError('Finite nonempty errors required')
    frame=pd.DataFrame({'borrower':borrower,'e':error})
    g=frame.groupby('borrower').e.agg(['sum','size'])
    avg=error.mean(); n=len(error); count=len(g)
    se=float(np.sqrt(count/(count-1)*np.sum((g['sum']-g['size']*avg)**2))/n) if count>1 else np.nan
    return float(avg-1.96*se),float(avg+1.96*se),count


def summarize(x,p,mu,var,se,y,cohort,name):
    p=np.asarray(p); mu=np.asarray(mu)
    if p.shape!=mu.shape or not np.isfinite(p).all() or not np.isfinite(mu).all():
        raise ValueError('Invalid predictions')
    rows=[]
    for label,mask in groups(x,p,mu,y):
        n=int(mask.sum())
        if not n:
            rows.append(dict(cohort=cohort,model=name,group=label,n=0)); continue
        err=p[mask]-mu[mask]
        low,high,g=mean_interval(err,x.loc[mask,'customer_id'].to_numpy())
        row=dict(cohort=cohort,model=name,group=label,n=n,borrowers=g,small_sample=g<30,
            mean_prediction=float(p[mask].mean()),mean_conditional=float(mu[mask].mean()),
            model_bias=float(err.mean()),model_bias_ci_low=low,model_bias_ci_high=high,
            conditional_rmse=float(np.sqrt(np.mean(err**2))),
            conditional_outcome_sd=float(np.sqrt(var[mask].mean())),
            expected_rmse=float(np.sqrt(np.mean(var[mask]+err**2))),
            mean_mc_se=float(np.sqrt(np.sum(se[mask]**2))/n),
            ead_weighted_model_bias=float(np.average(err,weights=x.loc[mask,'ead_at_default'])))
        if y is not None:
            realized=p[mask]-y[mask]; noise=mu[mask]-y[mask]
            row.update(mean_realized=float(y[mask].mean()),bias=float(realized.mean()),
                realization_bias=float(noise.mean()),mae=float(np.abs(realized).mean()),
                rmse=float(np.sqrt(np.mean(realized**2))))
            row['identity_error']=abs(row['bias']-row['model_bias']-row['realization_bias'])
            assert row['identity_error']<1e-12
            lo,hi,_=mean_interval(realized,x.loc[mask,'customer_id'].to_numpy())
            row.update(bias_ci_low=lo,bias_ci_high=hi)
        rows.append(row)
    return rows


def main():
    verify_data()
    if OUT.exists():
        raise SystemExit('Diagnostic output exists; preserve previous results')
    OUT.mkdir(parents=True)
    lock=json.loads((ROOT/'synthetic_bank/results/FINAL_LOCK.json').read_text())
    candidate_path=ROOT/'synthetic_bank/results/candidates.joblib'
    assert sha(candidate_path)==lock['artifact_hash']
    models,_=joblib.load(candidate_path)
    governed,manifest=artifacts.load()
    models={k:models[k] for k in ['frozen_v5','s1_same_spec','s1_captured_features']}
    models['governed_v5_8000']=governed['lgd']
    rows=[]; calibration=[]
    for cohort in ['final','selection','development','current']:
        b=pd.read_csv(DEST/cohort/'borrowers.csv.gz')
        x=pd.read_csv(DEST/cohort/'facilities.csv.gz')
        x=x.merge(b[['customer_id','interest_rate']],on='customer_id',validate='many_to_one')
        y=None
        if cohort!='current':
            w=pd.read_csv(DEST/cohort/'workouts.csv.gz')
            x=x.merge(w[['facility_id','economic_lgd']],on='facility_id',validate='one_to_one')
            y=x.economic_lgd.to_numpy()
        mu,var,se=integrate(x)
        evidence=x[['facility_id','customer_id']].copy()
        evidence['conditional_mean']=mu; evidence['conditional_variance']=var; evidence['mc_se']=se
        if y is not None: evidence['actual']=y
        for name,model in models.items():
            p=np.clip(model.predict(x),0,1)
            evidence[name]=p
            rows.extend(summarize(x,p,mu,var,se,y,cohort,name))
            slope,intercept=np.polyfit(p,mu,1)
            calibration.append(dict(cohort=cohort,model=name,target='conditional_mean',intercept=intercept,slope=slope))
            if y is not None:
                slope,intercept=np.polyfit(p,y,1)
                calibration.append(dict(cohort=cohort,model=name,target='realized',intercept=intercept,slope=slope))
        evidence.to_csv(OUT/(cohort+'_expectations.csv'),index=False)
        print(cohort,len(x),'completed',flush=True)
    frame=pd.DataFrame(rows)
    frame.to_csv(OUT/'group_metrics.csv',index=False)
    pd.DataFrame(calibration).to_csv(OUT/'calibration_slopes.csv',index=False)
    sources=[Path(__file__),ROOT/'research_diagnostics/s1_resolution/conditional.py',ROOT/'synthetic_bank/generate.py']
    info=dict(baseline='3539e36',draws=4096,seed=2026092501,
        data_manifest_hash=sha(DEST/'manifest.json'),candidate_hash=sha(candidate_path),
        governed_artifact_hash=manifest['artifacts']['lgd'],
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        status='RETROSPECTIVE SYNTHETIC DIAGNOSTIC; NO PROMOTION',
        uncertainty='approximate normal cluster-robust mean intervals; multiple comparisons not adjusted; MC means use independent integration draws')
    (OUT/'manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print(frame[(frame.cohort=='final') & frame.group.isin(['all','realized_gt75','conditional_gt75'])][
        ['model','group','n','borrowers','bias','model_bias','realization_bias','conditional_rmse','conditional_outcome_sd','model_bias_ci_low','model_bias_ci_high']].to_string(index=False))


if __name__=='__main__':
    main()
