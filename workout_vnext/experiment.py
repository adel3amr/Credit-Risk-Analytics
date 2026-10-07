"""Fixed WN-1 comparison; prospective generation, selection and final opening separated."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error,brier_score_loss
from .generate import HERE,DATA,FEATURES,FAMILIES,CHANNELS,sha,dump,save
from marginal_interest.experiment import boot,metrics

OUT=HERE/'results';CAT=['industry','product','collateral_type']

def verify():
    m=json.loads((DATA/'manifest.json').read_text())
    for f,h in m['files'].items():
        if sha(DATA/f)!=h:raise ValueError('Dataset hash mismatch '+f)
    return m

def features(x,omit=None):
    cols=[c for c in FEATURES if c not in FAMILIES.get(omit,[])]+CAT
    if x[cols].isna().any().any() or not np.isfinite(x[[c for c in cols if c not in CAT]].to_numpy()).all():raise ValueError('Missing/nonfinite WN features')
    if (x.ead<=0).any() or (x.rate<0).any() or not x.predefault_pd.between(0,1).all() or (x.age<0).any():raise ValueError('Invalid WN feature domain')
    return x[cols]

def pipeline(x,regressor,omit=None):
    nums=[c for c in FEATURES if c not in FAMILIES.get(omit,[])];cats=[sorted(x[c].unique()) for c in CAT]
    return Pipeline([('prep',ColumnTransformer([('num',StandardScaler(),nums),('cat',OneHotEncoder(categories=cats,handle_unknown='error',sparse_output=False),CAT)])),('model',regressor)])

class Component:
    def __init__(self,omit=None):self.omit=omit
    def fit(self,x,y):
        z=features(x,self.omit);self.cure=pipeline(x,LogisticRegression(C=1,max_iter=1000,random_state=94001),self.omit).fit(z,y.future_cure)
        self.parts={}
        for state in [0,1]:
            mask=y.future_cure.eq(state)
            self.parts[state]=pipeline(x,Ridge(alpha=10),self.omit).fit(z.loc[mask],y.loc[mask,['pv_'+c for c in CHANNELS]+['pv_cost']])
        self.timing=pipeline(x,Ridge(alpha=10),self.omit).fit(z,np.log1p(y.resolution_months));return self
    def predict_components(self,x):
        z=features(x,self.omit);p=self.cure.predict_proba(z)[:,1];a=np.maximum(self.parts[0].predict(z),0);b=np.maximum(self.parts[1].predict(z),0);parts=a*(1-p[:,None])+b*p[:,None]
        # One common residual cap on total predicted PV recoveries, no duplicated security allocation.
        total=parts[:,:len(CHANNELS)].sum(axis=1);parts[:,:len(CHANNELS)]/=np.maximum(total,1)[:,None]
        return parts,p,np.maximum(np.expm1(self.timing.predict(z)),0)
    def predict(self,x):
        parts,_,_=self.predict_components(x);return np.clip(1-parts[:,:len(CHANNELS)].sum(axis=1)+parts[:,-1],0,1)

def load(split):
    x=pd.read_csv(DATA/f'{split}_inputs.csv.gz');y=pd.read_csv(DATA/f'{split}_outcomes.csv.gz');assert x.snapshot_id.tolist()==y.snapshot_id.tolist();return x,y

def fit():
    verify()
    if OUT.exists():raise ValueError('Model results already exist')
    OUT.mkdir();x,y=load('development');mask=y.resolved.eq(1);d=x[mask];t=y[mask]
    direct=pipeline(d,HistGradientBoostingRegressor(max_iter=350,learning_rate=.05,max_leaf_nodes=31,min_samples_leaf=80,l2_regularization=5,random_state=94001,early_stopping=False)).fit(features(d),t.lgd)
    models={'direct_new':direct,'component':Component().fit(d,t)}
    for family in FAMILIES:models['without_'+family]=Component(family).fit(d,t)
    v,vy=load('validation');vm=vy.resolved.eq(1);rows=[]
    for n,m in models.items():
        joblib.dump(m,OUT/f'{n}.joblib');p=np.clip(m.predict(features(v[vm]) if n=='direct_new' else v[vm]),0,1);rows.append({'model':n,**metrics(vy.loc[vm,'lgd'],p)})
    pd.DataFrame(rows).to_csv(OUT/'validation_selection.csv',index=False)
    dump(OUT/'LOCK.json',{'candidate':'component','benchmark':'direct_new','models':{p.name:sha(p) for p in OUT.glob('*.joblib')},'data_manifest':sha(DATA/'manifest.json'),'architecture':'WN-1','final_opened':False,'no_tuning':True})

def retained_predict(x):
    m=joblib.load(HERE.parent/'s2_remediation/results/model.joblib')
    z=pd.DataFrame({'ead_at_default':x.ead,'collateral_coverage':x.collateral_ratio,'guarantee_coverage':x.guarantee_ratio,'leverage_at_default':np.exp(-x.financial_strength*.3+1),'current_ratio_at_default':np.exp(x.financial_strength*.2),'management_quality':np.clip(3+x.financial_strength,1,5),'interest_rate':x.rate,'output_growth_pct':x.growth,'unemployment_pct':x.unemployment,'collateral_change_pct':x.price_change*100,'liquidity':np.clip(.8+.025*x.growth,.05,1),'product_type':x['product'],'industry':x.industry,'collateral_type':x.collateral_type.map({'none':'Unsecured','cash':'Cash','property':'Mortgage','other':'Other'}),'lien_rank':np.where(x.lien==1,'First','Second')})
    return np.clip(m.predict(z),0,1)

def groups(x,y,p):
    yield 'all',np.ones(len(x),dtype=bool)
    for n,mask in [('cure',y.future_cure==1),('noncure',y.future_cure==0),('restructured',x.restructured==1),('secured',x.collateral_ratio>0),('unsecured',x.collateral_ratio==0),('guaranteed',x.guarantee_ratio>0),('full_guarantee',x.guarantee_ratio==1),('high60',y.lgd>.6),('high75',y.lgd>.75),('high90',y.lgd>=.9),('low10',y.lgd<=.1),('short',y.resolution_months<=12),('long',y.resolution_months>24)]:yield n,np.asarray(mask)
    for c in ['industry','product','default_vintage','age']:
        for v in sorted(x[c].unique()):yield c+':'+str(v),np.asarray(x[c]==v)
    for lo,hi in zip([0,.1,.25,.5,.75],[.1,.25,.5,.75,1.000001]):yield f'predicted:{lo}-{min(hi,1)}',(p>=lo)&(p<hi)

def evaluate():
    verify();lock=json.loads((OUT/'LOCK.json').read_text())
    if (OUT/'FINAL_OPENED.json').exists():raise ValueError('Final already opened')
    for f,h in lock['models'].items():
        if sha(OUT/f)!=h:raise ValueError('Artifact mismatch')
    dump(OUT/'FINAL_OPENED.json',{'lock_hash':sha(OUT/'LOCK.json'),'purpose':'single prespecified evaluation'})
    models={p.stem:joblib.load(p) for p in OUT.glob('*.joblib')};dev,_=load('development');summaries=[];segments=[];predictions=[];support=[];stress=[];cal=[];paired=[]
    for split in ['development','validation','final']:
        x,y=load(split);mask=y.resolved.eq(1);xx=x[mask].reset_index(drop=True);yy=y[mask].reset_index(drop=True)
        ps={n:np.clip(m.predict(features(xx) if n=='direct_new' else xx),0,1) for n,m in models.items()};ps['retained_transfer']=retained_predict(xx)
        for n,p in ps.items():
            summaries.append({'split':split,'model':n,**metrics(yy.lgd,p)});z=xx[['snapshot_id','facility_id','borrower_id','ead','age','default_vintage','industry']].copy();z['actual']=yy.lgd;z['prediction']=p;z['model']=n;z['split']=split;predictions.append(z)
            if n not in ['direct_new','component']:continue
            slope,intercept=np.polyfit(p,yy.lgd,1);cal.append({'split':split,'model':n,'slope':slope,'intercept':intercept})
            if split=='development':continue
            paired.append({'split':split,'model':n,'delta_rmse':np.sqrt(np.mean((p-yy.lgd)**2))-np.sqrt(np.mean((ps['direct_new']-yy.lgd)**2)),**boot(yy.lgd.to_numpy(),p,ps['direct_new'],xx.borrower_id.to_numpy(),1073000)})
            for label,g in groups(xx,yy,p):
                if not g.any():continue
                segments.append({'split':split,'model':n,'group':label,**metrics(yy.lgd.to_numpy()[g],p[g]),**boot(yy.lgd.to_numpy()[g],p[g],ps['direct_new'][g],xx.borrower_id.to_numpy()[g],1073000)})
        if split!='development':
            for c in FEATURES:support.append({'split':split,'feature':c,'missing':int(x[c].isna().sum()),'outside':int(((x[c]<dev[c].min())|(x[c]>dev[c].max())).sum()),'n':len(x)})
            baseline=models['component'].predict(x)
            for name in ['downturn','collateral_shock','guarantee_stress','slower_recovery','cost_shock']:
                z=x.copy()
                if name=='downturn':z['growth']-=2;z['unemployment']+=2;z['price_change']-=.2
                if name=='collateral_shock':z['collateral_ratio']*=.7
                if name=='guarantee_stress':z['guarantor_quality']*=.7
                if name in ['slower_recovery','cost_shock']:
                    parts,_,_=models['component'].predict_components(z)
                    if name=='slower_recovery':parts[:,:len(CHANNELS)]/=(1+z.rate.to_numpy())[:,None]
                    else:parts[:,-1]*=1.5
                    pp=np.clip(1-parts[:,:len(CHANNELS)].sum(axis=1)+parts[:,-1],0,1)
                else:pp=models['component'].predict(z)
                stress.append({'split':split,'stress':name,'mean_lgd_change':float(np.mean(pp-baseline)),'decreasing_loss_count':int((pp<baseline-1e-10).sum()),'basis':'sensitivity,not realized stressed validation'})
            # Every current/open observation gets a score, but no invented realized target.
            openx=x[~mask];save(OUT/f'{split}_open_scores.csv.gz',openx[['snapshot_id','facility_id','ead','age']].assign(prediction=models['component'].predict(openx)))
        print('evaluated',split,flush=True)
    for name,rows in [('metrics',summaries),('segments',segments),('paired',paired),('calibration',cal),('support',support),('stress',stress)]:pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False)
    save(OUT/'predictions.csv.gz',pd.concat(predictions,ignore_index=True))
    # Censor-aware descriptive survival, not a censor-adjusted LGD fit.
    episodes=pd.read_csv(DATA/'episodes.csv.gz');km=[]
    for split,g in episodes.groupby('split'):
        survival=1.
        for t in sorted(g.duration.unique()):
            risk=int((g.duration>=t).sum());events=int(((g.duration==t)&g.resolved).sum());survival*=1-events/risk;km.append({'split':split,'month':t,'at_risk':risk,'resolutions':events,'survival':survival})
    pd.DataFrame(km).to_csv(OUT/'survival.csv',index=False)
    d=pd.DataFrame(segments);c=d[(d.split=='final')&(d.model=='component')];eligible=c[~c.group.str.startswith(('high','low','cure','noncure','short','long'))]
    failures=[r['group'] for r in eligible.to_dict('records') if r['n']<100 or max(abs(r['bias_low']),abs(r['bias_high']))>(.01 if r['group']=='all' else .02)]
    dump(OUT/'decision.json',{'model':'WN-1-component','status':'REFERENCE_ARCHITECTURE_COMPLETE_MODEL_NOT_PROMOTED','institutional':'BLOCKED','calibration_failures':failures,'support_violations':sum(r['outside'] for r in support if r['split']=='final'),'stress_reversals':sum(r['decreasing_loss_count'] for r in stress if r['split']=='final'),'censoring':'OPEN: fit conditional on resolved episodes; selection bias not corrected','engineering':'PENDING','real_portfolio_feature_availability':'UNVALIDATED','criterion':'All gates required;no automatic promotion'})

if __name__=='__main__':
    import sys
    {'fit':fit,'evaluate':evaluate}[sys.argv[1]]()
