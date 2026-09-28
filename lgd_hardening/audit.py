"""Reconcile known evidence and distinguish bias, uncertainty and hidden lineage."""
import json
import math
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,atomic_json,file_hash
from s2_remediation.evaluate import verify,verify_lock
from economic_lgd.recovery import conditional

OUT=ROOT/'lgd_hardening/results'


def main():
    verify();verify_lock()
    OUT.mkdir(exist_ok=True)
    sources={};rows=[];power=[];lineage=[]
    for cohort in ['current','promotion']:
        directory=ROOT/'s2_remediation/results'
        pp=directory/f'{cohort}_predictions.csv';sp=directory/f'{cohort}_support.csv'
        fp=ROOT/('economic_lgd/data/current_inputs.csv.gz' if cohort=='current'
                 else 's2_remediation/data/promotion_inputs.csv.gz')
        for p in [pp,sp,fp]: sources[str(p.relative_to(ROOT))]=file_hash(p)
        pred=pd.read_csv(pp);support=pd.read_csv(sp);features=pd.read_csv(fp)
        data=pred.merge(support[['facility_id','scenario','supported']],on=['facility_id','scenario'],validate='one_to_one')
        fields=['facility_id','output_growth_pct','unemployment_pct','collateral_change_pct','liquidity',
                'security_quality','guarantor_strength']
        data=data.merge(features[fields],on='facility_id',validate='many_to_one')
        for scenario,g in data.groupby('scenario'):
            for lo in [0,.2,.4,.6,.8]:
                band=g[g.corrected.between(lo,lo+.2,inclusive='left')]
                if band.empty:continue
                clusters=band.groupby(['industry','reporting_date'])
                rows.append(dict(cohort=cohort,scenario=scenario,band=lo,n=len(band),
                    clusters=clusters.ngroups,prediction=band.corrected.mean(),actual=band.actual.mean(),
                    conditional=band.conditional_mean.mean(),
                    expected_error=(band.corrected-band.conditional_mean).mean(),
                    realization_component=(band.conditional_mean-band.actual).mean(),
                    support_failures=int((~band.supported).sum()),
                    collateral=band.collateral_type.value_counts().to_json(),
                    guarantees=band.guarantee_coverage.value_counts().sort_index().to_json(),
                    products=band.product_type.value_counts().to_json(),
                    industries=band.industry.value_counts().to_json(),
                    regimes=band.latent_regime.value_counts().to_json()))
        mp=directory/f'{cohort}_metrics.csv';sources[str(mp.relative_to(ROOT))]=file_hash(mp)
        metrics=pd.read_csv(mp)
        for _,m in metrics.query("model=='corrected'").iterrows():
            if m.group not in ['all','guarantee:full','predicted:0.8']:continue
            tolerance=.01 if m.group=='all' else .02
            margin=tolerance-abs(m.conditional_bias)
            # Planning illustration only: independent economic clusters, not rows.
            se=m.conditional_bias_se
            required=math.ceil(m.macro_clusters*(1.96*se/margin)**2) if margin>0 and np.isfinite(se) else None
            power.append(dict(cohort=cohort,scenario=m.scenario,group=m.group,
                bias=m.conditional_bias,tolerance=tolerance,current_clusters=int(m.macro_clusters),
                illustrative_required_clusters=required,
                classification='MODEL BIAS: sample size cannot fix' if margin<=0 else
                'PRECISION POSSIBLE ONLY WITH NEW INDEPENDENT ECONOMIES; stationarity unproven'))
        original=pd.read_csv(ROOT/f"synthetic_bank/data/{'current' if cohort=='current' else 'final'}/facilities.csv.gz")
        original=original.set_index('facility_id')
        key=features.facility_id if cohort=='current' else features.source_facility_id
        joined=original.loc[key]
        for field in ['security_quality','guarantor_strength']:
            diff=np.max(np.abs(features[field].to_numpy()-joined[field].to_numpy()))
            if diff>1e-12:raise ValueError('Imported quality lineage mismatch')
        for state in [0,1]:
            mask=joined.downturn_at_default.to_numpy()==state
            lineage.append(dict(cohort=cohort,original_s1_state=state,n=int(mask.sum()),
                security_mean=float(features.loc[mask,'security_quality'].mean()),
                guarantor_mean=float(features.loc[mask & (features.guarantee_coverage>0),'guarantor_strength'].mean()),
                quality_fields_copied_exactly=True))
    pd.DataFrame(rows).to_csv(OUT/'band_diagnosis.csv',index=False)
    pd.DataFrame(power).to_csv(OUT/'precision_planning.csv',index=False)
    pd.DataFrame(lineage).to_csv(OUT/'quality_lineage.csv',index=False)
    # New focused sensitivity: hold every scoring feature fixed, vary only the
    # existing S1 quality shift. This is not an oracle model or a fitted feature.
    development=pd.read_csv(ROOT/'s2_remediation/data/development_inputs.csv.gz').drop_duplicates('source_facility_id')
    sample=development[development.guarantee_coverage.eq(1)].head(256).copy()
    weaker=sample.copy()
    weaker['security_quality']=(weaker.security_quality-.10).clip(.05,1)
    weaker.loc[weaker.collateral_type.eq('Unsecured'),'security_quality']=0
    weaker['guarantor_strength']=(weaker.guarantor_strength-.12).clip(.02,1)
    a,_=conditional(sample,draws=2048,seed=108001)
    b,_=conditional(weaker,draws=2048,seed=108001)
    out=sample[['facility_id','collateral_type','guarantee_coverage']].copy()
    out['conditional_original']=a;out['conditional_shifted_quality']=b;out['shift']=b-a
    out.to_csv(OUT/'quality_sensitivity.csv',index=False)
    summary=dict(baseline='14b8c4db691c8f795c27501b7237442426eb70b2',
        sources=sources,quality_shift_mean_pp=float(100*(b-a).mean()),
        paired_development_cases=len(sample),
        interpretation='Conditional sensitivity only; not a real-bank causal estimate or proof every residual is unfixable',
        final_holdout_generated=False,final_holdout_opened=False,
        limitation='S2 direct state excluded, but imported S1 quality retains a distinct original latent-state pathway')
    atomic_json(OUT/'baseline_audit.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
