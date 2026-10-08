"""Full existing-portfolio reference execution. Does not deploy WN challenger."""
import json,os,time
import pandas as pd
import numpy as np
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from fastapi.testclient import TestClient
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss,roc_curve
from credit_platform import service,security,schema,audit,governance
from credit_platform.db import engine
from credit_platform.api import create_app
from credit_platform.cli import map_reference
from credit_platform.domain import RunInput
from .generate import HERE,dump

def main():
    command.upgrade(Config('alembic.ini'),'head');db=engine();token=security.issue(db,'wn-closeout-check','analyst')
    with db.connect() as c:actor=c.execute(select(schema.principals.c.id).where(schema.principals.c.name=='wn-closeout-check')).scalar_one()
    d=service.ingest(db,map_reference(),actor);run=service.execute(db,RunInput(dataset_id=d['id'],request_key='wn-closeout-check'),actor)
    assert run['status']=='SUCCEEDED',run
    with db.connect() as c:t=service.traces(c,run['id']);p=service.portfolio(c,run['id']);a=audit.verify(c)
    old=pd.read_csv('outputs/facility_ecl_predictions.csv').set_index('facility_id');b=pd.read_csv('outputs/borrower_audit_trace.csv').set_index('customer_id')
    maxima={'ead':0.,'ecl':0.,'lgd':0.,'pd':0.};stages=0
    for row in t:
        previous=old.loc[row['facility_id']]
        for key,field in [('ead','ead_at_default'),('ecl','facility_ecl'),('lgd','predicted_lgd')]:maxima[key]=max(maxima[key],abs(row[key]-previous[field]))
        maxima['pd']=max(maxima['pd'],abs(row['pit_pd']-b.loc[row['borrower_id'],'predicted_pd']))
        stages+=int(row['stage']!=previous.stage)
    assert maxima['ead']<.011 and maxima['ecl']<.011 and maxima['pd']<1e-12 and maxima['lgd']<1e-12 and stages==0
    client=TestClient(create_app(db));headers={'Authorization':'Bearer '+token};checks=[]
    for question in ['Portfolio totals','Borrower counts','Facility counts','Stage distribution','Industry attention','Watchlist','Unsecured exposure','Guarantees','Top risk cases','Which borrowers deteriorated most?']:
        r=client.post('/api/v1/copilot/query',headers=headers,json={'question':question,'use_case':'portfolio','run_id':run['id']});assert r.status_code==200,r.text;assert r.json()['facts']==p
        checks.append({'question':question,'exact_cockpit_evidence_match':True,'status':r.json()['status']})
    governance.seed(db,actor)
    with db.connect() as c:verified_audit=audit.verify(c)
    result={'run_id':run['id'],'dataset_hash':d['hash'],'portfolio':p,'max_historical_difference':maxima,'stage_mismatches':stages,'audit':verified_audit,'copilot_question_suite':checks,'note':'Reference scorer unchanged; historical face/EAD rounding allows <1.1 cents.'}
    dump(HERE/'release/platform_reconciliation.json',result)
    # Discrimination here is a current independently recalculated reporting check,
    # not refitting, calibration or deployment approval.
    if 'default_flag' in b:target='default_flag'
    elif 'default' in b:target='default'
    else:target=None
    if target:
        y=b[target];pred=b.predicted_pd;fpr,tpr,_=roc_curve(y,pred)
        dump(HERE/'release/pd_metrics.json',{'n':len(b),'target':target,'auc':roc_auc_score(y,pred),'gini':2*roc_auc_score(y,pred)-1,'ks':max(tpr-fpr),'brier':brier_score_loss(y,pred),'log_loss':log_loss(y,pred),'observed_rate':float(y.mean()),'predicted_mean':float(pred.mean()),'scope':'historical holdout borrower output; PIT reporting predictions'})
    else:dump(HERE/'release/pd_metrics.json',{'status':'target not present; no invented metric','columns':list(b)})
    print(json.dumps({'facilities':p['facility_count'],'borrowers':p['borrower_count'],'ead':p['ead'],'ecl':p['ecl'],'maxima':maxima,'audit':verified_audit}))
if __name__=='__main__':main()
