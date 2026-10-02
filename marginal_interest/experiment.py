"""MI-1 prospective research only. No production imports with write side effects."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from economic_lgd.model import NUMERIC
from economic_lgd.economics import MACRO, scenario_frame
from economic_lgd.recovery import simulate, BUCKETS
from src.lgd_model import CATEGORICAL_FEATURES
from s2_remediation.model import SIGNS
from s2_remediation.support import Support

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'marginal_interest'
DATA=HERE/'data'; OUT=HERE/'results'
MI=['marginal_interest_amount','marginal_interest_to_principal']
STATE=['cumulative_recovery_ratio','recent_recovery_ratio','months_since_last_recovery','restructured','default_principal']
EXTRA={'M0':[], 'M1':['months_since_default'],'M2':MI,'M3':['months_since_default']+MI,'M4':['months_since_default']+MI+STATE,'M4_without_mi':['months_since_default']+STATE}
SCENARIOS={'upside':{'real_gdp_growth_pct':3.,'unemployment_rate_pct':5.},'baseline':{'real_gdp_growth_pct':2.,'unemployment_rate_pct':6.},'downside':{'real_gdp_growth_pct':0.,'unemployment_rate_pct':8.}}
for _name, _scenario in SCENARIOS.items():
    _scenario['scenario'] = _name
WEIGHTS={'upside':.2,'baseline':.6,'downside':.2}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def writej(p,x): p.write_text(json.dumps(x,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v))+'\n')
def csv(p,x): x.to_csv(p,index=False,float_format='%.12g',compression={'method':'gzip','mtime':0} if str(p).endswith('.gz') else None)
def version(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def sigmoid(x): return 1/(1+np.exp(-x))

def ledger_features(history, observation_month, default_principal, rate):
    """Build only from dated pre-observation events; future rows cannot influence MI."""
    if not np.isfinite([default_principal,rate,observation_month]).all() or default_principal<=0 or rate<0 or observation_month<1:
        raise ValueError('Invalid principal/rate/observation')
    h=history[history.month<=observation_month].sort_values('month')
    if h.month.duplicated().any() or not np.array_equal(h.month.to_numpy(),np.arange(1,observation_month+1)):
        raise ValueError('Incomplete or duplicate ledger')
    balance=default_principal; accrued=0.
    for r in h.itertuples():
        if not np.isfinite(r.payment) or r.payment<0 or r.payment>balance: raise ValueError('Invalid principal payment')
        accrued+=balance*rate/12
        balance-=r.payment
    if balance<=0: raise ValueError('Resolved exposure not eligible for this impaired-observation cohort')
    last=h.loc[h.payment>0,'month'].max()
    return dict(ead_at_default=balance,default_principal=default_principal,
        marginal_interest_amount=accrued,marginal_interest_to_principal=accrued/balance,
        marginal_interest_to_ead=accrued/balance,months_since_default=observation_month,
        cumulative_recovery_ratio=(default_principal-balance)/default_principal,
        recent_recovery_ratio=h.loc[h.month>observation_month-3,'payment'].sum()/default_principal,
        months_since_last_recovery=observation_month if pd.isna(last) else observation_month-last)

def validate_x(x):
    fields=list(dict.fromkeys(NUMERIC+CATEGORICAL_FEATURES+EXTRA['M4']))
    if set(fields)-set(x): raise ValueError('Missing feature fields')
    numeric=list(dict.fromkeys(NUMERIC+EXTRA['M4']))
    if x[fields].isna().any().any() or not np.isfinite(x[numeric].to_numpy(dtype=float)).all(): raise ValueError('Missing/nonfinite features')
    if (x.ead_at_default<=0).any() or (x.interest_rate<0).any() or (x.marginal_interest_amount<0).any(): raise ValueError('Invalid amount')
    if not x.months_since_default.between(1,24).all(): raise ValueError('Invalid age')
    if (pd.to_datetime(x.default_date)>=pd.to_datetime(x.reporting_date)).any(): raise ValueError('Invalid dates')
    if not np.allclose(x.marginal_interest_to_principal,x.marginal_interest_amount/x.ead_at_default): raise ValueError('MI ratio mismatch')
    return x

def features(x,name):
    validate_x(x)
    return x[list(dict.fromkeys(NUMERIC+CATEGORICAL_FEATURES+EXTRA[name]))].copy()

def future(x, latent, seed, draws):
    z=x.copy(); z['current_ratio_at_default']=np.maximum(.05,z.current_ratio_at_default+.6*latent.willingness.to_numpy()+.2*latent.shock.to_numpy())
    rng=np.random.default_rng(seed)
    _,cf=simulate(z,rng,draws=draws,cashflows=True)
    cured=rng.random((len(x),draws))<sigmoid(-2+.5*latent.willingness.to_numpy()+.4*x.restructured.to_numpy())[:,None]
    cure_cf=np.zeros_like(cf); cure_cf[:,:,0]=-.005*x.ead_at_default.to_numpy()[:,None]; cure_cf[:,:,1]=x.ead_at_default.to_numpy()[:,None]
    cf=np.where(cured[:,:,None],cure_cf,cf)
    pv=(cf/(1+x.interest_rate.to_numpy()[:,None,None])**(BUCKETS[None,None,:]/12)).sum(axis=2)
    return np.clip(1-pv/x.ead_at_default.to_numpy()[:,None],0,1),cf,cured

def generate():
    if DATA.exists(): raise ValueError('Frozen data already exists; no regeneration')
    source=ROOT/'s2_remediation/data/development_inputs.csv.gz'
    f=pd.read_csv(source).drop_duplicates('source_facility_id').copy()
    rng=np.random.default_rng(10102026); borrowers=np.array(sorted(f.customer_id.unique())); rng.shuffle(borrowers); borrowers=borrowers[:12000]
    cuts=[0,int(.6*len(borrowers)),int(.8*len(borrowers)),len(borrowers)]
    DATA.mkdir(); manifest={'generator_commit':version(),'version':'MI-1','source_sha256':sha(source),'historical_data_modified':False,'pd_rating_control':'Absent in source borrower schema; financial proxies retained; no invented PD/rating','cohorts':{},'files':{}}
    for k,(split,start,quarters) in enumerate([('development','2000-01-01',32),('validation','2011-01-01',12),('final','2017-01-01',12)]):
        seed=10102027+k; rng=np.random.default_rng(seed)
        x=f[f.customer_id.isin(borrowers[cuts[k]:cuts[k+1]])].sort_values('source_facility_id').reset_index(drop=True)
        ids=sorted(x.customer_id.unique()); dates=pd.date_range(start,periods=quarters,freq='QS')
        bd={b:rng.choice(dates) for b in ids}; age={b:int(rng.integers(1,25)) for b in ids}; will={b:rng.normal() for b in ids}; shock={str(d):rng.normal(0,.4) for d in dates}
        histories=[]; rows=[]; latent=[]
        for row in x.to_dict('records'):
            b=row['customer_id']; d=pd.Timestamp(bd[b]); a=age[b]; w=will[b]; s=shock[str(d)]
            e=row['ead_at_default']; bal=e; h=[]
            for m in range(1,a+1):
                pay=bal*rng.uniform(.005,.045) if rng.random()<sigmoid(-1.5+w+.4*s) else 0.
                h.append({'month':m,'payment':pay}); histories.append({'facility_id':row['source_facility_id'],'month':m,'payment':pay,'event_date':str((d+pd.DateOffset(months=m)).date())}); bal-=pay
            row.update(ledger_features(pd.DataFrame(h),a,e,row['interest_rate']))
            row['collateral_coverage']*=e/bal; row['guarantee_coverage']=min(1,row['guarantee_coverage']*e/bal)
            row['facility_id']=row['source_facility_id']; row['default_date']=str(d.date()); obs=d+pd.DateOffset(months=a)
            row['reporting_date']=str(obs.date()); row['published_at']=str((obs-pd.Timedelta(days=1)).date()); row['economic_period']=str((obs-pd.Timedelta(days=90)).date())
            row['restructured']=int(rng.random()<sigmoid(-1+.3*w)); row['stage']=3; row['pd']=1.; row['cluster']=row['industry']+'|'+str(obs.to_period('Q'))
            rows.append(row); latent.append(dict(willingness=w,shock=s))
        x=validate_x(pd.DataFrame(rows)); latent=pd.DataFrame(latent)
        csv(DATA/f'{split}_inputs.csv.gz',x); csv(DATA/f'{split}_ledger.csv.gz',pd.DataFrame(histories))
        outcomes=[]
        for scenario in SCENARIOS:
            sx=scenario_frame(x,SCENARIOS[scenario],SCENARIOS['baseline'])
            y,cf,cure=future(sx,latent,seed+100,1)
            # Independent diagnostic draws; no outcomes returned to feature construction.
            means=[]
            for offset in range(0,len(x),256):
                cy,_,_=future(sx.iloc[offset:offset+256],latent.iloc[offset:offset+256],seed+200+offset,128); means.extend(cy.mean(axis=1))
            out=pd.DataFrame({'facility_id':x.facility_id,'scenario':scenario,'actual':y[:,0],'latent_conditional_mean':means,'cure':cure[:,0].astype(int),'resolved_at':[(pd.Timestamp(t)+pd.DateOffset(months=60)).date().isoformat() for t in x.reporting_date]})
            for j,m in enumerate(BUCKETS): out[f'net_cf_{m}m']=cf[:,0,j]
            outcomes.append(out)
        csv(DATA/f'{split}_outcomes.csv.gz',pd.concat(outcomes,ignore_index=True))
        manifest['cohorts'][split]={'facilities':len(x),'borrowers':x.customer_id.nunique(),'seed':seed,'clusters':x.cluster.nunique()}
        print(split,manifest['cohorts'][split],flush=True)
    manifest['files']={p.name:sha(p) for p in DATA.glob('*.gz')}; writej(DATA/'manifest.json',manifest)

def verify_data():
    m=json.loads((DATA/'manifest.json').read_text())
    for file,h in m['files'].items():
        if sha(DATA/file)!=h: raise ValueError('Frozen data hash mismatch: '+file)
    return m

def build(x,name):
    nums=list(dict.fromkeys(NUMERIC+EXTRA[name])); cats=[sorted(x[c].unique()) for c in CATEGORICAL_FEATURES]
    prep=ColumnTransformer([('num','passthrough',nums),('cat',OneHotEncoder(categories=cats,handle_unknown='error',sparse_output=False),CATEGORICAL_FEATURES)])
    signs=[SIGNS.get(c,0) for c in nums]+[0]*sum(map(len,cats))
    return Pipeline([('prep',prep),('model',HistGradientBoostingRegressor(loss='squared_error',max_iter=350,learning_rate=.05,max_leaf_nodes=31,min_samples_leaf=80,l2_regularization=5,random_state=94001,early_stopping=False,monotonic_cst=signs))])

def metrics(y,p):
    e=np.asarray(p)-np.asarray(y)
    return {'n':len(e),'mae':np.abs(e).mean(),'rmse':np.sqrt((e*e).mean()),'bias':e.mean(),'r2':r2_score(y,p) if len(e)>1 else np.nan,'predicted_mean':np.mean(p),'realized_mean':np.mean(y)}

def fit():
    verify_data()
    if OUT.exists(): raise ValueError('Results exist; no refitting')
    OUT.mkdir(); x=pd.read_csv(DATA/'development_inputs.csv.gz'); y=pd.read_csv(DATA/'development_outcomes.csv.gz').query("scenario=='baseline'")
    v=pd.read_csv(DATA/'validation_inputs.csv.gz'); vy=pd.read_csv(DATA/'validation_outcomes.csv.gz').query("scenario=='baseline'")
    assert x.facility_id.tolist()==y.facility_id.tolist() and v.facility_id.tolist()==vy.facility_id.tolist()
    results=[]
    for name in EXTRA:
        model=build(x,name); model.fit(features(x,name),y.actual); joblib.dump(model,OUT/f'{name}.joblib')
        p=np.clip(model.predict(features(v,name)),0,1); results.append({'model':name,**metrics(vy.actual,p)})
        print('validation',name,results[-1]['rmse'],flush=True)
    selected=min([r for r in results if r['model'] in ['M1','M2','M3','M4']],key=lambda r:(r['rmse'],r['model']))['model']
    csv(OUT/'validation_selection.csv',pd.DataFrame(results))
    writej(OUT/'LOCK.json',{'selected':selected,'commit':version(),'data_manifest_sha256':sha(DATA/'manifest.json'),'models':{p.name:sha(p) for p in OUT.glob('*.joblib')},'feature_spec':EXTRA,'final_opened':False})

def boot(y,p,b,groups,seed=10103000):
    """Paired cluster bootstrap over sufficient statistics, preserving cluster sizes."""
    a=np.column_stack([np.abs(p-y),(p-y)**2,p-y,np.abs(b-y),(b-y)**2,b-y,np.ones(len(y))])
    _,idx=np.unique(groups,return_inverse=True); sums=np.zeros((idx.max()+1,7)); np.add.at(sums,idx,a)
    rng=np.random.default_rng(seed); rows=[]
    for _ in range(400):
        z=sums[rng.integers(0,len(sums),len(sums))].sum(axis=0); q=z[:6]/z[6]
        rows.append([q[0]-q[3],np.sqrt(q[1])-np.sqrt(q[4]),q[2],q[2]-q[5],q[5]])
    lo,hi=np.quantile(rows,[.025,.975],axis=0)
    return {n+'_low':lo[j] for j,n in enumerate(['delta_mae','delta_rmse','bias','delta_bias','benchmark_bias'])}|{n+'_high':hi[j] for j,n in enumerate(['delta_mae','delta_rmse','bias','delta_bias','benchmark_bias'])}

def segments(x,y,p):
    yield 'all',np.ones(len(x),dtype=bool)
    for label,mask in [('realized_gt60',y.actual>.6),('realized_gt75',y.actual>.75),('realized_ge90',y.actual>=.9),('low_le10',y.actual<=.1),('cure',y.cure==1),('unsecured',x.collateral_coverage==0),('secured',x.collateral_coverage>0),('guarantee:zero',x.guarantee_coverage==0),('guarantee:partial',(x.guarantee_coverage>0)&(x.guarantee_coverage<1)),('guarantee:full',x.guarantee_coverage==1)]: yield label,np.asarray(mask)
    for c in ['product_type','industry','collateral_type','lien_rank','latent_regime']:
        for v in sorted(x[c].unique()): yield c+':'+str(v),np.asarray(x[c]==v)
    for lo,hi in [(1,6),(7,12),(13,24)]: yield f'age:{lo}-{hi}',np.asarray(x.months_since_default.between(lo,hi))
    for lo,hi in zip([0,.1,.25,.5,.75],[.1,.25,.5,.75,1.000001]): yield f'predicted:{lo}-{min(hi,1)}',(p>=lo)&(p<hi)

def evaluate():
    verify_data(); lock=json.loads((OUT/'LOCK.json').read_text())
    if (OUT/'FINAL_OPENED.json').exists(): raise ValueError('Final already opened; no repeated evaluation')
    for f,h in lock['models'].items():
        if sha(OUT/f)!=h: raise ValueError('Frozen model hash mismatch')
    writej(OUT/'FINAL_OPENED.json',{'commit':version(),'lock_sha256':sha(OUT/'LOCK.json'),'purpose':'single prespecified final opening'})
    dev=pd.read_csv(DATA/'development_inputs.csv.gz'); support=Support().fit(dev)
    mods={n:joblib.load(OUT/f'{n}.joblib') for n in EXTRA}; frozen=joblib.load(ROOT/'s2_remediation/results/model.joblib')
    summary=[]; detail=[]; paired=[]; supports=[]; reversals=[]; predictions=[]; ecl=[]; checks=[]
    for split in ['validation','final']:
        x=pd.read_csv(DATA/f'{split}_inputs.csv.gz'); yy=pd.read_csv(DATA/f'{split}_outcomes.csv.gz'); scenario_preds={}
        for scenario in SCENARIOS:
            sx=scenario_frame(x,SCENARIOS[scenario],SCENARIOS['baseline']); y=yy[yy.scenario==scenario].reset_index(drop=True); assert x.facility_id.tolist()==y.facility_id.tolist()
            ps={n:np.clip(m.predict(features(sx,n)),0,1) for n,m in mods.items()}
            ps['frozen_R1_transfer']=np.clip(frozen.predict(sx),0,1); scenario_preds[scenario]=ps
            sr=support.inspect(sx); sr['split']=split; sr['scenario']=scenario
            newcols=list(dict.fromkeys(EXTRA['M4'])); sr['new_feature_outside_range']=((sx[newcols]<dev[newcols].min())|(sx[newcols]>dev[newcols].max())).any(axis=1).to_numpy(); supports.append(sr)
            for n,p in ps.items():
                summary.append({'split':split,'scenario':scenario,'model':n,**metrics(y.actual,p)})
                pred=x[['facility_id','customer_id','cluster','industry','product_type','ead_at_default','stage','pd']].copy(); pred['split']=split;pred['scenario']=scenario;pred['model']=n;pred['prediction']=p;pred['actual']=y.actual; predictions.append(pred)
                if n=='frozen_R1_transfer': continue
                for label,mask in segments(x,y,p):
                    if not mask.any(): continue
                    a=y.actual.to_numpy()[mask]; z=p[mask]; b=ps['M0'][mask]
                    ci=boot(a,z,b,x.customer_id.to_numpy()[mask])
                    detail.append({'split':split,'scenario':scenario,'model':n,'segment':label,'adequate_n':int(mask.sum())>=100,**metrics(a,z),**ci})
                for control in (['M0']+(['M1'] if n=='M3' else [])+(['M4_without_mi'] if n=='M4' else [])):
                    for grouping in ['customer_id','cluster']:
                        paired.append({'split':split,'scenario':scenario,'model':n,'control':control,'grouping':grouping,'delta_rmse':np.sqrt(np.mean((p-y.actual)**2))-np.sqrt(np.mean((ps[control]-y.actual)**2)),**boot(y.actual.to_numpy(),p,ps[control],x[grouping].to_numpy())})
                if split=='final' and n in ['M0',lock['selected']]:
                    ee=p*x.ead_at_default.to_numpy()*WEIGHTS[scenario]
                    for sector,g in x.groupby('industry'):
                        ecl.append({'model':n,'scenario':scenario,'stage':3,'industry':sector,'ecl':ee[g.index].sum(),'n':len(g)})
            # Independent realized LGD arithmetic from stored cash flows.
            pv=sum(y[f'net_cf_{m}m'].to_numpy()/np.power(1+x.interest_rate.to_numpy(),m/12) for m in BUCKETS)
            err=float(np.max(np.abs(np.clip(1-pv/x.ead_at_default.to_numpy(),0,1)-y.actual)))
            checks.append({'split':split,'scenario':scenario,'target_cashflow_max_error':err,'passed':err<1e-9})
        for n in EXTRA:
            v=(scenario_preds['upside'][n]>scenario_preds['baseline'][n]+1e-10)|(scenario_preds['baseline'][n]>scenario_preds['downside'][n]+1e-10)
            reversals.append({'split':split,'model':n,'count':int(v.sum())})
        print('evaluated',split,flush=True)
    for name,rows in [('metrics',summary),('segments',detail),('paired_uncertainty',paired),('scenario_order',reversals),('ecl_bridge',ecl)]: csv(OUT/f'{name}.csv',pd.DataFrame(rows))
    csv(OUT/'support.csv.gz',pd.concat(supports)); csv(OUT/'predictions.csv.gz',pd.concat(predictions))
    writej(OUT/'reconciliation.json',checks)
    # Independently recompute every retained historical gate decision without rewriting evidence.
    old=json.loads((ROOT/'s2_remediation/results/gate_checks.json').read_text()); verified=[]
    for r in old:
        if 'bound_pp' in r: value=r['bound_pp']<=r['tolerance_pp'] and (r['n']>=100 if r['gate']=='guarantees' else True)
        elif 'original' in r: value=r['final']<=r['original']
        elif r['gate']=='scenario_consistency': value=r['count']==0
        elif r['gate']=='model_support': value=r['rejected']==0
        else: continue
        verified.append(value==r['passed'])
    d=pd.DataFrame(detail); selected=lock['selected']; gate_rows=[]
    for r in d[(d.model==selected)&(d.split=='final')].to_dict('records'):
        if r['segment'].startswith(('realized_','low_','cure','age:')): continue
        tolerance=.01 if r['segment']=='all' or r['segment'].startswith('latent_regime:') else .02
        gate_rows.append({'segment':r['segment'],'scenario':r['scenario'],'tolerance':tolerance,'status':'PASS' if r['n']>=100 and max(abs(r['bias_low']),abs(r['bias_high']))<=tolerance else 'FAIL','basis':'realized clustered interval; latent-state conditional equivalence not interchangeable'})
    writej(OUT/'promotion_gates.json',{'disposition':'CHALLENGER_NOT_PROMOTED','institutional':'BLOCKED','historical_gate_arithmetic_verified':all(verified),'historical_checks_recalculated':len(verified),'current_live_features':'BLOCKED: no validated MI ledger or observation-age contract','historical_conditional_gates':'NOT TRANSFERABLE: new remaining-LGD target; latent oracle is not observable conditional truth','original_S2_same_target_comparison':'NOT AVAILABLE: historical artifact has different target; cannot pass existing gate','calibration':gate_rows,'support':'PASS' if all(s.supported.all() and not s.new_feature_outside_range.any() for s in supports) else 'FAIL','scenario':'PASS' if all(r['count']==0 for r in reversals if r['model']==selected) else 'FAIL','engineering':'PENDING full tests','institutional_validation':'UNAVAILABLE'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['generate','fit','evaluate']);a=p.parse_args();globals()[a.action]()
