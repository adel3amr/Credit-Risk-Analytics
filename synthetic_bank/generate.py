"""S1 integrated synthetic source; independent of the production risk engine."""
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from credit_platform.contracts import BORROWER_FEATURES
from credit_platform.domain import DatasetInput
from src.lgd_model import portfolio_to_facilities

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'synthetic_bank/data'
COHORTS = {'development': (30000, 31001, '2005-01-01'),
           'selection': (15000, 31002, '2012-01-01'),
           'final': (15000, 31003, '2019-01-01'),
           'current': (5000, 31004, '2026-01-01')}
BUCKETS = np.array([1, 6, 12, 24, 36, 60])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(frame, path):
    # Empty filename and fixed timestamp make the compressed bytes reproducible.
    with open(path, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            zipped.write(frame.to_csv(index=False, float_format='%.12g').encode())


def base_borrowers(n, seed):
    spec = importlib.util.spec_from_file_location('s1_frozen_borrower_source',
                    ROOT/'scripts/generate_sme_portfolio.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as tmp:
        module.ROOT = Path(tmp)
        module.OUT = Path(tmp)/'data/raw/sme_credit_portfolio.csv'
        module.N, module.SEED = n, seed
        with contextlib.redirect_stdout(io.StringIO()):
            module.main()
        return pd.read_csv(module.OUT), pd.read_csv(Path(tmp)/'data/raw/sme_behavioral_history_36m.csv')


def recoveries(f, borrowers, rng):
    """Linked R2-derived cashflow process; shared borrower future uncertainty."""
    b = borrowers.set_index('customer_id')
    ids = f.customer_id
    selected = b.loc[ids]
    n = len(b)
    draws = pd.DataFrame(index=b.index)
    for name, sd in [('market', .16), ('bank', .16), ('collection', .10), ('cure_noise', 1), ('cost_noise', .009)]:
        draws[name] = rng.normal(0, sd, n)
    p = 1/(1+np.exp(-(-1.5+.6*(b.current_ratio-1)-.22*(b.leverage_ratio-2.5)
                     +.20*(b.management_quality-3)-.55*b.downturn_at_default)))
    draws['cure'] = rng.binomial(1, p)
    draws['delay'] = rng.gamma(2, 5, n)
    draws['cash_months'] = rng.integers(1, 5, n)
    d = draws.loc[ids].reset_index(drop=True)
    f = f.reset_index(drop=True).copy()
    e = f.ead_at_default.to_numpy()
    c = f.collateral_type.to_numpy()
    downturn = f.downturn_at_default.to_numpy()
    second = f.lien_rank.eq('Second').to_numpy()
    liquidation = np.select([c=='Cash', c=='Mortgage', c=='Other'], [.97,.68,.44], default=0.)
    secured = np.minimum(e, e*f.collateral_coverage.to_numpy()*liquidation*
        np.where(second,.72,1)*(.55+.6*f.security_quality.to_numpy())*
        np.clip(1+d.market.to_numpy()-.2*downturn,.15,1.5))
    guaranteed = np.minimum(np.maximum(e-secured,0),e*f.guarantee_coverage.to_numpy()*
        (.25+.65*f.guarantor_strength.to_numpy())*np.clip(1+d.bank.to_numpy()-.2*downturn,0,1.3))
    residual = np.maximum(e-secured-guaranteed,0)
    unsecured = residual*np.clip(.30-.027*(f.leverage_at_default.to_numpy()-2.8)
        +.045*(f.current_ratio_at_default.to_numpy()-1)+.02*(f.management_quality.to_numpy()-3)
        -.10*downturn+d.collection.to_numpy(),0,.75)
    cured = np.where(d.cure==1,np.maximum(e*(.90+.04*d.cure_noise)-secured-guaranteed-unsecured,0),0)
    cured = np.minimum(cured,np.maximum(e-secured-guaranteed-unsecured,0))
    gross = secured+guaranteed+unsecured+cured
    months = np.clip(np.rint(8+17*(c=='Mortgage')+8*second+9*(1-d.cure)+13*downturn+d.delay),1,60)
    months = np.where(c=='Cash',d.cash_months+4*downturn,months)
    costs = e*np.clip(.012+.014*(c=='Mortgage')+.012*second+.025*downturn+d.cost_noise,.003,.16)
    weights = np.exp(-np.abs(BUCKETS[None,:]-np.asarray(months)[:,None])/9)
    weights /= weights.sum(axis=1,keepdims=True)
    net = np.asarray(gross)[:,None]*weights
    net[:,0] -= costs*(c=='Cash')
    net[:,2] -= costs*(c!='Cash')
    rate = selected.interest_rate.to_numpy()
    pv = (net/(1+rate[:,None])**(BUCKETS[None,:]/12)).sum(axis=1)
    out = pd.DataFrame({'facility_id':f.facility_id,'customer_id':ids.to_numpy(),
        'default_date':selected.default_date.to_numpy(),
        'resolved_at':[(pd.Timestamp(x)+pd.DateOffset(months=60)).date().isoformat() for x in selected.default_date],
        'collateral_recovery':secured,'guarantee_recovery':guaranteed,
        'unsecured_recovery':unsecured,'cure_recovery':cured,'cure_flag':d.cure,
        'workout_cost':costs,'months_to_resolution':months,'discount_rate':rate,
        'pv_net_recovery':pv,'unbounded_economic_lgd':1-pv/e,'economic_lgd':np.clip(1-pv/e,0,1)})
    for j,m in enumerate(BUCKETS):
        out[f'recovery_cf_{m}m'] = net[:,j]
    return out


def generate_cohort(name, n, seed, date):
    b, history = base_borrowers(n, seed)
    b.customer_id = name+'-'+b.customer_id
    history.customer_id = name+'-'+history.customer_id
    history['observed_at'] = [(pd.Timestamp(date)+pd.DateOffset(months=int(m))).date().isoformat()
                             for m in history.month_from_reporting]
    rng = np.random.default_rng(seed+100000)
    # Sector state is an observed synthetic context shared within the cohort.
    sector_states = dict(zip(sorted(b.industry.unique()),rng.binomial(1,.22,b.industry.nunique())))
    b['downturn_at_default'] = b.industry.map(sector_states)
    b['observed_at'] = date
    f = portfolio_to_facilities(b)
    f.facility_id = name+'-'+f.facility_id
    # Reconcile trade EAD from stored face, avoiding independent rounding.
    bidx = b.set_index('customer_id')
    ccf = {'Import LC':.2,'Performance Guarantee':.5,'Financial Guarantee':1.}
    for product, factor in ccf.items():
        mask = f.product_type.eq(product)
        f.loc[mask,'ead_at_default'] = np.round(bidx.loc[f.loc[mask,'customer_id'],'trade'].to_numpy()*factor,2)
    f['observed_at'] = date
    f['downturn_at_default'] = f.customer_id.map(bidx.downturn_at_default)
    has_guarantee = rng.binomial(1,.2,len(f))
    f['guarantee_coverage'] = has_guarantee*rng.choice([.15,.35,.55,.8,1.],len(f))
    f['security_quality'] = np.where(f.collateral_type.eq('Unsecured'),0,
        np.clip(rng.beta(4,2,len(f))-.1*f.downturn_at_default,.05,1))
    f['guarantor_strength'] = np.where(has_guarantee,
        np.clip(rng.beta(3,2,len(f))-.12*f.downturn_at_default,.02,1),0)
    # One collateral pool per borrower, allocated rather than counted per product.
    total = f.groupby('customer_id').ead_at_default.sum()
    coverage = bidx.collateral_value/total
    f['collateral_coverage'] = f.customer_id.map(coverage)
    f['allocated_collateral_value'] = f.ead_at_default*f.collateral_coverage
    f['guarantee_amount'] = f.ead_at_default*f.guarantee_coverage
    b['ead'] = b.customer_id.map(total)
    b['collateral_coverage'] = b.collateral_value/b.ead
    b['recognized_collateral'] = np.minimum(b.collateral_value*(1-b.collateral_haircut),b.ead)
    b['recognized_collateral_coverage'] = b.recognized_collateral/b.ead
    # Keep future targets in a separate entity, never in canonical scoring inputs.
    impaired = b.current_credit_impaired.eq(1)
    event = impaired | b.default.eq(1)
    offsets = rng.integers(1,366,len(b))
    dates = pd.to_datetime(date)+pd.to_timedelta(np.where(impaired,0,offsets),unit='D')
    targets = pd.DataFrame({'customer_id':b.customer_id,'observed_at':date,
        'at_risk':(~impaired).astype(int),'default_12m':np.where(impaired,np.nan,b.default),
        'default_date':np.where(event,dates.strftime('%Y-%m-%d'),None),
        'target_available_at':(pd.Timestamp(date)+pd.DateOffset(years=1)).date().isoformat()})
    b['default_date'] = targets.default_date
    default_facilities = f[f.customer_id.isin(b.loc[event,'customer_id'])]
    workouts = recoveries(default_facilities,b,rng) if name!='current' else pd.DataFrame()
    b = b.drop(columns=['default','pd_true','default_date','lgd','unsecured_lgd','unsecured_ead'])
    if name=='current':
        targets = pd.DataFrame()
    return b,f,history,targets,workouts


def canonical(b,f,name,date):
    bidx = b.set_index('customer_id')
    borrowers = [dict(id=row.customer_id,industry=row.industry,observed_at=date,
        collateral_type=row.collateral_type,features={k:float(getattr(row,k)) for k in BORROWER_FEATURES})
        for row in b.itertuples(index=False)]
    facilities = []
    for row in f.itertuples(index=False):
        source = bidx.loc[row.customer_id]
        direct = row.product_type in ('Term Loan','OVD')
        facilities.append(dict(id=row.facility_id,borrower_id=row.customer_id,observed_at=date,
            product=row.product_type,drawn=float(source.loans if row.product_type=='Term Loan' else
                source.ovd*source.credit_utilization if row.product_type=='OVD' else 0),
            limit=float(source.loan_limit if row.product_type=='Term Loan' else source.ovd if row.product_type=='OVD' else 0),
            face=float(0 if direct else source.trade),remaining_months=float(row.remaining_months),
            collateral_type=row.collateral_type,collateral_coverage=float(row.collateral_coverage),
            guarantee_coverage=float(row.guarantee_coverage),lien_rank=row.lien_rank))
    return DatasetInput.model_validate(dict(name='S1 '+name,effective_date=date,source='synthetic-bank-S1',
        borrowers=borrowers,facilities=facilities))


def main():
    if DEST.exists():
        raise SystemExit('S1 output exists: frozen data may not be overwritten; use a new version')
    DEST.mkdir(parents=True)
    manifest = {'version':'S1','status':'FROZEN SYNTHETIC; NOT BANK DATA','cohorts':{},'sources':{}}
    for p in [Path(__file__),ROOT/'scripts/generate_sme_portfolio.py',ROOT/'synthetic_bank/PROTOCOL.md']:
        manifest['sources'][str(p.relative_to(ROOT))] = sha(p)
    for name,(n,seed,date) in COHORTS.items():
        frames = generate_cohort(name,n,seed,date)
        dest = DEST/name
        dest.mkdir()
        for label,frame in zip(['borrowers','facilities','conduct','targets','workouts'],frames):
            if not frame.empty:
                write_csv(frame,dest/(label+'.csv.gz'))
        if name=='current':
            data = canonical(frames[0],frames[1],name,date)
            with gzip.GzipFile(filename=str(dest/'canonical.json.gz'),mode='wb',mtime=0) as stream:
                stream.write(data.model_dump_json().encode())
        manifest['cohorts'][name] = dict(n=n,seed=seed,observed_at=date)
        print(name, 'borrowers',len(frames[0]),'facilities',len(frames[1]),'workouts',len(frames[4]),flush=True)
    manifest['files'] = {str(p.relative_to(ROOT)):sha(p) for p in sorted(DEST.rglob('*.gz'))}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    main()
