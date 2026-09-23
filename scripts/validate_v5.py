"""Release diagnostics and independent accounting checks; no model tuning."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.lgd_model import NUMERIC_FEATURES, CATEGORICAL_FEATURES, lgd_validation_summary
from src.validation import validation_summary

OUT = ROOT / 'outputs'


def main():
    checks = []

    def check(name, condition, detail=''):
        checks.append({'check': name, 'passed': bool(condition), 'detail': str(detail)})

    hist = pd.read_csv(ROOT / 'data/raw/lgd_workout_history.csv')
    hold = pd.read_csv(OUT / 'lgd_holdout_predictions.csv')
    b = pd.read_csv(OUT / 'borrower_audit_trace.csv')
    f = pd.read_csv(OUT / 'facility_ecl_predictions.csv')
    train_idx, test_idx = train_test_split(hist.index, test_size=.25, random_state=42)
    train_ids = set(hist.loc[train_idx, 'facility_id'])
    check('LGD split disjoint and reproducible', not train_ids.intersection(hold.facility_id)
          and set(hold.facility_id) == set(hist.loc[test_idx, 'facility_id']))
    for name, frame, key in [('history', hist, 'facility_id'), ('holdout', hold, 'facility_id'),
                             ('borrowers', b, 'customer_id'), ('facilities', f, 'facility_id')]:
        check(f'{name}: unique non-null IDs', frame[key].notna().all() and frame[key].is_unique)
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    outcomes = {'economic_lgd', 'cure_flag', 'write_off_flag', 'months_to_resolution',
                'workout_cost', 'pv_net_recovery', 'discount_rate'} | {c for c in hist if c.startswith('recovery_cf_')}
    check('LGD outcomes excluded from predictors', not set(features).intersection(outcomes))
    check('LGD training feature completeness', hist[features].notna().all().all())
    check('LGD numeric features finite', np.isfinite(hist[NUMERIC_FEATURES]).all().all())
    check('Positive historical EAD and bounded target', (hist.ead_at_default > 0).all()
          and hist.economic_lgd.between(0, 1).all())
    pv = sum(hist[f'recovery_cf_{month}m'] / (1 + hist.discount_rate) ** (month / 12)
             for month in [1, 6, 12, 24, 36, 60])
    reconstructed = np.clip(1 - pv / hist.ead_at_default, 0, 1)
    target_error = np.abs(reconstructed - hist.economic_lgd)
    # Stored cash flows/EAD/rates are rounded. This tolerance is 0.005 pp LGD,
    # far smaller than reported model errors; it is not a performance threshold.
    check('Discounted net recovery reproduces LGD', target_error.max() < 5e-5, target_error.max())
    coverage_error = np.abs(hist.collateral_value_at_default / hist.ead_at_default - hist.collateral_coverage)
    check('Historical collateral coverage reconciles', coverage_error.max() < 6e-5, coverage_error.max())
    check('Net recovery cash flows reconcile to stored PV',
          (np.abs(pv - hist.pv_net_recovery) / hist.ead_at_default).max() < 5e-5)
    check('Predictions bounded and finite', np.isfinite(hold.predicted_lgd).all()
          and hold.predicted_lgd.between(0, 1).all())
    clipping_count = int((~hold.raw_predicted_lgd.between(0, 1)).sum())

    joined = hold[['facility_id', 'predicted_lgd']].merge(hist, on='facility_id', validate='one_to_one')
    # Reapply the frozen legacy generator formula to this resolved-workout sample.
    # This is a diagnostic transfer, not an original historical model forecast.
    # Its synthetic residual is drawn once with a fixed seed, without seeing LGD.
    legacy_rng = np.random.default_rng(20260923)
    severity = np.clip(.62 + .06 * hist.industry.eq('Hospitality')
                       + legacy_rng.normal(0, .07, len(hist)), .35, .85)
    haircut = hist.collateral_type.map({'Cash': 0., 'Mortgage': .20, 'Other': .35, 'Unsecured': 1.})
    recognized = np.minimum(hist.collateral_value_at_default * (1 - haircut), hist.ead_at_default)
    legacy_prediction = np.clip(severity * (hist.ead_at_default - recognized) / hist.ead_at_default, 0, .85)
    joined['legacy_proxy_reapplied'] = joined.facility_id.map(dict(zip(hist.facility_id, legacy_prediction)))
    rows = []
    masks = {'all': np.ones(len(joined), dtype=bool),
             'realized <=10%': joined.economic_lgd <= .10,
             'realized >60%': joined.economic_lgd > .60,
             'realized >75%': joined.economic_lgd > .75,
             'realized >=90%': joined.economic_lgd >= .90,
             'realized >=97%': joined.economic_lgd >= .97,
             'cure': joined.cure_flag == 1, 'no cure': joined.cure_flag == 0}
    for dim in ['collateral_type', 'product_type', 'lien_rank']:
        for value in sorted(joined[dim].unique()):
            masks[f'{dim}: {value}'] = joined[dim].eq(value)
    for label, mask in masks.items():
        g = joined.loc[mask]
        if len(g):
            rows.append({'segment': label, 'facilities': len(g),
                         **lgd_validation_summary(g.economic_lgd, g.predicted_lgd, g.ead_at_default)})
    segments = pd.DataFrame(rows)
    segments.to_csv(OUT / 'v5_lgd_realized_segments.csv', index=False)
    comparison = []
    calibration_rows = []
    for model_name, column in [('Facility Gradient Boosting', 'predicted_lgd'),
                               ('Legacy proxy reapplied (fixed seed)', 'legacy_proxy_reapplied')]:
        for label, mask in masks.items():
            g = joined.loc[mask]
            if len(g):
                comparison.append({'Model': model_name, 'segment': label, 'facilities': len(g),
                    **lgd_validation_summary(g.economic_lgd, g[column], g.ead_at_default)})
        # Fixed LGD prediction bands allow both models to expose calibration.
        predicted_band = pd.cut(joined[column], [-.001, .1, .3, .6, .75, .9, 1])
        for band, g in joined.groupby(predicted_band, observed=True):
            calibration_rows.append({'Model': model_name, 'predicted_band': str(band),
                'facilities': len(g), 'predicted_mean': g[column].mean(), 'realized_mean': g.economic_lgd.mean()})
    pd.DataFrame(comparison).to_csv(OUT / 'v5_lgd_legacy_holdout_comparison.csv', index=False)
    pd.DataFrame(calibration_rows).to_csv(OUT / 'v5_lgd_legacy_calibration.csv', index=False)
    bands = pd.cut(joined.economic_lgd, [-.001, .1, .3, .6, .75, .9, 1], include_lowest=True)
    band_rows = []
    for band, g in joined.groupby(bands, observed=True):
        band_rows.append({'actual_lgd_band': str(band), 'facilities': len(g),
                          **lgd_validation_summary(g.economic_lgd, g.predicted_lgd, g.ead_at_default)})
    pd.DataFrame(band_rows).to_csv(OUT / 'v5_lgd_bands.csv', index=False)
    residual = joined.predicted_lgd - joined.economic_lgd
    residual.describe(percentiles=[.01, .05, .1, .5, .9, .95, .99]).to_csv(OUT / 'v5_lgd_residual_distribution.csv')
    support = []
    for name, idx in [('train', train_idx), ('holdout', test_idx)]:
        g = hist.loc[idx]
        support.append({'sample': name, 'facilities': len(g), 'lgd_above_60': int((g.economic_lgd > .6).sum()),
                        'lgd_above_75': int((g.economic_lgd > .75).sum()),
                        'lgd_at_least_90': int((g.economic_lgd >= .9).sum()),
                        'lgd_at_least_97': int((g.economic_lgd >= .97).sum()),
                        'cures': int(g.cure_flag.sum()), 'mean_lgd': g.economic_lgd.mean()})
    pd.DataFrame(support).to_csv(OUT / 'v5_lgd_sample_support.csv', index=False)

    # Current-portfolio legacy comparisons have no realized workout outcome.
    # Preserve the same-population bridge without fabricating MAE/RMSE for it.
    legacy = b[['customer_id', 'lgd_legacy_proxy', 'modelled_lgd', 'ead', 'stage']].copy()
    legacy['difference'] = legacy.modelled_lgd - legacy.lgd_legacy_proxy
    legacy.to_csv(OUT / 'v5_legacy_facility_comparison.csv', index=False)

    check('Facility borrower links complete', f.customer_id.isin(b.customer_id).all())
    source = b.set_index('customer_id').reindex(f.customer_id)
    check('Borrower drivers reach facilities unchanged', all(np.allclose(f[target], source[origin])
          for target, origin in [('collateral_coverage', 'collateral_coverage'),
                                 ('leverage_at_default', 'leverage_ratio'),
                                 ('current_ratio_at_default', 'current_ratio'),
                                 ('management_quality', 'management_quality')]))
    expected_guarantee = f.product_type.map({'Import LC': .20, 'Performance Guarantee': .35,
                                            'Financial Guarantee': .55}).fillna(0.)
    check('Existing facility guarantee mapping preserved', np.allclose(f.guarantee_coverage, expected_guarantee))
    expected_lien = np.where(f.collateral_type.eq('Unsecured'), 'Unsecured',
                            np.where(f.product_type.eq('Term Loan') | f.collateral_type.eq('Cash'), 'First', 'Second'))
    check('Existing facility seniority mapping preserved', (f.lien_rank == expected_lien).all())
    check('Trade EAD reconciles to frozen CCF', np.allclose(b.trade_ead, b.trade * b.trade_ccf, atol=.02, rtol=0))
    check('Facility numeric outputs finite', np.isfinite(f[['ead_at_default', 'predicted_lgd',
          'facility_pd_12m', 'facility_lifetime_pd', 'facility_ecl']]).all().all())
    check('Borrower product EAD reconciles', np.allclose(b.ead, b.loan_ead + b.ovd_ead + b.trade_ead, atol=.02, rtol=0))
    agg = f.groupby('customer_id')[['ead_at_default', 'facility_ecl', 'facility_ecl_12m']].sum()
    z = b.set_index('customer_id').join(agg)
    check('Facility EAD reconciles to borrower', np.allclose(z.ead, z.ead_at_default, atol=.02, rtol=0))
    check('Facility ECL reconciles to borrower', np.allclose(z.ecl, z.facility_ecl, atol=.02, rtol=0))
    check('Facility 12M ECL reconciles to borrower', np.allclose(z.ecl_12m, z.facility_ecl_12m, atol=.02, rtol=0))
    effective_pd = np.select([f.stage.eq('Stage 3'), f.stage.eq('Stage 2')],
                             [1., f.facility_lifetime_pd], default=f.facility_pd_12m)
    expected = effective_pd * f.predicted_lgd * f.ead_at_default
    check('Facility stage-specific ECL identities', np.allclose(f.facility_ecl, expected, atol=.02, rtol=0))
    check('Facility lifetime PD identity', np.allclose(f.facility_lifetime_pd,
          1 - (1 - f.facility_pd_12m) ** (f.remaining_months / 12), atol=1e-12))
    check('ECL within exposure', ((f.facility_ecl >= 0) & (f.facility_ecl <= f.ead_at_default)).all())
    s3 = b.current_credit_impaired.eq(1) | b.days_past_due.ge(90)
    s2 = (~s3) & (b.days_past_due.ge(30) | b.delinquencies_12m.ge(2)
          | (b.credit_utilization.ge(.85) & b.days_past_due.gt(0))
          | (b.previous_defaults.ge(1) & b.predicted_pd.ge(.05))
          | (b.ews_sicr_flag.eq(1) & b.consecutive_ews_months.ge(9)))
    expected_stage = np.select([s3, s2], ['Stage 3', 'Stage 2'], default='Stage 1')
    check('Staging and fixed 9-month policy reconcile', (b.stage == expected_stage).all())
    check('Stage 2 defaults to Rating 7', b.loc[s2, 'risk_rating'].eq(7).all())
    check('Rating 1 restricted to full-cash Stage 1',
          ((b.loc[b.risk_rating.eq(1), 'stage'] == 'Stage 1')
           & b.loc[b.risk_rating.eq(1), 'collateral_type'].eq('Cash')
           & b.loc[b.risk_rating.eq(1), 'recognized_collateral_coverage'].ge(.999)).all())
    pd_metrics = validation_summary(b.default, b.predicted_pd)
    saved = pd.read_csv(OUT / 'model_validation.csv').set_index('Model').loc['Logistic Regression']
    check('PD metrics independently recomputed', all(np.isclose(saved[k], v) for k, v in pd_metrics.items()))
    trace = f.copy()
    trace['effective_pd_for_ecl'] = effective_pd
    trace['recomputed_ecl'] = expected
    trace['difference'] = trace.facility_ecl - expected
    trace.groupby('stage', sort=True).head(3).to_csv(OUT / 'v5_facility_trace_examples.csv', index=False)
    pd.DataFrame(checks).to_csv(OUT / 'v5_release_checks.csv', index=False)
    manifest = {'python': platform.python_version(),
                'dependencies': {p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'joblib', 'matplotlib', 'streamlit']},
                'data_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sorted((ROOT / 'data/raw').glob('*.csv'))},
                'lgd_holdout_clipped_predictions': clipping_count,
                'legacy_diagnostic_noise_seed': 20260923,
                'max_lgd_target_reconstruction_error': float(target_error.max()),
                'pd_metrics': pd_metrics, 'total_ead': float(b.ead.sum()), 'total_ecl': float(b.ecl.sum())}
    (OUT / 'v5_run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    failed = [c['check'] for c in checks if not c['passed']]
    print(f'V5 release checks: {len(checks)-len(failed)}/{len(checks)} passed')
    print(segments.head(8).to_string(index=False))
    if failed:
        raise AssertionError(f'Failed release checks: {failed}')


if __name__ == '__main__':
    main()
