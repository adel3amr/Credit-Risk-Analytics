"""Independently check frozen synthetic source/output data quality and write evidence.

Run after scripts/run_v5.py in a separate archived frozen V5 checkout.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT=Path(sys.argv[1]).resolve()
OUT=Path(__file__).resolve().parents[1]/'evidence'
raw=pd.read_csv(ROOT/'data/raw/sme_credit_portfolio.csv')
workout=pd.read_csv(ROOT/'data/raw/lgd_workout_history.csv')
hold=pd.read_csv(ROOT/'outputs/lgd_holdout_predictions.csv')
borrowers=pd.read_csv(ROOT/'outputs/borrower_audit_trace.csv')
facilities=pd.read_csv(ROOT/'outputs/facility_ecl_predictions.csv')
checks={}
def record(key, condition, detail=''):
    checks[key]=dict(passed=bool(condition), detail=str(detail))

record('borrower IDs unique/non-null',raw.customer_id.is_unique and raw.customer_id.notna().all())
record('workout facility IDs unique/non-null',workout.facility_id.is_unique and workout.facility_id.notna().all())
record('holdout facility IDs unique/non-null',hold.facility_id.is_unique and hold.facility_id.notna().all())
record('reporting facility IDs unique/non-null',facilities.facility_id.is_unique and facilities.facility_id.notna().all())
record('all reporting borrowers in raw',borrowers.customer_id.isin(raw.customer_id).all())
record('all scored facilities linked',facilities.customer_id.isin(borrowers.customer_id).all())
record('structural trade missingness only for no-trade accounts',raw.trade_type.isna().eq(raw.trade.eq(0)).all(),
       f'missing={raw.trade_type.isna().sum()}, zero trade={raw.trade.eq(0).sum()}')
record('all other raw fields complete',raw.drop(columns=['trade_type']).notna().all().all())
record('all workout fields complete',workout.notna().all().all())
record('finite financial and model values',all(np.isfinite(d[c]).all() for d,cols in [
    (raw,['ead','lgd','collateral_coverage','pd_true','loans','ovd','trade']),
    (workout,['ead_at_default','economic_lgd','pv_net_recovery','discount_rate']),
    (borrowers,['predicted_pd','forward_looking_pd_12m','ead','ecl']),
    (facilities,['ead_at_default','predicted_lgd','facility_pd_12m','facility_ecl'])] for c in cols))
record('nonnegative exposure and bounded probability/loss',
       raw.ead.ge(0).all() and workout.ead_at_default.gt(0).all()
       and borrowers.predicted_pd.between(0,1).all() and workout.economic_lgd.between(0,1).all()
       and facilities.predicted_lgd.between(0,1).all())
record('month history complete',len(pd.read_csv(ROOT/'data/raw/sme_behavioral_history_36m.csv'))==36*len(raw))
record('raw trade CCF identity',np.allclose(raw.trade_ead,raw.trade*raw.trade_ccf,rtol=0,atol=.02))
record('holdout workout outcome unchanged by join',
       hold.set_index('facility_id').economic_lgd.sort_index().equals(
           workout.set_index('facility_id').loc[hold.facility_id].economic_lgd.sort_index()))
record('no observed outcome columns in scored facility schema',
       not {'economic_lgd','cure_flag','pv_net_recovery','write_off_flag'} & set(facilities.columns))
detail=dict(raw_borrowers=len(raw),raw_columns=len(raw.columns),raw_future_defaults=int(raw.default.sum()),
            sectors=raw.industry.value_counts().to_dict(),
            structural_missing_trade_type=int(raw.trade_type.isna().sum()),
            resolved_workouts=len(workout),zero_or_negative_pv_recovery=int(workout.pv_net_recovery.le(0).sum()),
            observed_zero_lgd=int(workout.economic_lgd.eq(0).sum()),
            high_lgd_gt75=int(workout.economic_lgd.gt(.75).sum()),
            cured_workouts=int(workout.cure_flag.sum()),
            collateral_segments=workout.collateral_type.value_counts().to_dict(),
            reporting_borrowers=len(borrowers),reporting_facilities=len(facilities),
            reporting_products=facilities.product_type.value_counts().to_dict())
payload=dict(checks=checks,profile=detail)
(OUT/'frozen_data_quality.json').write_text(json.dumps(payload,indent=2)+'\n')
assert all(v['passed'] for v in checks.values()),[k for k,v in checks.items() if not v['passed']]
print(f'{sum(v["passed"] for v in checks.values())}/{len(checks)} data checks passed')
