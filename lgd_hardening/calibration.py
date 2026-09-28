"""Single smooth monotone calibration assessment using matured calibration only."""
import json
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from credit_platform.common import ROOT,atomic_json,file_hash
from economic_lgd.evaluate import metrics
from .audit import OUT

VERSION='s2-r1-continuous-calibration-1'


def fit(predicted,actual):
    x=np.asarray(predicted,dtype=float);y=np.asarray(actual,dtype=float)
    if len(x)!=len(y) or len(x)<6000 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Invalid calibration inputs')
    if ((x<0)|(x>1)|(y<0)|(y>1)).any():raise ValueError('Invalid LGD')
    indices=np.argsort(x,kind='stable')
    bins=np.array_split(indices,20)
    xx=np.array([x[i].mean() for i in bins]);yy=np.array([y[i].mean() for i in bins])
    weights=np.array([len(i) for i in bins])
    iso=IsotonicRegression(y_min=0,y_max=1,increasing=True,out_of_bounds='clip').fit(xx,yy,sample_weight=weights)
    return dict(version=VERSION,x=iso.X_thresholds_.tolist(),y=iso.y_thresholds_.tolist(),
                bins=20,minimum_bin_n=int(weights.min()),tail_behavior='flat extension beyond learned knots')


def predict(calibration,raw):
    values=np.asarray(raw,dtype=float)
    if not np.isfinite(values).all() or ((values<0)|(values>1)).any():raise ValueError('Invalid raw LGD')
    return np.interp(values,calibration['x'],calibration['y'])


def main():
    from s2_remediation.evaluate import verify,verify_lock
    verify();verify_lock()
    evidence=json.loads((ROOT/'s2_remediation/results/decision.json').read_text())
    for name,h in evidence['source_hashes'].items():
        if file_hash(ROOT/name)!=h:raise ValueError('Frozen calibration/validation evidence mismatch')
    path=ROOT/'s2_remediation/results/calibration_predictions.csv'
    if (OUT/'calibration.json').exists():raise ValueError('Existing candidate: no overwrite/tuning')
    fitting=pd.read_csv(path).query("scenario=='baseline'")
    cal=fit(fitting.corrected,fitting.actual)
    cal['fit_source_sha256']=file_hash(path)
    cal['fit_rows']=len(fitting)
    cal['excluded_fit_sources']=['current','promotion','conditional_mean','hidden qualities']
    atomic_json(OUT/'calibration.json',cal)
    rows=[];summaries=[];bands=[]
    for cohort in ['current','promotion']:
        pp=ROOT/f's2_remediation/results/{cohort}_predictions.csv'
        fp=ROOT/('economic_lgd/data/current_inputs.csv.gz' if cohort=='current' else 's2_remediation/data/promotion_inputs.csv.gz')
        frame=pd.read_csv(fp).set_index('facility_id')
        observations=pd.read_csv(pp)
        observations['calibrated']=predict(cal,observations.corrected)
        observations.to_csv(OUT/f'{cohort}_calibration_engineering.csv',index=False)
        for scenario,g in observations.groupby('scenario'):
            x=frame.loc[g.facility_id].reset_index()
            y=g.actual.to_numpy();mu=g.conditional_mean.to_numpy()
            for model,p in [('r1',g.corrected.to_numpy()),('calibrated',g.calibrated.to_numpy())]:
                values=metrics(x,y,p,mu,model,cohort)
                for v in values:v['scenario']=scenario;v['role']='KNOWN ENGINEERING ONLY'
                rows.extend(values)
            for lo in [0,.2,.4,.6,.8]:
                original_band=g[g.corrected.between(lo,lo+.2,inclusive='left')]
                if len(original_band):bands.append(dict(cohort=cohort,scenario=scenario,
                    original_band=lo,n=len(original_band),
                    r1_bias=float((original_band.corrected-original_band.conditional_mean).mean()),
                    calibrated_bias=float((original_band.calibrated-original_band.conditional_mean).mean())))
        pivot=observations.pivot(index='facility_id',columns='scenario',values='calibrated')
        summaries.append(dict(cohort=cohort,reversals=int(((pivot.upside>pivot.baseline+1e-10)|
                            (pivot.baseline>pivot.downside+1e-10)).sum())))
    pd.DataFrame(rows).to_csv(OUT/'calibration_engineering_metrics.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'original_band_calibration.csv',index=False)
    atomic_json(OUT/'calibration_engineering.json',dict(version=VERSION,shape=summaries,
        status='DEVELOPMENT_NOT_PROMOTED',new_final_holdout_used=False))
    print(pd.DataFrame(rows).query("model=='calibrated' and group in ['all','guarantee:full','predicted:0.8']")[[
        'cohort','scenario','group','n','conditional_bias','conditional_bias_se','mae','rmse']].to_string(index=False))


if __name__=='__main__':main()
