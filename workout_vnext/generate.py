"""WN-1 chronological simulator. No final LGD is used to construct any event."""
from pathlib import Path
import json,gzip,hashlib,subprocess
import numpy as np
import pandas as pd
from .store import ENTITIES

HERE=Path(__file__).resolve().parent
DATA=HERE/'data'
FEATURES=['predefault_pd','predefault_rating','rating_migration','financial_strength','previous_defaults','utilization','delinquency','age','months_since_last_recovery','recovered_ratio','collateral_ratio','haircut','lien','enforcement','guarantee_ratio','guarantor_quality','enforceability','claim','restructured','cost_ratio','growth','unemployment','price_change','rate','mi_ratio','ead']
FAMILIES={'credit':['predefault_pd','predefault_rating','rating_migration','financial_strength','previous_defaults','utilization','delinquency'],'age':['age','months_since_last_recovery'],'collateral':['collateral_ratio','haircut','lien','enforcement'],'guarantees':['guarantee_ratio','guarantor_quality','enforceability','claim'],'history':['recovered_ratio','restructured'],'costs':['cost_ratio'],'macro':['growth','unemployment','price_change','rate'],'interest':['mi_ratio']}
CHANNELS=['borrower','restructure','collateral','guarantee','sale','cure']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v))+'\n')
def save(p,x):x.to_csv(p,index=False,float_format='%.12g',compression={'method':'gzip','mtime':0})
def sig(x):return 1/(1+np.exp(-x))

def snapshot(events,facility,month,observation):
    visible={n:[r for r in rows if r['effective_date']<=observation and r['recorded_at']<=observation] for n,rows in events.items()}
    latest=lambda n:visible[n][-1]['payload'] if visible[n] else {}
    if visible['resolution_event']:return None
    credit=latest('credit_snapshot');macro=latest('macro_snapshot');sec=latest('collateral_valuation');guar=latest('guarantee');base=facility['principal']+facility['predefault_interest']
    rec=sum(r['amount'] for r in visible['recovery_transaction']);ead=base-rec
    if ead<=.01:return None
    last=max([r['payload']['month'] for r in visible['recovery_transaction']],default=0)
    return {'facility_id':facility['id'],'borrower_id':facility['borrower_id'],'observation_date':observation,'age':month,'ead':ead,'predefault_pd':credit['predefault_pd'],'predefault_rating':credit['predefault_rating'],'rating_migration':credit['rating_migration'],'financial_strength':credit['financial_strength'],'previous_defaults':credit['previous_defaults'],'utilization':credit['utilization'],'delinquency':credit['delinquency'],'months_since_last_recovery':month-last,'recovered_ratio':rec/base,'collateral_ratio':sec.get('value',0)/ead,'haircut':sec.get('haircut',0),'lien':sec.get('lien',1),'enforcement':int(bool(visible['collateral_enforcement'])),'guarantee_ratio':min(1,guar.get('eligible',0)/ead),'guarantor_quality':guar.get('quality',0),'enforceability':guar.get('enforceability',0),'claim':int(bool(visible['guarantee_claim'])),'restructured':int(bool(visible['restructure_event'])),'cost_ratio':sum(r['amount'] for r in visible['workout_cost'])/base,'growth':macro['growth'],'unemployment':macro['unemployment'],'price_change':macro['price_change'],'rate':facility['rate'],'mi_ratio':sum(r['amount'] for r in visible['interest_accrual'])/ead,'known_event_ids':[r['id'] for rows in visible.values() for r in rows]}

