"""WN-1 reference feature contract. Real institution capture remains unvalidated."""
import numpy as np
from .generate import FEATURES
CATEGORIES={'industry':['Manufacturing','Retail','Services','Construction'],'product':['Term Loan','OVD'],'collateral_type':['none','cash','property','other']}
RANGES={n:(0,None) for n in FEATURES}
RANGES.update({n:(0,1) for n in ['predefault_pd','utilization','recovered_ratio','haircut','guarantee_ratio','guarantor_quality','enforceability','enforcement','claim','restructured']})
RANGES.update(predefault_rating=(1,7),lien=(1,2),financial_strength=(None,None),rating_migration=(None,None),growth=(None,None),price_change=(None,None))
SOURCES={
'credit_snapshot':['predefault_pd','predefault_rating','rating_migration','financial_strength','previous_defaults','utilization','delinquency'],
'default_event':['age'],'recovery_transaction':['months_since_last_recovery','recovered_ratio'],
'collateral_valuation':['collateral_ratio','haircut','lien'],'collateral_enforcement':['enforcement'],
'guarantee':['guarantee_ratio','guarantor_quality','enforceability'],'guarantee_claim':['claim'],
'restructure_event':['restructured'],'workout_cost':['cost_ratio'],'macro_snapshot':['growth','unemployment','price_change'],
'facility':['rate','ead'],'interest_accrual':['mi_ratio']}

def check(x):
    for name,(low,high) in RANGES.items():
        if name not in x:raise ValueError('Missing WN feature '+name)
        v=x[name]
        if v.dtype.kind not in 'iuf' or v.isna().any() or not np.isfinite(v).all():raise ValueError('Invalid WN numeric '+name)
        if (low is not None and (v<low).any()) or (high is not None and (v>high).any()):raise ValueError('WN range violation '+name)
    if (x.ead<=0).any():raise ValueError('Positive remaining EAD required')
    for name,values in CATEGORIES.items():
        if name not in x or not x[name].isin(values).all():raise ValueError('Invalid WN category '+name)
    return x
