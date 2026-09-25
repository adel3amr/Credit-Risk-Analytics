"""Predeclared S1 model comparison. Separate selection and single final execution."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss,roc_curve
from src.data_preparation import prepare_data,pd_feature_columns
from src.pd_model import logistic_model
from src.lgd_model import gradient_boosting_lgd_model,NUMERIC_FEATURES
from lgd_research.run_study import model,NEW_NUM
from credit_platform import artifacts
from credit_platform.validation import loss_metrics
from synthetic_bank.generate import ROOT,DEST,sha

RESULTS=ROOT/'synthetic_bank/results'


def verify_data():
    freeze=json.loads((ROOT/'synthetic_bank/DATA_FREEZE.json').read_text())
    assert sha(DEST/'manifest.json')==freeze['manifest_sha256']
    manifest=json.loads((DEST/'manifest.json').read_text())
    for path,digest in {**manifest['files'],**manifest['sources']}.items():
        assert sha(ROOT/path)==digest,path


def data(name):
    base=DEST/name
    b=pd.read_csv(base/'borrowers.csv.gz')
    t=pd.read_csv(base/'targets.csv.gz')
    b=b.merge(t[['customer_id','at_risk','default_12m']],on='customer_id',validate='one_to_one')
    b=b[b.at_risk.eq(1)].copy()
    f=pd.read_csv(base/'facilities.csv.gz')
    w=pd.read_csv(base/'workouts.csv.gz')
    w=f.merge(w,on=['facility_id','customer_id'],validate='one_to_one')
    return b,w


def score(models,columns,b,w,phase):
    rows=[]; predictions=w[['facility_id','customer_id','economic_lgd','ead_at_default']].copy()
    for name in ['frozen_v5','s1_same_spec','s1_captured_features']:
        p=np.clip(models[name].predict(w),0,1)
        predictions[name]=p
        metrics=loss_metrics(w.economic_lgd.tolist(),p.tolist(),w.ead_at_default.tolist())
        for m in metrics:
            rows.append(dict(phase=phase,model=name,**m))
        for col in ['collateral_type','product_type']:
            for segment in sorted(w[col].unique()):
                mask=w[col].eq(segment)
                m=loss_metrics(w.loc[mask,'economic_lgd'].tolist(),p[mask].tolist(),w.loc[mask,'ead_at_default'].tolist())[0]
                rows.append(dict(phase=phase,model=name,**{**m,'cohort':col+':'+segment}))
        for low,high in zip([0,.2,.4,.6,.8],[.2,.4,.6,.8,1]):
            mask=(p>=low)&((p<high) if high<1 else (p<=high))
            if mask.any():
                m=loss_metrics(w.loc[mask,'economic_lgd'].tolist(),p[mask].tolist(),w.loc[mask,'ead_at_default'].tolist())[0]
                rows.append(dict(phase=phase,model=name,**{**m,'cohort':f'predicted_{low:.1f}_{high:.1f}'}))
    pd.DataFrame(rows).to_csv(RESULTS/(phase+'_lgd.csv'),index=False)
    predictions.to_csv(RESULTS/(phase+'_predictions.csv'),index=False)
    x=prepare_data(b); y=b.default_12m.astype(int).to_numpy(); pdrows=[]; calibration=[]
    for name in ['frozen_pd','s1_pd']:
        p=models[name].predict_proba(x.reindex(columns=columns[name],fill_value=0))[:,1]
        auc=roc_auc_score(y,p); fpr,tpr,_=roc_curve(y,p)
        pdrows.append(dict(model=name,n=len(y),defaults=int(y.sum()),auc=auc,gini=2*auc-1,
            ks=float(np.max(tpr-fpr)),brier=brier_score_loss(y,p),log_loss=log_loss(y,p),
            observed=float(y.mean()),predicted=float(p.mean())))
        for lo,hi in zip([0,.01,.025,.05,.1,.2],[.01,.025,.05,.1,.2,1]):
            mask=(p>=lo)&(p<hi)
            calibration.append(dict(model=name,lower=lo,upper=hi,n=int(mask.sum()),
                predicted=float(p[mask].mean()) if mask.any() else None,
                observed=float(y[mask].mean()) if mask.any() else None))
    pd.DataFrame(pdrows).to_csv(RESULTS/(phase+'_pd.csv'),index=False)
    pd.DataFrame(calibration).to_csv(RESULTS/(phase+'_pd_calibration.csv'),index=False)
    print(pd.DataFrame(rows).query("cohort in ['all','realized_gt75']")[['model','cohort','n','mae','rmse','bias']].to_string(index=False))
    print(pd.DataFrame(pdrows).to_string(index=False))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['selection','final'])
    args=parser.parse_args(); verify_data()
    if args.phase=='selection':
        if RESULTS.exists():
            raise SystemExit('Results already exist; no retuning or overwriting')
        RESULTS.mkdir()
        b,w=data('development')
        incumbent,manifest=artifacts.load()
        x=prepare_data(b); cols=pd_feature_columns(x)
        models={'frozen_v5':joblib.load(ROOT/'lgd_research/results/a_v5_h.joblib'),
            's1_same_spec':gradient_boosting_lgd_model().fit(w,w.economic_lgd),
            's1_captured_features':model(NUMERIC_FEATURES+NEW_NUM).fit(w,w.economic_lgd),
            'frozen_pd':incumbent['pd'],
            's1_pd':logistic_model().fit(x[cols],b.default_12m.astype(int))}
        columns={'frozen_pd':manifest['pd_columns'],'s1_pd':cols}
        joblib.dump((models,columns),RESULTS/'candidates.joblib')
        sb,sw=data('selection'); score(models,columns,sb,sw,'selection')
        lock=dict(status='RESEARCH ONLY; ALL THREE LGD CANDIDATES RETAINED; NO TUNING',
            artifact_hash=sha(RESULTS/'candidates.joblib'),data_manifest_hash=sha(DEST/'manifest.json'),
            evaluation_source_hash=sha(__file__),n_training_workouts=len(w),n_training_borrowers=len(b))
        (RESULTS/'FINAL_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n')
    else:
        lock=json.loads((RESULTS/'FINAL_LOCK.json').read_text())
        assert lock['artifact_hash']==sha(RESULTS/'candidates.joblib')
        assert lock['data_manifest_hash']==sha(DEST/'manifest.json')
        assert lock['evaluation_source_hash']==sha(__file__)
        # Exclusive marker written before opening final data. A failure requires a
        # documented recovery, not silently restarting selection.
        with (RESULTS/'FINAL_OPENED.json').open('x') as stream:
            json.dump(lock,stream,indent=2)
        models,columns=joblib.load(RESULTS/'candidates.joblib')
        b,w=data('final'); score(models,columns,b,w,'final')


if __name__=='__main__':
    main()
