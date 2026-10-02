"""Read-only historical evidence checks plus isolated reference execution.

Writes only final_red_team_evidence; does not fit models or regenerate data.
"""
import json
import math
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss, log_loss
from credit_platform import service, security, schema, audit
from credit_platform.cli import map_reference
from credit_platform.db import engine
from credit_platform.domain import RunInput
from credit_platform.common import ROOT, file_hash
from s2_remediation.evaluate import verify, verify_lock


def main():
    out = ROOT / 'final_red_team_evidence'
    out.mkdir(exist_ok=True)
    verify(); verify_lock()
    report = {'historical_r1_hashes': 'VERIFIED', 'new_final_holdout_opened': False,
              'models_fitted': False, 'bank_gate': 'BLOCKED'}
    historical = pd.read_csv(ROOT / 'outputs/borrower_audit_trace.csv')
    y, p = historical['default'], historical.predicted_pd
    fpr, tpr, _ = roc_curve(y, p)
    auc = roc_auc_score(y, p)
    report['pd'] = dict(n=len(y), defaults=int(y.sum()), observed_default_rate=float(y.mean()),
                       predicted_mean=float(p.mean()), auc=float(auc), gini=float(2*auc-1),
                       ks=float(max(tpr-fpr)), brier=float(brier_score_loss(y,p)),
                       log_loss=float(log_loss(y,p)))
    rows=[]
    for cohort in ('current','promotion'):
        frame=pd.read_csv(ROOT/f's2_remediation/results/{cohort}_predictions.csv')
        for scenario,g in frame.groupby('scenario'):
            for model in ('incumbent','original_s2','corrected'):
                for name, subset in [('all',g),('realized_gt75',g[g.actual>.75]),
                                     ('predicted_80_100',g[g[model]>=.8]),
                                     ('full_guarantee',g[g.guarantee_coverage>=1])]:
                    e=subset[model]-subset.actual
                    rows.append(dict(cohort=cohort,scenario=scenario,model=model,group=name,n=len(subset),
                        mae_pp=float(e.abs().mean()*100),rmse_pp=float(np.sqrt((e**2).mean())*100),
                        realized_bias_pp=float(e.mean()*100),
                        conditional_bias_pp=float((subset[model]-subset.conditional_mean).mean()*100)))
    pd.DataFrame(rows).to_csv(out/'lgd_independent_metrics.csv',index=False)
    ecl=pd.read_csv(ROOT/'s2_remediation/results/scenario_ecl.csv')
    independent=.2*ecl.ecl_upside+.6*ecl.ecl_baseline+.2*ecl.ecl_downside
    err=float((independent-ecl.corrected_ecl).abs().max())
    assert err<1e-7
    report['r1_ecl']={'max_weighting_error':err,'portfolio':float(independent.sum()),
                     'borrower_aggregation_error':float(abs(ecl.groupby('borrower_id').corrected_ecl.sum().sum()-ecl.corrected_ecl.sum()))}
    with tempfile.TemporaryDirectory(prefix='credit-red-team-') as tmp:
        os.environ['DATABASE_URL']='sqlite:///'+tmp+'/review.db'
        command.upgrade(Config(str(ROOT/'alembic.ini')),'head')
        db=engine()
        security.issue(db,'red-team-operator','analyst')
        with db.connect() as c:
            actor=c.scalar(select(schema.principals.c.id))
        d=service.ingest(db,map_reference(),actor)
        r=service.execute(db,RunInput(dataset_id=d['id'],request_key='independent-red-team'),actor)
        assert r['status']=='SUCCEEDED',r
        with db.connect() as c:
            traces=service.traces(c,r['id'])
            chain=audit.verify(c)
        errors={'ead':0.,'scenario_pd':0.,'ecl':0.}
        stage_mismatches=rating_mismatches=0
        scenarios=r['versions']['configuration']['scenarios']
        baseline=next(x for x in scenarios if x['scenario']=='baseline')
        cases={}
        for t in traces:
            f=t['source_facility']; b=t['source_borrower']['features']
            expected_ead=(f['drawn'] if f['product']=='Term Loan' else f['limit'] if f['product']=='OVD'
                          else round(f['face']*{'Import LC':.2,'Performance Guarantee':.5,'Financial Guarantee':1}[f['product']]*100)/100)
            signals=sum([b['utilization_6m_change']>=.1,b['avg_utilization_6m']>=.8 or b['months_above_80_utilization']>=3,b['limit_breach_count']>=1])
            stage=('Stage 3' if b['current_credit_impaired']==1 or b['days_past_due']>=90 else
                   'Stage 2' if b['days_past_due']>=30 or b['delinquencies_12m']>=2 or
                   (b['credit_utilization']>=.85 and b['days_past_due']>0) or
                   (b['previous_defaults']>=1 and t['pit_pd']>=.05) or
                   (signals>=2 and b['consecutive_ews_months']>=9) else 'Stage 1')
            stage_mismatches+=stage!=t['stage']
            pit=max(1e-8,min(1-1e-8,t['pit_pd']))
            weighted=0
            for sc in scenarios:
                shift=sum(beta*(sc[key]-baseline[key]) for key,beta in {
                    'real_gdp_growth_pct':-.1,'unemployment_rate_pct':.08,'policy_rate_pct':.06,'inflation_pct':.03}.items())
                odds=pit/(1-pit)*math.exp(shift)
                weighted+=sc['weight']*odds/(1+odds)
            effective=1 if stage=='Stage 3' else 1-(1-weighted)**(f['remaining_months']/12) if stage=='Stage 2' else weighted
            expected=effective*t['lgd']*expected_ead
            errors['ead']=max(errors['ead'],abs(expected_ead-t['ead']))
            errors['scenario_pd']=max(errors['scenario_pd'],abs(weighted-t['pd']))
            errors['ecl']=max(errors['ecl'],abs(expected-t['ecl']))
            rating=next((i for i,cut in [(2,.005),(3,.01),(4,.02),(5,.04)] if t['pit_pd']<=cut),6)
            if signals>=2 or stage=='Stage 2':rating=7
            if stage=='Stage 3':rating=10 if b['write_off_flag'] else 9 if b['days_past_due']>=120 else 8
            if stage=='Stage 1' and t['source_borrower']['collateral_type']=='Cash' and b['recognized_collateral_coverage']>=.999:rating=1
            rating_mismatches+=rating!=t['risk_rating']
            cases.setdefault(stage,t)
            if t['watchlist']:cases.setdefault('Watchlist',t)
        assert stage_mismatches==rating_mismatches==0
        assert errors['ead']<1e-9 and errors['scenario_pd']<1e-12 and errors['ecl']<1e-7, errors
        report['reference']={'run_id':r['id'],'dataset_hash':d['hash'],'facility_count':len(traces),
            'max_errors':errors,'stage_mismatches':stage_mismatches,'rating_mismatches':rating_mismatches,
            'portfolio_ecl':math.fsum(t['ecl'] for t in traces),'audit':chain,'versions':r['versions']}
        (out/'worked_cases.json').write_text(json.dumps(cases,indent=2))
        db.dispose()
    report['input_hashes']={p:file_hash(ROOT/p) for p in [
        'outputs/borrower_audit_trace.csv','s2_remediation/results/current_predictions.csv',
        's2_remediation/results/promotion_predictions.csv','s2_remediation/results/scenario_ecl.csv']}
    (out/'independent_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('reference','input_hashes')},indent=2))
    print('Reference facilities:',report['reference']['facility_count'],'errors:',errors)

if __name__=='__main__':main()