def generate():
    if DATA.exists():raise ValueError('Frozen WN data exists; no regeneration')
    DATA.mkdir();rng=np.random.default_rng(1072026);tables={n:[] for n in ['borrower','facility']+ENTITIES};snapshots=[];outcomes=[];episode=[];sources=[]
    for i in range(8000):
        split='development' if i<4800 else 'validation' if i<6400 else 'final';lo,hi={'development':(2010,2015),'validation':(2015,2018),'final':(2018,2021)}[split]
        year=int(rng.integers(lo,hi));month=int(rng.integers(1,13));start=pd.Timestamp(year,month,1);dates=[str((start+pd.DateOffset(months=m)).date()) for m in range(73)]
        sector=['Manufacturing','Retail','Services','Construction'][i%4];fid=f'WN-F{i:05d}';bid=f'WN-B{i:05d}';source='WN-1:1072026';stress=.8*np.sin((year-2010)*1.3)+rng.normal(0,.25);strength=rng.normal();hidden=rng.normal()
        pd0=float(sig(-3-.65*strength+.5*stress));rating=int(np.clip(np.ceil(pd0*45)+2,1,7));principal=float(np.exp(rng.normal(12.5,.8)));rate=float(np.clip(.05+.02*stress+.04*pd0,.02,.18));pre=principal*rate/12
        fac=dict(id=fid,borrower_id=bid,product=['Term Loan','OVD'][i%2],principal=principal,predefault_interest=pre,rate=rate,source=source);tables['borrower'].append(dict(id=bid,industry=sector,source=source));tables['facility'].append(fac);events={n:[] for n in ENTITIES}
        def add(kind,m,amount=0,delay=0,**payload):
            day=dates[min(m,72)] if m>=0 else str((start+pd.DateOffset(months=m)).date());recorded=str((pd.Timestamp(day)+pd.Timedelta(days=delay)).date())
            r=dict(id=f'{fid}-{kind}-{len(events[kind])}',facility_id=fid,effective_date=day,recorded_at=recorded,source=source,amount=float(amount),payload={'month':m,**payload});events[kind].append(r);return r
        for m in [-12,-6,-3,0]:
            p=float(sig(np.log(pd0/(1-pd0))+.025*(m+12)));add('credit_snapshot',m,predefault_pd=p,predefault_rating=rating,rating_migration=1 if m==0 else 0,financial_strength=strength,previous_defaults=int(i%17==0),utilization=float(np.clip(.6+.02*(m+12)+rng.normal(0,.03),0,1)),delinquency=max(0,int(90+m*7.5)),current_pd=1 if m==0 else p)
        add('default_event',0,reason='90DPD',default_pd=1,default_rating=8)
        ctype=rng.choice(['none','cash','property','other'],p=[.35,.1,.35,.2]);coverage=float(rng.uniform(.3,1.4)) if ctype!='none' else 0;val=coverage*(principal+pre);hair={'none':0,'cash':0,'property':.2,'other':.4}[ctype];lien=int(rng.choice([1,2],p=[.85,.15]));gcat=rng.choice(['none','partial','full'],p=[.65,.25,.1]);gc=0 if gcat=='none' else 1 if gcat=='full' else rng.uniform(.2,.8);quality=rng.uniform(.3,1) if gc else 0;enforce=rng.choice([0,1],p=[.08,.92]) if gc else 0
        add('collateral',0,val,type=ctype,lien=lien,original_value=val);add('collateral_valuation',0,val,value=val,haircut=hair,lien=lien)
        add('guarantee',0,gc*(principal+pre),nominal=gc*(principal+pre),eligible=gc*(principal+pre)*enforce,quality=quality,enforceability=int(enforce),guarantor=f'G-{i}',type='corporate')
        balance=principal+pre;mi=0;follow=int(rng.choice([24,36,60,72],p=[.10,.15,.25,.5]));coll_month=2 if ctype=='cash' else int(rng.integers(12,49));claim_month=int(rng.integers(6,37));resolved=None;cured=False;restructured=False;local_snaps=[]
        for m in range(follow+1):
            if m%3==0:
                macro=dict(growth=2-2*stress+.25*np.sin(m/6),unemployment=5.5+1.2*stress,price_change=-.1*stress+.025*np.sin(m/9));add('macro_snapshot',m,**macro)
                if ctype!='none' and not any(r['payload'].get('channel')=='collateral' for r in events['recovery_transaction']):
                    value=max(0,val*(1+macro['price_change'])*np.exp(rng.normal(0,.04)));add('collateral_valuation',m,value,value=value,haircut=hair,lien=lien,delay=2 if m else 0)
            if resolved is not None:
                if cured and m%6==0:add('credit_snapshot',m,predefault_pd=pd0,predefault_rating=rating,rating_migration=-1,financial_strength=strength,previous_defaults=1,utilization=.5,delinquency=0,current_pd=pd0)
                continue
            if m>0:
                accr=balance*rate/12;mi+=accr;add('interest_accrual',m,accr,treatment='suspended_memo_not_EAD')
                add('workout_cost',m,(principal+pre)*(.0007+.00025*max(stress,0)),kind='servicing')
                if m==6:
                    restructured=bool(rng.random()<sig(-1+.5*strength));
                    if restructured:add('restructure_event',m,status='agreed',interest_capitalized=False)
                    if ctype not in ['none','cash']:add('collateral_enforcement',m,status='initiated');add('workout_cost',m,principal*.008,kind='legal')
                    if gc:add('guarantee_claim',m,status='submitted',eligible=gc*(principal+pre)*enforce)
                payments=[]
                if rng.random()<sig(-1+.6*strength+.5*hidden-.3*stress):payments.append(('restructure' if restructured else 'borrower',balance*rng.uniform(.005,.04)))
                if m==coll_month and ctype!='none':
                    latest=events['collateral_valuation'][-1]['amount'];gross=latest*(1-hair)*(1 if lien==1 else .7)*np.clip(1-.15*stress+rng.normal(0,.12),.1,1.2);payments.append(('collateral',gross));add('workout_cost',m,gross*.03,kind='realization')
                if m==claim_month and gc and enforce and rng.random()<quality:payments.append(('guarantee',gc*(principal+pre)*quality*np.clip(1-.15*stress,0,1)))
                if m==42 and rng.random()<.08:payments.append(('sale',balance*rng.uniform(.1,.45)))
                if rng.random()<sig(-4+.7*strength+.4*hidden-.4*stress+.4*restructured):payments.append(('cure',balance));cured=True
                for channel,amount in payments:
                    pay=max(0,min(balance,amount));balance-=pay
                    if pay:add('recovery_transaction',m,pay,channel=channel)
                if cured:add('cure_event',m,status='paid_and_returned_performing')
                terminal=cured or balance<=.01 or (m>=60 and rng.random()<.8)
                if terminal:
                    if balance>.01:add('writeoff_event',m,balance,noncash=True)
                    resolved=m;add('resolution_event',m,status='cured' if cured else 'closed',residual=balance)
            if m in [0,3,6,12,24]:
                x=snapshot(events,fac,m,dates[m])
                if x is not None:
                    x.update(split=split,industry=sector,product=fac['product'],collateral_type=ctype,default_vintage=year,snapshot_id=f'{fid}-{m}');local_snaps.append(x);add('workout_snapshot',m,balance,snapshot_id=x['snapshot_id'],stage=3)
        for x in local_snaps:
            y=dict(snapshot_id=x['snapshot_id'],facility_id=fid,borrower_id=bid,split=split,resolved=int(resolved is not None),followup=follow-x['age'],future_cure=int(cured),resolution_months=resolved-x['age'] if resolved is not None else np.nan)
            for ch in CHANNELS:y['pv_'+ch]=np.nan
            y['pv_cost']=np.nan;y['raw_lgd']=np.nan;y['lgd']=np.nan
            if resolved is not None:
                for ch in CHANNELS:y['pv_'+ch]=sum(r['amount']/(1+rate)**((r['payload']['month']-x['age'])/12) for r in events['recovery_transaction'] if r['payload']['month']>x['age'] and r['payload']['channel']==ch)/x['ead']
                y['pv_cost']=sum(r['amount']/(1+rate)**((r['payload']['month']-x['age'])/12) for r in events['workout_cost'] if r['payload']['month']>x['age'])/x['ead'];y['raw_lgd']=1-sum(y['pv_'+ch] for ch in CHANNELS)+y['pv_cost'];y['lgd']=np.clip(y['raw_lgd'],0,1)
            outcomes.append(y)
        snapshots.extend(local_snaps);episode.append(dict(facility_id=fid,borrower_id=bid,split=split,default_vintage=year,followup=follow,duration=resolved if resolved is not None else follow,resolved=resolved is not None,cured=cured))
        for n in ENTITIES:tables[n].extend(events[n])
        if i%2000==0:print('episodes',i,flush=True)
    for n,rows in tables.items():
        with gzip.open(DATA/(n+'.jsonl.gz'),'wt') as f:
            for r in rows:f.write(json.dumps(r)+'\n')
    for split in ['development','validation','final']:
        x=pd.DataFrame(snapshots);y=pd.DataFrame(outcomes);save(DATA/f'{split}_inputs.csv.gz',x[x.split==split]);save(DATA/f'{split}_outcomes.csv.gz',y[y.split==split])
    save(DATA/'episodes.csv.gz',pd.DataFrame(episode))
    dump(DATA/'manifest.json',{'version':'WN-1','seed':1072026,'generator_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'counts':{n:len(v) for n,v in tables.items()},'snapshots':len(snapshots),'files':{p.name:sha(p) for p in DATA.glob('*.gz')}})

if __name__=='__main__':generate()
