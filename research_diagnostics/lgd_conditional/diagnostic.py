"""Non-deployable conditional-mean diagnostic; never imported by the risk engine."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from lgd_research.generate_r2 import DEPLOYABLE

ROOT = Path(__file__).resolve().parents[2]
BUCKETS = np.array([1, 6, 12, 24, 36, 60])


def outcomes(frame, rng):
    """Independent transcription of ordinary R2 future outcomes, fixed known X.

    Input allow-list prevents using actual cure, shocks, recoveries or target.
    Draw order is retained for independent exact replay of the original generator.
    """
    x = frame[DEPLOYABLE]
    n = len(x)
    ead = x.ead_at_default.to_numpy()
    collateral = x.collateral_type.to_numpy()
    lien = x.lien_rank.to_numpy()
    coverage = x.collateral_coverage.to_numpy()
    guarantee = x.guarantee_coverage.to_numpy()
    leverage = x.leverage_at_default.to_numpy()
    liquidity = x.current_ratio_at_default.to_numpy()
    management = x.management_quality.to_numpy()
    downturn = x.downturn_at_default.to_numpy()
    quality = x.security_quality.to_numpy()
    strength = x.guarantor_strength.to_numpy()
    market = rng.normal(0, .16, n)
    bank = rng.normal(0, .16, n)
    collection = rng.normal(0, .10, n)
    cure_probability = 1 / (1 + np.exp(-(-1.5 + .6*(liquidity-1)
        - .22*(leverage-2.5) + .20*(management-3) - .55*downturn)))
    cure = rng.binomial(1, cure_probability)
    liquidation = np.select([collateral == 'Cash', collateral == 'Mortgage',
        collateral == 'Other'], [.97, .68, .44], default=0.)
    secured = np.minimum(ead, ead*coverage*liquidation*
        np.where(lien == 'Second', .72, 1.)*(.55+.6*quality)*
        np.clip(1+market-.20*downturn, .15, 1.5))
    guaranteed = np.minimum(np.maximum(ead-secured, 0), ead*guarantee*
        (.25+.65*strength)*np.clip(1+bank-.2*downturn, 0, 1.3))
    residual = np.maximum(ead-secured-guaranteed, 0)
    unsecured = residual*np.clip(.30-.027*(leverage-2.8)+.045*(liquidity-1)
        +.02*(management-3)-.10*downturn+collection, 0, .75)
    cured = np.where(cure == 1, np.maximum(ead*(.90+.04*rng.normal(size=n))
        -secured-guaranteed-unsecured, 0), 0)
    cured = np.minimum(cured, np.maximum(ead-secured-guaranteed-unsecured, 0))
    gross = secured+guaranteed+unsecured+cured
    months = np.clip(np.rint(8+17*(collateral == 'Mortgage')+8*(lien == 'Second')
        +9*(1-cure)+13*downturn+rng.gamma(2, 5, n)), 1, 60)
    months = np.where(collateral == 'Cash', rng.integers(1, 5, n)+4*downturn, months)
    costs = ead*np.clip(.012+.014*(collateral == 'Mortgage')+.012*(lien == 'Second')
        +.025*downturn+rng.normal(0, .009, n), .003, .16)
    weights = np.exp(-np.abs(BUCKETS[None, :]-months[:, None])/9)
    weights /= weights.sum(axis=1, keepdims=True)
    net = gross[:, None]*weights
    net[:, 0] -= costs*(collateral == 'Cash')
    net[:, 2] -= costs*(collateral != 'Cash')
    rate = np.clip(rng.normal(.07, .012, n), .035, .12)
    pv = np.sum(net/(1+rate[:, None])**(BUCKETS[None, :]/12), axis=1)
    return np.clip(1-pv/ead, 0, 1)


def conditional_mean(frame, draws=4096, seed=2026092401):
    if draws < 2:
        raise ValueError('At least two draws required')
    rng = np.random.default_rng(seed)
    # Bounded memory and independent shocks for every case and draw.
    x = frame[DEPLOYABLE].reset_index(drop=True)
    means, errors = [], []
    for start in range(0, len(x), 50):
        batch = x.iloc[start:start+50]
        repeated = batch.loc[batch.index.repeat(draws)]
        values = outcomes(repeated, rng).reshape(len(batch), draws)
        means.extend(values.mean(axis=1))
        errors.extend(values.std(axis=1, ddof=1)/np.sqrt(draws))
    return np.array(means), np.array(errors)


def main():
    path = ROOT/'lgd_research/data/r2_final_holdout.csv'
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != '093a0686316812d0cbf267c42b2a6551d6de6ba21a86529f0ba61f3e1fc2fc59':
        raise ValueError('Frozen holdout hash mismatch')
    frame = pd.read_csv(path)
    prediction_path = ROOT/'lgd_research/results/final_predictions.csv'
    predictions = pd.read_csv(prediction_path)
    frame = frame.merge(predictions[['facility_id', 'A V5 H', 'two-stage enhanced R2']],
                        on='facility_id', validate='one_to_one')
    if len(frame) != 3000:
        raise ValueError('Incomplete frozen prediction join')
    expected, se = conditional_mean(frame)
    actual = frame.economic_lgd.to_numpy()
    rows = []
    for name, prediction in [('V5', frame['A V5 H'].to_numpy()),
                            ('two_stage', frame['two-stage enhanced R2'].to_numpy()),
                            ('simulator_conditional_mean', expected)]:
        cohorts = [('all', np.ones(len(frame), dtype=bool)),
                   *[(f'realized_gt{int(q*100)}', actual > q) for q in (.6, .75, .9)],
                   ('realized_le10', actual <= .1)]
        for lo, hi in zip([0, .2, .4, .6, .8], [.2, .4, .6, .8, 1.]):
            cohorts.append((f'predicted_{lo:.1f}_{hi:.1f}',
                            (prediction >= lo) & ((prediction < hi) if hi < 1 else (prediction <= hi))))
        for cohort, mask in cohorts:
            n = int(mask.sum())
            if not n:
                rows.append(dict(model=name, cohort=cohort, n=0))
                continue
            err = prediction[mask]-actual[mask]
            model_error = float((prediction[mask]-expected[mask]).mean())
            outcome_error = float((expected[mask]-actual[mask]).mean())
            assert np.isclose(err.mean(), model_error+outcome_error, atol=1e-12)
            rows.append(dict(model=name, cohort=cohort, n=n,
                mae=float(np.abs(err).mean()), rmse=float(np.sqrt((err**2).mean())),
                bias=float(err.mean()), mean_actual=float(actual[mask].mean()),
                mean_predicted=float(prediction[mask].mean()),
                model_minus_conditional_mean=model_error,
                conditional_mean_minus_realization=outcome_error,
                conditional_mean_mc_se=float(np.sqrt((se[mask]**2).sum())/n)))
    dest = ROOT/'research_diagnostics/lgd_conditional/results'
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest/'scorecard.csv', index=False)
    pd.DataFrame(dict(facility_id=frame.facility_id, conditional_mean=expected,
                      monte_carlo_se=se)).to_csv(dest/'conditional_means.csv', index=False)
    evidence = dict(holdout_sha256=sha, seed=2026092401, draws_per_case=4096,
        n=len(frame), max_case_mc_se=float(se.max()),
        prediction_sha256=hashlib.sha256(prediction_path.read_bytes()).hexdigest(),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        generator_sha256=hashlib.sha256((ROOT/'lgd_research/generate_r2.py').read_bytes()).hexdigest(),
        status='RETROSPECTIVE SIMULATOR DIAGNOSTIC; NOT DEPLOYABLE; NO PROMOTION')
    (dest/'manifest.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(pd.DataFrame(rows).query("cohort in ['all', 'realized_gt75']").to_string(index=False))


if __name__ == '__main__':
    main()
