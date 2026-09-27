"""Gate decisions recalculated from frozen prediction/validation files, never fit."""
import json
import numpy as np
import pandas as pd
from credit_platform.common import ROOT,atomic_json,file_hash
from .evaluate import OUT,verify,verify_lock
from .model import VERSION


def equivalence(row,tolerance):
    return bool(np.isfinite(row.equivalence_se) and
        abs(row.conditional_bias)+1.96*row.equivalence_se<=tolerance)


def main():
    verify(); verify_lock()
    frames={name:pd.read_csv(OUT/f'{name}_metrics.csv') for name in ['current','promotion']}
    evidence=[]
    for cohort,metrics in frames.items():
        predictions=pd.read_csv(OUT/f'{cohort}_predictions.csv')
        # Independent arithmetic from the saved predictions, including squared
        # errors; do not rely solely on production/evaluation summary functions.
        for scenario,rows in predictions.groupby('scenario'):
            for model in ['incumbent','original_s2','corrected']:
                summary=metrics[(metrics.scenario==scenario)&(metrics.model==model)&(metrics.group=='all')].iloc[0]
                residual=rows[model]-rows.actual
                for field,value in [('bias',residual.mean()),('mae',residual.abs().mean()),
                                    ('rmse',np.sqrt((residual**2).mean())),
                                    ('conditional_bias',(rows[model]-rows.conditional_mean).mean())]:
                    if abs(summary[field]-value)>1e-12: raise ValueError('Independent metric mismatch')
        for _,r in metrics.iterrows():
            evidence.append(dict(cohort=cohort,model=r.model,group=r.group,scenario=r.scenario,n=int(r.n),
                bias_pp=r.conditional_bias*100,realized_bias_pp=r.bias*100,
                mae_pp=r.mae*100,rmse_pp=r.rmse*100,
                ci95_low_pp=r.ci95_low*100,ci95_high_pp=r.ci95_high*100))
    allrows=pd.concat(frames.values(),ignore_index=True)
    candidate=allrows[allrows.model=='corrected']
    checks=[]
    for _,r in candidate.iterrows():
        gate=None; tolerance=None
        if r.group=='all':
            gate='current_calibration' if r.scenario=='baseline' else 'scenario_calibration'
            tolerance=.01
        elif r.group in ['guarantee:zero','guarantee:partial','guarantee:full']:
            gate='guarantees';tolerance=.02
        elif r.group in ['regime:0','regime:1']:
            gate='general_performance';tolerance=.01
        elif r.n>=100 and not r.group.startswith(('reporting_date:','realized_gt:')):
            gate='general_performance';tolerance=.02
        if gate:
            checks.append(dict(gate=gate,cohort=r.cohort,scenario=r.scenario,group=r.group,
                n=int(r.n),bias_pp=r.conditional_bias*100,
                bound_pp=(abs(r.conditional_bias)+1.96*r.equivalence_se)*100,
                tolerance_pp=tolerance*100,
                passed=equivalence(r,tolerance) and (r.n>=100 if gate=='guarantees' else True)))
    for scenario in ['upside','baseline','downside']:
        frame=frames['promotion']
        frame=frame[(frame.scenario==scenario)&(frame.group=='all')].set_index('model')
        for metric in ['mae','rmse']:
            checks.append(dict(gate='general_performance',cohort='promotion',scenario=scenario,
                group=metric,passed=bool(frame.loc['corrected',metric]<=frame.loc['original_s2',metric]),
                original=float(frame.loc['original_s2',metric]),final=float(frame.loc['corrected',metric])))
    shapes={c:json.loads((OUT/f'{c}_shape.json').read_text()) for c in frames}
    supports={c:pd.read_csv(OUT/f'{c}_support.csv') for c in frames}
    for cohort in frames:
        shape=next(r for r in shapes[cohort] if r['model']=='corrected')
        checks.append(dict(gate='scenario_consistency',cohort=cohort,**shape,passed=shape['count']==0))
        for scenario,g in supports[cohort].groupby('scenario'):
            checks.append(dict(gate='model_support',cohort=cohort,scenario=scenario,
                rejected=int((~g.supported).sum()),outside_range=int(g.outside_macro_range.sum()),
                passed=bool(g.supported.all())))
    ecl=json.loads((OUT/'ecl_reconciliation.json').read_text())
    checks.append(dict(gate='ecl',passed=ecl['max_facility_error']<=1e-7 and ecl['aggregation_error']<=1e-6))
    # Engineering signoff is a separate post-test artifact, never presumed green.
    signoff=OUT/'engineering.json'
    engineering=json.loads(signoff.read_text()) if signoff.exists() else {'passed':False,'reason':'Full-suite signoff pending'}
    checks.append(dict(gate='engineering_governance',**engineering))
    gates={name:all(r['passed'] for r in checks if r['gate']==name)
           for name in sorted({r['gate'] for r in checks})}
    failed=[r for r in checks if not r['passed']]
    status='PROMOTED_SYNTHETIC_REFERENCE' if all(gates.values()) else 'CHALLENGER_NOT_PROMOTED'
    deficiencies=[f"{r['gate']}: {r.get('cohort','')} {r.get('scenario','')} {r.get('group','')} "+
        (f"equivalence bound {r['bound_pp']:.3f} pp exceeds {r['tolerance_pp']:.2f} pp" if 'bound_pp' in r else
         f"rejected={r['rejected']}" if 'rejected' in r else 'acceptance check failed') for r in failed]
    atomic_json(OUT/'gate_checks.json',checks)
    sources={str(p.relative_to(ROOT)):file_hash(p) for p in sorted(OUT.glob('*.csv'))}
    for name in ['gate_checks.json','ecl_reconciliation.json','current_shape.json','promotion_shape.json','LOCK.json']:
        sources[str((OUT/name).relative_to(ROOT))]=file_hash(OUT/name)
    if signoff.exists(): sources[str(signoff.relative_to(ROOT))]=file_hash(signoff)
    decision=dict(model_version=VERSION,status=status,bank_gate='BLOCKED',gates=gates,
        remaining_deficiencies=deficiencies+['Synthetic recovery truth; unavailable institutional validation and operational qualification'],
        metrics=evidence,source_hashes=sources,ecl=ecl,
        historical_decision='economic_lgd/results/decision.json',
        comparison='Same frozen S2-R1 holdout; current S2 is known diagnostic evidence',
        moc=0,calibration_overlay=None)
    atomic_json(OUT/'decision.json',decision)
    atomic_json(OUT/'registry.json',dict(model_id=VERSION,status=status,bank_gate='BLOCKED',
        artifact_sha256=file_hash(OUT/'model.joblib'),data_sha256=file_hash(ROOT/'s2_remediation/data/manifest.json'),
        gates=gates,decision_sha256=file_hash(OUT/'decision.json')))
    print(json.dumps({'status':status,'gates':gates,'failures':failed},indent=2),flush=True)


if __name__=='__main__': main()
