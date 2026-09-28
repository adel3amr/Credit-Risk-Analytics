"""Shared domain boundary: declared economics is not validated model support."""
import math
import numpy as np
import pandas as pd
from economic_lgd.economics import RANGES,validate

VERSION='lgd-economic-domain-1'


def scenario_inputs(frame,scenario,baseline):
    validate(frame)
    dg=float(scenario['real_gdp_growth_pct'])-float(baseline['real_gdp_growth_pct'])
    du=float(scenario['unemployment_rate_pct'])-float(baseline['unemployment_rate_pct'])
    if not all(math.isfinite(v) for v in [dg,du]):raise ValueError('Invalid scenario delta')
    out=frame.copy()
    for field,delta in dict(output_growth_pct=dg,unemployment_pct=du,
            collateral_change_pct=2*dg-du,liquidity=.035*dg-.025*du).items():
        out[field]=out[field]+delta
    # Unlike the historical mapper, this boundary does not silently truncate a
    # scenario. Report the unsupported scenario instead of changing its meaning.
    outside=np.zeros(len(out),dtype=bool)
    for field,(lo,hi) in RANGES.items():outside|=~out[field].between(lo,hi).to_numpy()
    return out,outside


def assess(frame,support,scenarios):
    if frame.facility_id.duplicated().any():raise ValueError('Duplicate facility')
    names=[s['scenario'] for s in scenarios]
    if len(names)!=len(set(names)) or set(names)!={'upside','baseline','downside'}:
        raise ValueError('Invalid scenario identities')
    weights=[s['weight'] for s in scenarios]
    if not all(math.isfinite(w) and 0<=w<=1 for w in weights) or not math.isclose(sum(weights),1,abs_tol=1e-12):
        raise ValueError('Invalid scenario weights')
    baseline=next(s for s in scenarios if s['scenario']=='baseline')
    reports=[]
    for s in scenarios:
        shifted,invalid=scenario_inputs(frame,s,baseline)
        report=pd.DataFrame({'facility_id':frame.facility_id.to_numpy(),
            'scenario':s['scenario'],'supported':False,'reason':'OUTSIDE_DECLARED_ECONOMIC_DOMAIN'})
        positions=np.flatnonzero(~invalid)
        if len(positions):
            inspected=support.inspect(shifted.iloc[positions].reset_index(drop=True))
            report.loc[positions,'supported']=inspected.supported.to_numpy()
            report.loc[positions,'reason']=np.where(inspected.supported,
                'SUPPORTED_INPUT_ONLY_PROMOTION_STILL_REQUIRED','OUTSIDE_VALIDATED_MODEL_SUPPORT')
        report['expected_lgd']=None
        report['sensitivity_lgd_lower']=0.0
        report['sensitivity_lgd_upper']=1.0
        report['bound_status']='NONBOOKABLE_BOUND_NOT_EXPECTED_LGD'
        report['domain_version']=VERSION
        reports.append(report)
    return pd.concat(reports,ignore_index=True)
