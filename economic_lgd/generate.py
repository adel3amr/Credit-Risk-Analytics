"""Generate S2 once; freeze inputs and realized cashflows before model development."""
import json
import numpy as np
import pandas as pd
from credit_platform.common import ROOT, file_hash, atomic_json
from synthetic_bank.generate import write_csv
from .economics import history, validate
from .recovery import simulate, BUCKETS

DEST = ROOT/'economic_lgd/data'
COHORTS = {'development':(12000,72001,'2000-01-01'),
           'selection':(3000,72002,'2009-01-01'),
           'final':(3000,72003,'2018-01-01'),
           'current':(None,72004,'2026-01-01')}


def main():
    if DEST.exists():
        raise SystemExit('Frozen S2 output exists; use a new version, never overwrite')
    DEST.mkdir(parents=True)
    manifest = {'version':'S2','purpose':'synthetic conditional-on-default recovery fixtures',
                'sources':{},'cohorts':{},'files':{}}
    for name,(n,seed,date) in COHORTS.items():
        path = ROOT/f'synthetic_bank/data/{name}/facilities.csv.gz'
        bpath = ROOT/f'synthetic_bank/data/{name}/borrowers.csv.gz'
        manifest['sources'][str(path.relative_to(ROOT))] = file_hash(path)
        manifest['sources'][str(bpath.relative_to(ROOT))] = file_hash(bpath)
        f = pd.read_csv(path)
        if n:
            f = f.sample(n=n,random_state=seed)
        f = f.sort_values('facility_id').reset_index(drop=True)
        borrowers = pd.read_csv(bpath).set_index('customer_id')
        f['interest_rate'] = f.customer_id.map(borrowers.interest_rate)
        # S1 hidden regime is neither a join key nor an S2 economic observation.
        f = f.drop(columns=['downturn_at_default','observed_at'],errors='ignore')
        h = history(sorted(f.industry.unique()),date,seed,current=name=='current')
        dates = sorted(h.reporting_date.unique())
        rng = np.random.default_rng(seed+100)
        borrower_dates = dict(zip(sorted(f.customer_id.unique()),
            rng.choice(dates,f.customer_id.nunique())))
        f['reporting_date'] = f.customer_id.map(borrower_dates)
        f = f.merge(h,on=['industry','reporting_date'],validate='many_to_one')
        validate(f)
        # Independent targets: never placed in the feature contract.
        y,cf = simulate(f,np.random.default_rng(seed+200),cashflows=True)
        w = f[['facility_id','customer_id','reporting_date']].copy()
        w['economic_lgd'] = y[:,0]
        w['resolved_at'] = (pd.to_datetime(w.reporting_date)+pd.DateOffset(months=60)).dt.strftime('%Y-%m-%d')
        for j,m in enumerate(BUCKETS):
            w[f'net_cf_{m}m'] = cf[:,0,j]
        write_csv(f,DEST/f'{name}_inputs.csv.gz')
        write_csv(w,DEST/f'{name}_outcomes.csv.gz')
        write_csv(h,DEST/f'{name}_macro.csv.gz')
        manifest['cohorts'][name] = {'n':len(f),'seed':seed,'start':date,
            'borrowers':f.customer_id.nunique(),'macro_clusters':len(h),
            'target_role':'diagnostic-only' if name=='current' else 'hypothetical-workout'}
    for p in sorted((ROOT/'economic_lgd').glob('*.py')):
        manifest['sources'][str(p.relative_to(ROOT))] = file_hash(p)
    manifest['sources']['economic_lgd/PROTOCOL.md'] = file_hash(ROOT/'economic_lgd/PROTOCOL.md')
    manifest['files'] = {str(p.relative_to(ROOT)):file_hash(p) for p in sorted(DEST.glob('*.gz'))}
    atomic_json(DEST/'manifest.json',manifest)
    print(json.dumps(manifest['cohorts'],indent=2))


if __name__=='__main__':
    main()
