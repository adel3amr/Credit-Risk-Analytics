"""Independent S1 data audit; does not fit or score any model."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from synthetic_bank.generate import ROOT, DEST, sha, canonical


def validate_cohort(b,f,h,t,w):
    assert b.customer_id.is_unique and f.facility_id.is_unique
    assert set(f.customer_id)<=set(b.customer_id)
    assert set(h.customer_id)==set(b.customer_id)
    assert h.groupby('customer_id').size().eq(36).all()
    assert pd.to_datetime(h.observed_at).max()<=pd.to_datetime(b.observed_at).max()
    assert not {'default','pd_true','economic_lgd','cure_flag'} & set(b)
    assert not {'economic_lgd','cure_flag','pv_net_recovery'} & set(f)
    assert f.guarantee_coverage.between(0,1).all()
    assert f.loc[f.guarantee_coverage.eq(0),'guarantor_strength'].eq(0).all()
    assert f.loc[f.collateral_type.eq('Unsecured'),'collateral_coverage'].eq(0).all()
    totals=f.groupby('customer_id').ead_at_default.sum()
    allocated=f.groupby('customer_id').allocated_collateral_value.sum()
    np.testing.assert_allclose(totals.sort_index(),b.set_index('customer_id').ead.sort_index(),rtol=1e-10)
    np.testing.assert_allclose(allocated.sort_index(),b.set_index('customer_id').collateral_value.sort_index(),rtol=1e-10)
    if not w.empty:
        assert w.facility_id.is_unique
        assert set(w.facility_id)<=set(f.facility_id)
        joined=w.merge(f[['facility_id','ead_at_default']],on='facility_id',validate='one_to_one')
        net=joined[[f'recovery_cf_{m}m' for m in (1,6,12,24,36,60)]].to_numpy()
        pv=np.sum(net/(1+joined.discount_rate.to_numpy()[:,None])**(np.array([1,6,12,24,36,60])/12),axis=1)
        np.testing.assert_allclose(pv,joined.pv_net_recovery,rtol=1e-9,atol=1e-6)
        np.testing.assert_allclose(np.clip(1-pv/joined.ead_at_default,0,1),joined.economic_lgd,atol=1e-9)
        gross=joined[['collateral_recovery','guarantee_recovery','unsecured_recovery','cure_recovery']].sum(axis=1)
        assert (gross<=joined.ead_at_default+1e-5).all()
        np.testing.assert_allclose(net.sum(axis=1),gross-joined.workout_cost,rtol=1e-9,atol=1e-5)
        assert w.groupby('customer_id').cure_flag.nunique().le(1).all()
        expected=set(f.loc[f.customer_id.isin(t.loc[t.default_date.notna(),'customer_id']),'facility_id'])
        assert set(w.facility_id)==expected
        assert (pd.to_datetime(w.resolved_at)>pd.to_datetime(w.default_date)).all()
    return dict(borrowers=len(b),facilities=len(f),conduct_rows=len(h),workouts=len(w),
        zero_guarantee_share=float(f.guarantee_coverage.eq(0).mean()),
        default_rate=float(t.default_12m.mean()) if not t.empty else None,
        lgd_gt75=int(w.economic_lgd.gt(.75).sum()) if not w.empty else None,
        lgd_le10=int(w.economic_lgd.le(.1).sum()) if not w.empty else None,
        economic_loss_gt100=int(w.unbounded_economic_lgd.gt(1).sum()) if not w.empty else None)


def load(name):
    return tuple(pd.read_csv(DEST/name/(label+'.csv.gz')) if (DEST/name/(label+'.csv.gz')).exists() else pd.DataFrame()
                 for label in ['borrowers','facilities','conduct','targets','workouts'])


def main():
    manifest=json.loads((DEST/'manifest.json').read_text())
    for path,digest in {**manifest['files'],**manifest['sources']}.items():
        assert sha(ROOT/path)==digest, path
    all_ids=set(); results={}; previous_end=None
    for name,config in manifest['cohorts'].items():
        b,f,h,t,w=load(name)
        assert not all_ids & set(b.customer_id)
        all_ids.update(b.customer_id)
        if previous_end is not None:
            assert previous_end < pd.Timestamp(config['observed_at'])
        if not w.empty:
            previous_end=pd.to_datetime(w.resolved_at).max()
        results[name]=validate_cohort(b,f,h,t,w)
        # Validate all records through the canonical contract in bounded chunks.
        for start in range(0,len(b),10000):
            chunk=b.iloc[start:start+10000]
            canonical(chunk,f[f.customer_id.isin(chunk.customer_id)],name,config['observed_at'])
    evidence=dict(status='DATA CHECKS PASSED; NO MODEL APPROVAL',manifest_sha256=sha(DEST/'manifest.json'),cohorts=results)
    (ROOT/'synthetic_bank/DATA_FREEZE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':
    main()
