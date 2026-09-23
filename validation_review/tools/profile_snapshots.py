"""Profile the selected immutable archive reruns created by reproduce_history.py.

Run after reproduce_history.py. Uses raw/generated artifacts only and records
whether comparability fails because the dataset or target was regenerated.
"""
from pathlib import Path
import csv
import glob
import hashlib
import json
import pandas as pd

DEST = Path(__file__).resolve().parents[1] / 'evidence'
history = pd.read_csv(DEST / 'historical_reproduction.csv')
rows = []
tails = []
experimental = []
for snap in history.snapshot:
    matches = sorted(glob.glob('/tmp/cra-history-' + snap + '-*'),
                     key=lambda p: Path(p).stat().st_mtime, reverse=True)
    if not matches:
        raise RuntimeError(f'Run reproduce_history.py first: no isolated rerun for {snap}')
    # Re-running the history reproducer creates new immutable temp directories.
    # Use the newest snapshot of each named phase, not an arbitrary glob result.
    base = Path(matches[0])
    raw = pd.read_csv(base / 'data/raw/sme_credit_portfolio.csv')
    scored_path = base / 'data/processed/scored_portfolio.csv'
    scored = pd.read_csv(scored_path) if scored_path.exists() else None
    val_path = base / 'outputs/model_validation.csv'
    val = pd.read_csv(val_path) if val_path.exists() else None
    governed = val.loc[val.Model.eq('Logistic Regression')].iloc[0] if val is not None else None
    hist_path = base / 'data/raw/lgd_workout_history.csv'
    workout = pd.read_csv(hist_path) if hist_path.exists() else None
    hold_path = base / 'outputs/lgd_holdout_predictions.csv'
    hold = pd.read_csv(hold_path) if hold_path.exists() else None
    entry = dict(snapshot=snap, raw_hash=hashlib.sha256((base/'data/raw/sme_credit_portfolio.csv').read_bytes()).hexdigest(),
                 borrowers=len(raw), raw_columns=len(raw.columns), raw_defaults=int(raw.default.sum()),
                 raw_default_rate=float(raw.default.mean()), raw_missing=json.dumps(raw.isna().sum().loc[lambda s:s>0].to_dict()),
                 raw_unique_borrowers=int(raw.customer_id.nunique()),
                 raw_industries=int(raw.industry.nunique()) if 'industry' in raw else '',
                 scored_count=len(scored) if scored is not None else '',
                 scored_stages=json.dumps(scored.stage.value_counts().to_dict()) if scored is not None and 'stage' in scored else '',
                 scored_exposure=float(scored.ead.sum()) if scored is not None and 'ead' in scored else '',
                 pd_auc=governed.get('ROC_AUC','') if governed is not None else '',
                 pd_ks=governed.get('KS','') if governed is not None else '',
                 pd_brier=governed.get('Brier','') if governed is not None else '',
                 pd_logloss=governed.get('LogLoss','') if governed is not None else '',
                 pd_mean=governed.get('Mean_PD','') if governed is not None else '',
                 pd_observed=governed.get('Observed_DR','') if governed is not None else '',
                 workout_hash=hashlib.sha256(hist_path.read_bytes()).hexdigest() if workout is not None else '',
                 workout_count=len(workout) if workout is not None else '',
                 workout_target_mean=float(workout.economic_lgd.mean()) if workout is not None else '',
                 workout_high_loss=int((workout.economic_lgd>.75).sum()) if workout is not None else '',
                 lgd_holdout_count=len(hold) if hold is not None else '',
                 lgd_holdout_mean=float(hold.economic_lgd.mean()) if hold is not None else '',
                 lgd_holdout_pred_mean=float(hold.predicted_lgd.mean()) if hold is not None else '')
    rows.append(entry)
    if hold is not None:
        for group, mask in [('all',hold.economic_lgd.notna()),
                            ('realized >75%',hold.economic_lgd>.75),
                            ('predicted top 10%',hold.predicted_lgd>=hold.predicted_lgd.quantile(.9))]:
            g=hold.loc[mask]
            diff=g.predicted_lgd-g.economic_lgd
            tails.append(dict(snapshot=snap, cohort=group, n=len(g),
                              realized_mean=float(g.economic_lgd.mean()),predicted_mean=float(g.predicted_lgd.mean()),
                              bias=float(diff.mean()),mae=float(diff.abs().mean()),rmse=float((diff.pow(2).mean())**.5)))
    files = {'woe_experiment':'outputs/experiments/woe_credit_scorecard/woe_vs_governed_validation.csv',
             'pca_experiment':'outputs/pca_logistic_challenger.csv',
             'bootstrap_experiment':'outputs/experiments/bootstrap_confidence_intervals/bootstrap_confidence_intervals.csv',
             'stress_experiment':'outputs/experiments/stress_sensitivity/stress_scenario_summary.csv'}
    if snap in files:
        experiment_frame=pd.read_csv(base/files[snap])
        for _, record in experiment_frame.iterrows():
            experimental.append(dict(snapshot=snap, source=files[snap],
                                     row_json=json.dumps(record.to_dict(),default=float)))
for path, collection in [('historical_data_profiles.csv', rows), ('historical_lgd_tails.csv', tails),
                         ('historical_experiments.csv', experimental)]:
    with (DEST/path).open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(collection[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(collection)
print('Profiled',len(rows),'snapshots and',len(tails),'LGD cohorts')
