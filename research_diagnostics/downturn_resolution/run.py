"""Focused downturn investigation; no source regeneration or production promotion."""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score,brier_score_loss
from lgd_research.run_study import model
from src.lgd_model import NUMERIC_FEATURES,CATEGORICAL_FEATURES
from synthetic_bank.generate import ROOT,sha
from synthetic_bank.evaluate import verify_data
from research_diagnostics.s1_resolution.followup import inputs
from research_diagnostics.s1_resolution.analyze import summarize
from research_diagnostics.downturn_resolution.calibration import RegimeCalibration,scenario_control
from research_diagnostics.downturn_resolution.mechanisms import integrate

OUT=ROOT/'research_diagnostics/downturn_resolution/results'


def main():
    verify_data()
    if OUT.exists(): raise SystemExit('Results exist; no overwrite/repeated tuning')
    OUT.mkdir(parents=True)
    d=inputs('development')
    calibrator=RegimeCalibration().fit(d.governed_v5_8000,d.collateral_type,d.downturn_at_default,d.actual)
    proxies={}
    for name,numeric,categorical in [
        ('canonical_proxy',NUMERIC_FEATURES,CATEGORICAL_FEATURES),
        ('canonical_no_industry',NUMERIC_FEATURES,[c for c in CATEGORICAL_FEATURES if c!='industry']),
        ('capture_required_proxy',NUMERIC_FEATURES+['security_quality','guarantor_strength'],[c for c in CATEGORICAL_FEATURES if c!='industry'])]:
        prep=model(numeric,categorical).named_steps['prep']
        proxies[name]=Pipeline([('prep',prep),('classifier',GradientBoostingClassifier(n_estimators=100,max_depth=2,
            learning_rate=.05,min_samples_leaf=25,random_state=42))]).fit(d,d.downturn_at_default)
    joblib.dump((calibrator,proxies),OUT/'research_calibration.joblib')
    (OUT/'calibration_coefficients.json').write_text(json.dumps(dict(
        names=['intercept','base_logit','state','Cash','Mortgage','Other','Cash_state','Mortgage_state','Other_state'],
        coefficients=calibrator.coefficients.tolist(),training='S1 development realized losses only',
        status='RESEARCH; state-source gate required'),indent=2)+'\n')
    metrics=[];proxy_metrics=[];baseline=[];calibrations=[]
    for cohort in ['development','selection','final','current']:
        x=inputs(cohort); base=x.governed_v5_8000.to_numpy(); state=x.downturn_at_default.to_numpy()
        y=x.actual.to_numpy() if 'actual' in x else None
        predictions={'governed':base,'existing_enhanced':x.s1_captured_features.to_numpy(),
            'state_oracle_calibration':calibrator.predict(base,x.collateral_type,state),
            'normal_scenario':calibrator.predict(base,x.collateral_type,np.zeros(len(x))),
            'downturn_scenario':calibrator.predict(base,x.collateral_type,np.ones(len(x)))}
        # Previously trained R2 two-stage is retained as published R2 evidence;
        # it was not serialized, so no unapproved retraining occurs here.
        for name,proxy in proxies.items():
            prob=proxy.predict_proba(x)[:,1]
            predictions[name]=calibrator.mixture(base,x.collateral_type,prob)
            proxy_metrics.append(dict(cohort=cohort,model=name,n=len(x),auc=roc_auc_score(state,prob),
                brier=brier_score_loss(state,prob),observed_state=float(state.mean()),predicted_state=float(prob.mean())))
        for name,p in predictions.items():
            rows=summarize(x,p,x.conditional_mean.to_numpy(),x.conditional_variance.to_numpy(),x.mc_se.to_numpy(),y,cohort,name)
            metrics.extend(rows)
            for regime in [0,1]:
                mask=state==regime; subset=x.loc[mask].reset_index(drop=True)
                group=summarize(subset,p[mask],subset.conditional_mean.to_numpy(),subset.conditional_variance.to_numpy(),
                    subset.mc_se.to_numpy(),y[mask] if y is not None else None,cohort,name)[0]
                group['group']='normal' if regime==0 else 'downturn'
                metrics.append(group)
            for target in ['conditional_mean']+(['actual'] if y is not None else []):
                slope,intercept=np.polyfit(p,x[target],1)
                calibrations.append(dict(cohort=cohort,model=name,target=target,slope=slope,intercept=intercept))
        pd.DataFrame({'facility_id':x.facility_id,**predictions}).to_csv(OUT/(cohort+'_predictions.csv'),index=False)
        print(cohort,'model comparisons complete',flush=True)
    pd.DataFrame(metrics).to_csv(OUT/'group_metrics.csv',index=False)
    pd.DataFrame(proxy_metrics).to_csv(OUT/'proxy_metrics.csv',index=False)
    pd.DataFrame(calibrations).to_csv(OUT/'calibration_slopes.csv',index=False)
    x=inputs('current'); stages=[]
    stages.append(('all_direct_off',[]))
    switches=[]
    for mechanism in ['collateral','guarantee','unsecured','cure','timing','cost']:
        switches=switches+[mechanism]; stages.append((mechanism,switches))
    last=None; contributions=[]; paired={}
    for label,enabled in stages:
        mu,_,_=integrate(x,draws=1024,seed=2026092502,enabled=enabled)
        paired[label]=mu
        delta=np.zeros(len(x)) if last is None else mu-last
        for segment in ['all',*sorted(x.collateral_type.unique())]:
            mask=np.ones(len(x),dtype=bool) if segment=='all' else x.collateral_type.eq(segment).to_numpy()
            contributions.append(dict(step=label,segment=segment,n=int(mask.sum()),
                mean_lgd=float(mu[mask].mean()),increment=float(delta[mask].mean())))
        last=mu
        print('mechanism',label,'complete',flush=True)
    assert np.allclose(sum(paired[b]-paired[a] for (a,_),(b,_) in zip(stages[:-1],stages[1:])),
                       paired['cost']-paired['all_direct_off'],atol=1e-12)
    restored=x.copy()
    restored['security_quality']=np.where(x.collateral_type.eq('Unsecured'),0,np.minimum(1,x.security_quality+.1*x.downturn_at_default))
    restored['guarantor_strength']=np.where(x.guarantee_coverage.eq(0),0,np.minimum(1,x.guarantor_strength+.12*x.downturn_at_default))
    quality_mu,_,_=integrate(restored,draws=1024,seed=2026092502,enabled=[])
    contributions.append(dict(step='quality_restoration_sensitivity',segment='all',n=len(x),
        mean_lgd=float(quality_mu.mean()),increment=float((quality_mu-paired['all_direct_off']).mean())))
    pd.DataFrame(contributions).to_csv(OUT/'mechanism_contributions.csv',index=False)
    # Reuse audited, unchanged PD/EAD/stage path from the preceding full-system run.
    trace=pd.read_csv(ROOT/'research_diagnostics/s1_resolution/results/facility_ecl_shadows.csv')
    predictions=pd.read_csv(OUT/'current_predictions.csv')
    merged=trace.merge(predictions,on='facility_id',validate='one_to_one').merge(x[['facility_id','collateral_type','industry','downturn_at_default']],on='facility_id',validate='one_to_one')
    impacts=[]
    for name in predictions.columns[1:]:
        values=merged.effective_pd*merged[name]*merged.ead
        for field in ['all','stage','collateral_type','industry','downturn_at_default']:
            grouping=[('all',merged.index)] if field=='all' else merged.groupby(field).groups.items()
            for segment,idx in grouping:
                total=float(values.loc[idx].sum()); old=float(merged.loc[idx,'ecl'].sum())
                impacts.append(dict(model=name,field=field,segment=str(segment),n=len(idx),ecl=total,delta=total-old))
        by_borrower=pd.DataFrame({'id':merged.borrower_id,'ecl':values}).groupby('id').ecl.sum().sum()
        assert np.isclose(by_borrower,values.sum(),atol=1e-7,rtol=1e-12)
    pd.DataFrame(impacts).to_csv(OUT/'ecl_impacts.csv',index=False)
    aligned=x.set_index('facility_id').loc[merged.facility_id]
    control=scenario_control(calibrator,merged.governed,aligned.collateral_type,merged.effective_pd,merged.ead,
        scenario='downturn',source='S1 development-fitted research regime calibration; declared adverse scenario, no inferred state',
        run_id='downturn-resolution-4a9599f')
    (OUT/'scenario_control.json').write_text(json.dumps(control)+'\n')
    assert np.allclose(control['base_ecl'],merged.ecl,atol=1e-7)
    (OUT/'manifest.json').write_text(json.dumps(dict(baseline='4a9599f',
        artifacts_sha256=sha(OUT/'research_calibration.joblib'),
        source_sha256=sha(__file__),status='RESEARCH/SCENARIO SENSITIVITY ONLY; NO PROMOTION',
        retained_two_stage='Original R2 published predictions retained; no serialized model exists; no retrain'),indent=2)+'\n')
    print(pd.DataFrame(metrics).query("cohort=='current' and group in ['all','normal','downturn']")[[
        'model','group','n','model_bias','conditional_rmse']].to_string(index=False))


if __name__=='__main__': main()
