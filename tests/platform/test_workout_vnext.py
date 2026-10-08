import copy,json
import pandas as pd
import pytest
from sqlalchemy import create_engine,select
from sqlalchemy.exc import IntegrityError
from test_platform import db,clients,sample,create_run
from workout_vnext.store import migrate,load,asof,EVENTS
from workout_vnext.contracts import check
from workout_vnext.generate import DATA

def test_bitemporal_store_and_transaction(tmp_path):
    from credit_platform.db import engine
    d=engine('sqlite:///'+str(tmp_path/'workout.db'))
    b={'id':'B','industry':'Retail','source':'test'}
    f={'id':'F','borrower_id':'B','product':'Term Loan','principal':100,'predefault_interest':1,'rate':.05,'source':'test'}
    late={'id':'late','facility_id':'F','effective_date':'2020-01-01','recorded_at':'2020-02-01','source':'test','amount':50,'payload':{}}
    load(d,{'borrower':[b],'facility':[f],'collateral_valuation':[late]});migrate(d)
    with d.connect() as c:
        assert asof(c,'F','2020-01-15')['collateral_valuation']==[]
        assert asof(c,'F','2020-02-01')['collateral_valuation'][0]['amount']==50
        with pytest.raises(ValueError):asof(c,'unknown','2020-02-01')
    with pytest.raises(IntegrityError):load(d,{'recovery_transaction':[{**late,'id':'orphan','facility_id':'missing'}]})
    with d.connect() as c:assert c.execute(select(EVENTS['recovery_transaction'])).all()==[]

@pytest.mark.parametrize('field,value',[('ead',0),('rate',-1),('predefault_pd',1.1),('guarantee_ratio',2),('collateral_ratio',-1),('age',float('nan')),('product','invented'),('industry','unknown'),('claim',True)])
def test_contract_rejects(field,value):
    x=pd.read_csv(DATA/'development_inputs.csv.gz',nrows=1);x[field]=value
    with pytest.raises(ValueError):check(x)

def test_frozen_ledger_independent_reconciliation():
    from workout_vnext.experiment import OUT,verify
    verify();report=json.loads((OUT/'ledger_audit.json').read_text())
    assert report['observations']==31815
    assert report['maximum_target_error']<1e-8
    assert report['open_observations_without_target']>0
    assert report['split_borrowers']=={'development':4800,'validation':1600,'final':1600}

@pytest.mark.parametrize('question',['Portfolio totals','Borrower and facility counts','EAD and ECL','Stage distribution','Which industries deserve attention?','Watchlist','Deteriorated most','Unsecured exposure','Guarantee support','Top-risk cases'])
def test_cockpit_copilot_one_source(clients,question):
    c,h=clients;d=sample();d['facilities'].append({**d['facilities'][0],'id':'F2'})
    rid=create_run(c,h,d).json()['id']
    p=c.get(f'/api/v1/runs/{rid}/portfolio',headers=h['analyst']).json()
    r=c.post('/api/v1/copilot/query',headers=h['analyst'],json={'question':question,'use_case':'portfolio','run_id':rid}).json()
    assert r['facts']==p
    assert p['borrower_count']==1 and p['facility_count']==2
    for group in ['by_stage','by_industry','by_product','by_rating','by_risk_direction']:
        assert sum(v['ead'] for v in p[group].values())==pytest.approx(p['ead'])
        assert sum(v['ecl'] for v in p[group].values())==pytest.approx(p['ecl'])
    assert p['unsecured']['ead']<=p['ead'] and p['guaranteed']['ead']<=p['ead']
    assert c.get('/api/v1/audit/verify',headers=h['audit']).json()['status']=='VERIFIED'

def test_workout_evidence_auth_grounding(clients):
    c,h=clients
    assert c.get('/api/v1/lgd-workout-validation').status_code==401
    p=c.get('/api/v1/lgd-workout-validation',headers=h['validator']).json()[0]
    r=c.post('/api/v1/copilot/query',headers=h['validator'],json={'question':'Explain WN-1 workout limitations','use_case':'model_risk'}).json()
    assert r['facts']['workout_lgd']==p['evidence']
    assert r['sources']==[p['source']]
    assert 'BLOCKED' in r['answer']

def test_external_unsubstantiated_narrative_falls_back(monkeypatch):
    from credit_platform.copilot import ExternalJSONProvider,DeterministicProvider
    monkeypatch.setenv('COPILOT_ALLOW_EXTERNAL','true');monkeypatch.setenv('COPILOT_EXTERNAL_ENDPOINT','https://example.invalid');monkeypatch.setenv('COPILOT_EXTERNAL_API_KEY','test-not-secret')
    class Reply:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,*a):return b'{"answer":"Bank-approved. Losses are zero."}'
    monkeypatch.setattr('credit_platform.copilot.urlopen',lambda *a,**k:Reply())
    facts={'workout_lgd':{'decision':{'status':'NOT_PROMOTED','calibration_failures':['all']}}}
    assert ExternalJSONProvider().render('explain',facts,'model_risk')==DeterministicProvider().render('explain',facts,'model_risk')

def test_invalid_observation_date_rejected(tmp_path):
    from credit_platform.db import engine
    d=engine('sqlite:///'+str(tmp_path/'dates.db'));migrate(d)
    with d.connect() as c:
        with pytest.raises(ValueError):asof(c,'F','2020-02-31')

def test_incomplete_versioned_schema_rejected(tmp_path):
    from credit_platform.db import engine
    from sqlalchemy import text
    d=engine('sqlite:///'+str(tmp_path/'schema.db'));migrate(d)
    with d.begin() as c:c.execute(text('DROP TABLE wn_guarantee_claim'))
    with pytest.raises(ValueError,match='Incomplete workout schema'):migrate(d)
