"""Scenario-specific expected-loss integration; shadow only until promotion."""
import math
import numpy as np
import pandas as pd
from .economics import scenario_frame
from .model import predict


def ecl_components(stage, ead, months, pds, lgds, scenarios):
    if stage not in ('Stage 1','Stage 2','Stage 3'):
        raise ValueError('Invalid stage')
    if not all(math.isfinite(v) and v>=0 for v in (ead,months)):
        raise ValueError('Invalid exposure/maturity')
    names = [s['scenario'] for s in scenarios]
    if len(names)!=len(set(names)) or set(names)!=set(pds) or set(names)!=set(lgds):
        raise ValueError('Scenario contract mismatch')
    if not math.isclose(sum(s['weight'] for s in scenarios),1,abs_tol=1e-12):
        raise ValueError('Weights must sum to one')
    rows=[]
    for s in scenarios:
        name=s['scenario']; p=pds[name]; lgd=lgds[name]; weight=s['weight']
        if not all(math.isfinite(v) and 0<=v<=1 for v in (p,lgd,weight)):
            raise ValueError('Invalid probability/LGD/weight')
        effective=1 if stage=='Stage 3' else 1-(1-p)**(months/12) if stage=='Stage 2' else p
        rows.append(dict(scenario=name,weight=weight,pd=p,effective_pd=effective,
            lgd=lgd,ead=ead,ecl=effective*lgd*ead,weighted_ecl=weight*effective*lgd*ead))
    return rows


def shadow(frame,traces,model,scenarios):
    baseline=next(s for s in scenarios if s['scenario']=='baseline')
    predictions={s['scenario']:predict(model,scenario_frame(frame,s,baseline)) for s in scenarios}
    indexed={t['facility_id']:t for t in traces}
    if set(indexed)!=set(frame.facility_id) or len(indexed)!=len(frame):
        raise ValueError('Facility identities do not reconcile')
    rows=[]
    for i,f in enumerate(frame.itertuples()):
        t=indexed[f.facility_id]
        lgds={name:float(p[i]) for name,p in predictions.items()}
        components=ecl_components(t['stage'],t['ead'],t['remaining_months'],t['scenario_pd'],lgds,scenarios)
        old=ecl_components(t['stage'],t['ead'],t['remaining_months'],t['scenario_pd'],
                           {s['scenario']:t['lgd'] for s in scenarios},scenarios)
        row=dict(facility_id=f.facility_id,borrower_id=t['borrower_id'],stage=t['stage'],
            ead=t['ead'],legacy_ecl=t['ecl'],
            incumbent_scenario_order_ecl=sum(s['weighted_ecl'] for s in old),
            corrected_ecl=sum(s['weighted_ecl'] for s in components))
        for c in components:
            row['lgd_'+c['scenario']]=c['lgd']
            row['ecl_'+c['scenario']]=c['ecl']
        rows.append(row)
    result=pd.DataFrame(rows)
    # Independent arithmetic from stored scenario rows, not ecl_components().
    recalculated=[]
    for i,f in enumerate(frame.itertuples()):
        t=indexed[f.facility_id]; total=0.
        for s in scenarios:
            p=t['scenario_pd'][s['scenario']]
            if t['stage']=='Stage 3': p=1.
            elif t['stage']=='Stage 2': p=-math.expm1(math.log1p(-p)*t['remaining_months']/12) if p<1 else float(t['remaining_months']>0)
            total+=s['weight']*t['ead']*predictions[s['scenario']][i]*p
        recalculated.append(total)
    error=float(np.max(np.abs(result.corrected_ecl-np.array(recalculated))))
    portfolio=float(result.corrected_ecl.sum())
    borrower=float(result.groupby('borrower_id').corrected_ecl.sum().sum())
    if error>1e-7 or abs(portfolio-borrower)>1e-6:
        raise ValueError('Independent ECL reconciliation failed')
    return result,dict(max_facility_error=error,aggregation_error=abs(portfolio-borrower),
        legacy_ecl=float(result.legacy_ecl.sum()),
        incumbent_scenario_order_ecl=float(result.incumbent_scenario_order_ecl.sum()),
        corrected_ecl=portfolio,
        ordering_violations=int(((result.lgd_downside<result.lgd_baseline-1e-12)|
                                 (result.lgd_baseline<result.lgd_upside-1e-12)).sum()),
        scenario_mean_lgd={s['scenario']:float(result['lgd_'+s['scenario']].mean()) for s in scenarios},
        status='SHADOW ONLY; NO BOOKED ADJUSTMENT')
