"""Read-only, production-function-free recalculation of a frozen V5 build.

Run: python validation_review/tools/independent_recalculation.py /path/to/clean/v5
All outputs are written into the review package, never into the V5 snapshot.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEST = Path(__file__).resolve().parents[1] / 'evidence'
DEST.mkdir(parents=True, exist_ok=True)
ROOT = Path(sys.argv[1]).resolve()
OUT = ROOT / 'outputs'


def metrics(actual, prediction, weight=None):
    a, p = np.asarray(actual, float), np.asarray(prediction, float)
    d = p - a
    w = np.ones(len(a)) if weight is None else np.asarray(weight, float)
    return dict(n=len(a), actual_mean=float(a.mean()), predicted_mean=float(p.mean()),
                bias=float(d.mean()), mae=float(np.abs(d).mean()),
                rmse=float(np.sqrt(np.mean(d*d))), weighted_bias=float(np.average(d, weights=w)),
                weighted_mae=float(np.average(np.abs(d), weights=w)))


hist = pd.read_csv(ROOT / 'data/raw/lgd_workout_history.csv')
hold = pd.read_csv(OUT / 'lgd_holdout_predictions.csv')
borrower = pd.read_csv(OUT / 'borrower_audit_trace.csv')
facility = pd.read_csv(OUT / 'facility_ecl_predictions.csv')
assert hold.facility_id.is_unique and hist.facility_id.is_unique
joined = hold.merge(hist, on='facility_id', validate='one_to_one', suffixes=('', '_source'))
assert len(joined) == len(hold) == 2000
assert np.max(np.abs(joined.economic_lgd - joined.economic_lgd_source)) < 1e-12

groups = [('all', np.ones(len(joined), dtype=bool)),
          ('realized <=10%', joined.economic_lgd <= .1),
          ('realized >60%', joined.economic_lgd > .6),
          ('realized >75%', joined.economic_lgd > .75),
          ('realized >=90%', joined.economic_lgd >= .9),
          ('realized >=97%', joined.economic_lgd >= .97),
          ('predicted top 10%', joined.predicted_lgd >= joined.predicted_lgd.quantile(.9)),
          ('predicted top 5%', joined.predicted_lgd >= joined.predicted_lgd.quantile(.95))]
for column in ['collateral_type', 'product_type', 'lien_rank', 'industry', 'cure_flag']:
    groups.extend((f'{column}={key}', joined[column].eq(key)) for key in sorted(joined[column].unique()))
segment = pd.DataFrame([dict(segment=name, **metrics(g.economic_lgd, g.predicted_lgd, g.ead_at_default))
                        for name, mask in groups if len(g := joined.loc[mask])])
segment.to_csv(DEST / 'independent_lgd_segments.csv', index=False)

cal = joined.assign(decile=pd.qcut(joined.predicted_lgd.rank(method='first'), 10, labels=False) + 1)
pd.DataFrame([dict(decile=int(k), **metrics(g.economic_lgd, g.predicted_lgd, g.ead_at_default))
              for k, g in cal.groupby('decile')]).to_csv(DEST / 'independent_lgd_calibration.csv', index=False)

# Outcome and cashflow invariants are independently constructed from raw fields.
pv = sum(hist[f'recovery_cf_{m}m'].to_numpy() / (1 + hist.discount_rate.to_numpy()) ** (m/12)
         for m in (1, 6, 12, 24, 36, 60))
pv_lgd = np.clip(1 - pv/hist.ead_at_default.to_numpy(), 0, 1)
target_max = float(np.max(np.abs(pv_lgd - hist.economic_lgd.to_numpy())))
assert target_max < 5e-5
assert (hist.economic_lgd.between(0, 1)).all()

# Avoid any package's model metric functions; tied ranks use the mean rank.
y = borrower.default.to_numpy(dtype=int)
p = borrower.predicted_pd.to_numpy(dtype=float)
n1, n0 = int(y.sum()), int((1-y).sum())
ranks = pd.Series(p).rank(method='average').to_numpy()
auc = float((ranks[y == 1].sum() - n1*(n1+1)/2) / (n1*n0))
order = np.argsort(-p, kind='stable')
fpr = np.cumsum(1-y[order]) / n0
tpr = np.cumsum(y[order]) / n1
ks = float(np.max(np.abs(tpr-fpr)))
pe = np.clip(p, 1e-15, 1-1e-15)
pd_metrics = dict(n=len(p), defaults=n1, observed_default_rate=float(y.mean()),
                  predicted_mean=float(p.mean()), auc=auc, gini=2*auc-1, ks=ks,
                  brier=float(np.mean((p-y)**2)),
                  log_loss=float(-np.mean(y*np.log(pe)+(1-y)*np.log1p(-pe))))
saved = pd.read_csv(OUT / 'model_validation.csv').set_index('Model').loc['Logistic Regression']
metric_diffs = {key: float(pd_metrics[ours] - saved[reported]) for ours, reported, key in
                [('auc','ROC_AUC','auc'), ('gini','Gini','gini'), ('ks','KS','ks'),
                 ('brier','Brier','brier'), ('log_loss','LogLoss','log_loss')]}

sig = (borrower.utilization_6m_change.fillna(0).ge(.10).astype(int)
       + (borrower.avg_utilization_6m.fillna(0).ge(.80)
          | borrower.months_above_80_utilization.fillna(0).ge(3)).astype(int)
       + borrower.limit_breach_count.fillna(0).ge(1).astype(int))
direction = np.where(sig >= 2, 'Deteriorating', np.where(sig == 1, 'Watch', 'Stable'))
ews = sig >= 2
s3 = (borrower.current_credit_impaired == 1) | (borrower.days_past_due >= 90)
s2 = ~s3 & ((borrower.days_past_due >= 30) | (borrower.delinquencies_12m >= 2)
            | ((borrower.credit_utilization >= .85) & (borrower.days_past_due > 0))
            | ((borrower.previous_defaults >= 1) & (borrower.predicted_pd >= .05))
            | (ews & (borrower.consecutive_ews_months >= 9)))
stage = np.where(s3, 'Stage 3', np.where(s2, 'Stage 2', 'Stage 1'))
stage_errors = int((stage != borrower.stage).sum())
ews_errors = int((direction != borrower.risk_direction).sum())
assert stage_errors == ews_errors == 0

macro = pd.read_csv(ROOT / 'config/macro_scenarios.csv')
baseline = macro.loc[macro.scenario.str.lower() == 'baseline'].iloc[0]
betas = {'real_gdp_growth_pct': -.10, 'unemployment_rate_pct': .08,
         'policy_rate_pct': .06, 'inflation_pct': .03}
odds = p/(1-p)
scenario = []
for _, row in macro.iterrows():
    mult = np.exp(sum(v*(row[k]-baseline[k]) for k,v in betas.items()))
    scenario.append((row.weight, odds*mult/(1+odds*mult)))
forward = sum(w*sp for w,sp in scenario)
forward_max = float(np.max(np.abs(forward-borrower.forward_looking_pd_12m.to_numpy())))

assert facility.facility_id.is_unique and borrower.customer_id.is_unique
assert facility.customer_id.isin(borrower.customer_id).all()
f = facility.merge(borrower[['customer_id','stage','forward_looking_pd_12m']],
                   on='customer_id', suffixes=('', '_borrower'), validate='many_to_one')
life = 1 - (1-f.forward_looking_pd_12m.to_numpy())**(f.remaining_months.to_numpy()/12)
effective = np.where(f.stage.eq('Stage 3'), 1, np.where(f.stage.eq('Stage 2'), life,
                                                               f.forward_looking_pd_12m))
expected = effective*f.predicted_lgd.to_numpy()*f.ead_at_default.to_numpy()
max_ecl_error = float(np.max(np.abs(expected-f.facility_ecl.to_numpy())))
max_life_error = float(np.max(np.abs(life-f.facility_lifetime_pd.to_numpy())))
fagg = f.groupby('customer_id')[['ead_at_default','facility_ecl']].sum()
bagg = borrower.set_index('customer_id').join(fagg)
ead_error = float(np.max(np.abs(bagg.ead-bagg.ead_at_default)))
borrower_ecl_error = float(np.max(np.abs(bagg.ecl-bagg.facility_ecl)))
assert max_ecl_error < .02 and max_life_error < 1e-12
assert ead_error < .02 and borrower_ecl_error < .02 and forward_max < 1e-12

traces = []
for label in ['Stage 1','Stage 2','Stage 3']:
    g = f.loc[f.stage == label].iloc[0]
    borrower_row=borrower.set_index('customer_id').loc[g.customer_id]
    traces.append(dict(stage=label, customer_id=g.customer_id, facility_id=g.facility_id,
                       product_type=g.product_type, collateral_type=g.collateral_type,
                       lien_rank=g.lien_rank, guarantee_coverage=g.guarantee_coverage,
                       leverage_ratio=borrower_row.leverage_ratio,
                       credit_utilization=borrower_row.credit_utilization,
                       days_past_due=borrower_row.days_past_due,
                       current_credit_impaired=borrower_row.current_credit_impaired,
                       consecutive_ews_months=borrower_row.consecutive_ews_months,
                       risk_direction=borrower_row.risk_direction,
                       risk_rating=borrower_row.risk_rating,
                       borrower_predicted_pd=borrower_row.predicted_pd,
                       pd_12m=g.forward_looking_pd_12m, remaining_months=g.remaining_months,
                       lifetime_pd=1-(1-g.forward_looking_pd_12m)**(g.remaining_months/12),
                       effective_pd=1 if label == 'Stage 3' else
                                    (1-(1-g.forward_looking_pd_12m)**(g.remaining_months/12)
                                     if label == 'Stage 2' else g.forward_looking_pd_12m),
                       lgd=g.predicted_lgd, ead=g.ead_at_default,
                       independent_ecl=float(expected[g.name]), recorded_ecl=g.facility_ecl))
pd.DataFrame(traces).to_csv(DEST / 'independent_facility_traces.csv', index=False)

checks = dict(frozen_v5=str(ROOT), lgd_sample=len(hist), holdout=len(hold),
              workout_target_max_error=target_max,
              lgd_clipped=int((~hold.raw_predicted_lgd.between(0, 1)).sum()),
              ews_mismatches=ews_errors, stage_mismatches=stage_errors,
              forward_pd_max_error=forward_max, ecl_facility_max_error=max_ecl_error,
              lifetime_pd_max_error=max_life_error, borrower_ecl_max_error=borrower_ecl_error,
              borrower_ead_max_error=ead_error, pd_metrics=pd_metrics,
              reported_pd_metric_differences=metric_diffs,
              total_ead=float(borrower.ead.sum()), total_ecl=float(borrower.ecl.sum()),
              stage_counts=borrower.stage.value_counts().to_dict(),
              watchlist_count=int(borrower.risk_rating.eq(7).sum()))
(DEST / 'independent_reconciliation.json').write_text(json.dumps(checks, indent=2)+'\n')
print(json.dumps(checks, indent=2))
print(segment.head(8).to_string(index=False))
