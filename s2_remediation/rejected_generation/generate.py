"""Single versioned extension of historical economic support; never overwrites S2."""
import argparse
import json
import numpy as np
import pandas as pd
from credit_platform.common import ROOT, atomic_json, file_hash
from economic_lgd.economics import VERSION, RANGES, validate
from economic_lgd.recovery import simulate, BUCKETS
from economic_lgd.evaluate import verify as verify_s2
from synthetic_bank.generate import write_csv

DEST = ROOT / 's2_remediation/data'


def history(industries, start, quarters, seed):
    rng = np.random.default_rng(seed)
    # Persistent cycle with recovery distinct from deterioration; broad historical
    # cycles rather than copies of the operational scenario or its outcomes.
    dates = pd.date_range(start, periods=quarters, freq='QS')
    rows = []
    sector_shift = {s: rng.uniform(-3, 3) for s in industries}
    shocks = {s: 0.0 for s in industries}
    profile = np.array([-.6, 0, .5, 1.6, .7, -.6])
    for t, date in enumerate(dates):
        common = rng.normal(0, .35)
        for sector in industries:
            phase = ((t + sector_shift[sector]) % 40) / 8
            severity = np.interp(phase, np.arange(6), profile)
            shocks[sector] = .5 * shocks[sector] + rng.normal(0, .5)
            activity = 2 - 3.5 * severity + common + shocks[sector]
            labour = 5.5 + 1.7 * severity - .2 * activity + rng.normal(0, .9)
            price = 1.6 * activity - 2 * severity + rng.normal(0, 5)
            liquidity = .8 + .025 * activity - .2 * severity + rng.normal(0, .10)
            values = dict(zip(RANGES, [activity, labour, price, liquidity]))
            values = {k: float(np.clip(v, *RANGES[k])) for k, v in values.items()}
            rows.append(dict(industry=sector, reporting_date=str(date.date()),
                economic_period=str((date-pd.Timedelta(days=90)).date()),
                published_at=str((date-pd.Timedelta(days=1)).date()),
                economic_version=VERSION, latent_regime=int(severity >= .5),
                cycle_phase=['expansion','normal','deterioration','recession','recovery'][int(phase)],
                history_version='s2-r1-cycle-1', **values))
    result = pd.DataFrame(rows)
    validate(result)
    return result


def generate(destination=DEST):
    verify_s2()
    destination = destination.resolve()
    if destination.exists():
        raise ValueError('Frozen dataset exists; no overwrite')
    destination.mkdir(parents=True)
    manifest = dict(version='s2-r1-data-1', sources={}, cohorts={}, files={})
    specs = [('development','development',None,94001,'1950-01-01',240,3),
             ('calibration','selection',6000,94002,'2016-01-01',12,1),
             ('promotion','final',6000,94003,'2026-01-01',12,1)]
    for name, source, n, seed, start, quarters, repetitions in specs:
        fp = ROOT/f'synthetic_bank/data/{source}/facilities.csv.gz'
        bp = ROOT/f'synthetic_bank/data/{source}/borrowers.csv.gz'
        for p in (fp,bp): manifest['sources'][str(p.relative_to(ROOT))] = file_hash(p)
        frame = pd.read_csv(fp)
        if name == 'promotion':
            used_path = ROOT/'economic_lgd/data/final_inputs.csv.gz'
            manifest['sources'][str(used_path.relative_to(ROOT))] = file_hash(used_path)
            used = set(pd.read_csv(used_path).customer_id)
            frame = frame[~frame.customer_id.isin(used)]
        if n: frame = frame.sample(n, random_state=seed)
        frame = frame.sort_values('facility_id').reset_index(drop=True)
        borrowers = pd.read_csv(bp).set_index('customer_id')
        frame['interest_rate'] = frame.customer_id.map(borrowers.interest_rate)
        frame = frame.drop(columns=['downturn_at_default','observed_at'], errors='ignore')
        macro = history(sorted(frame.industry.unique()),start,quarters,seed)
        rng = np.random.default_rng(seed+100)
        repeats = []
        for rep in range(repetitions):
            f = frame.copy()
            borrower_dates = dict(zip(sorted(f.customer_id.unique()),
                rng.choice(sorted(macro.reporting_date.unique()),f.customer_id.nunique())))
            f['reporting_date'] = f.customer_id.map(borrower_dates)
            f['source_facility_id'] = f.facility_id
            f['facility_id'] = 's2r1-'+f.facility_id+'-'+str(rep)
            repeats.append(f.merge(macro,on=['industry','reporting_date'],validate='many_to_one'))
        x = pd.concat(repeats,ignore_index=True)
        y, cf = simulate(x,np.random.default_rng(seed+200),cashflows=True)
        outcomes = x[['facility_id','customer_id','reporting_date']].copy()
        outcomes['economic_lgd'] = y[:,0]
        outcomes['resolved_at'] = (pd.to_datetime(x.reporting_date)+pd.DateOffset(months=60)).dt.strftime('%Y-%m-%d')
        for j,m in enumerate(BUCKETS): outcomes[f'net_cf_{m}m'] = cf[:,0,j]
        write_csv(x,destination/f'{name}_inputs.csv.gz')
        write_csv(outcomes,destination/f'{name}_outcomes.csv.gz')
        write_csv(macro,destination/f'{name}_macro.csv.gz')
        manifest['cohorts'][name] = dict(n=len(x),borrowers=x.customer_id.nunique(),seed=seed,
            macro_clusters=len(macro),start=start,quarters=quarters,repeated_vintages=repetitions)
        print(name, manifest['cohorts'][name], flush=True)
    for p in sorted((ROOT/'s2_remediation').glob('*.py')):
        manifest['sources'][str(p.relative_to(ROOT))] = file_hash(p)
    manifest['sources']['s2_remediation/PROTOCOL.md'] = file_hash(ROOT/'s2_remediation/PROTOCOL.md')
    manifest['files'] = {p.name:file_hash(p) for p in sorted(destination.glob('*.gz'))}
    atomic_json(destination/'manifest.json',manifest)
    return manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=str)
    args=parser.parse_args()
    from pathlib import Path
    generate(Path(args.destination) if args.destination else DEST)
