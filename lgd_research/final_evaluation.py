"""Single protected R2 holdout evaluation after FINAL_EVALUATION_LOCK.md.

Results are immutable within this round; re-execution verifies hashes and
reproduces the same values, without hyperparameter search or candidate selection.
"""
from pathlib import Path
import hashlib
import json
import joblib
import numpy as np
import pandas as pd

from lgd_research.run_study import HERE, NUMERIC_FEATURES, CATEGORICAL_FEATURES, NEW_NUM, ORACLE_NUM, TwoStage, Component, model, predict, score

OUT = HERE / "results"
HOLDOUT = HERE / "data/r2_final_holdout.csv"
EXPECTED = "093a0686316812d0cbf267c42b2a6551d6de6ba21a86529f0ba61f3e1fc2fc59"


def paired_bootstrap(frame, models, a, b, cohort, nrep=1000):
    rng = np.random.default_rng(872201)
    y = frame.economic_lgd.to_numpy()
    ead = frame.ead_at_default.to_numpy()
    pa,pb = models[a],models[b]
    # Forecast-selected cohort is chosen by incumbent's prediction once.
    mask = (y > .75 if cohort == "realized_gt75" else
            pa >= np.quantile(pa, .9) if cohort == "V5_predicted_top10" else
            np.ones(len(y), dtype=bool))
    idx = np.flatnonzero(mask)
    res = []
    for metric in ["mae", "rmse", "bias", "ead_weighted_bias"]:
        diffs = []
        for _ in range(nrep):
            j = rng.choice(idx, len(idx), replace=True)
            ea,eb = pa[j]-y[j], pb[j]-y[j]
            def value(e):
                if metric == "mae": return np.mean(abs(e))
                if metric == "rmse": return np.sqrt(np.mean(e*e))
                if metric == "ead_weighted_bias": return np.average(e, weights=ead[j])
                return np.mean(e)
            diffs.append(value(eb)-value(ea))
        res.append(dict(comparison=f"{b} minus {a}", cohort=cohort, metric=metric,
                        n=int(mask.sum()), lower_95=float(np.quantile(diffs,.025)),
                        upper_95=float(np.quantile(diffs,.975)),
                        bootstrap_mean=float(np.mean(diffs))))
    return res


def main():
    assert (HERE / "FINAL_EVALUATION_LOCK.md").exists()
    assert hashlib.sha256(HOLDOUT.read_bytes()).hexdigest() == EXPECTED, "Final holdout changed"
    validation = pd.read_csv(HERE / "data/r2_selection.csv")
    dev = pd.read_csv(HERE / "data/r2_development.csv")
    hold = pd.read_csv(HOLDOUT)
    assert set(hold.facility_id).isdisjoint(validation.facility_id)
    assert set(hold.facility_id).isdisjoint(dev.facility_id)
    existing = OUT / "final_holdout_evaluated.json"
    if existing.exists():
        prior = json.loads(existing.read_text())
        assert prior["holdout_sha256"] == EXPECTED and prior["selection_lock"] == "FINAL_EVALUATION_LOCK.md"
    files = {
        "A V5 H": "a_v5_h.joblib",
        "V5 R2 full": "v5_r2_full.joblib",
        "GB enhanced R2": "gb_enhanced_r2.joblib",
    }
    forecasts = {name: predict(joblib.load(OUT/path),hold) for name,path in files.items()}
    # Custom research objects are reconstructed deterministically from the
    # frozen development sample, avoiding __main__ pickle import ambiguity.
    forecasts["two-stage enhanced R2"] = predict(
        TwoStage(NUMERIC_FEATURES+NEW_NUM,CATEGORICAL_FEATURES).fit(dev),hold)
    forecasts["component R2"] = predict(Component().fit(dev),hold)
    # These two special models are trained from development only, after finalist
    # lock. Future-information fields appear exclusively in the oracle.
    oracle = model(NUMERIC_FEATURES+NEW_NUM+ORACLE_NUM,CATEGORICAL_FEATURES)
    oracle.fit(dev,dev.economic_lgd)
    forecasts["oracle FUTURE INFORMATION"] = predict(oracle,hold)
    quantile = model(NUMERIC_FEATURES+NEW_NUM,CATEGORICAL_FEATURES,kind="quantile")
    quantile.fit(dev,dev.economic_lgd)
    forecasts["quantile p90 RISK ONLY"] = predict(quantile,hold)
    rows = []
    for name,p in forecasts.items():
        rows.extend(score(hold.economic_lgd,p,hold.ead_at_default,name,"R2 final holdout"))
    pd.DataFrame(rows).to_csv(OUT/"final_scorecard.csv",index=False)
    pred = hold[["facility_id","economic_lgd","ead_at_default","collateral_type",
                 "product_type","guarantee_coverage","cure_flag"]].copy()
    for name,p in forecasts.items(): pred[name]=p
    pred.to_csv(OUT/"final_predictions.csv",index=False)
    ci=[]
    for challenger in ["V5 R2 full","GB enhanced R2","two-stage enhanced R2","component R2"]:
        for cohort in ["all","realized_gt75","V5_predicted_top10"]:
            ci.extend(paired_bootstrap(hold,forecasts,"A V5 H",challenger,cohort))
    pd.DataFrame(ci).to_csv(OUT/"paired_bootstrap.csv",index=False)
    marker = dict(holdout_sha256=EXPECTED, selection_lock="FINAL_EVALUATION_LOCK.md",
                  models=list(forecasts), facilities=len(hold),
                  methodology_approved=False, bank_production_permitted=False)
    if existing.exists():
        assert json.loads(existing.read_text()) == marker, "Final-evaluation metadata changed"
    existing.write_text(json.dumps(marker,indent=2)+"\n")
    print(pd.DataFrame(rows).query("cohort in ['all','realized_gt75','predicted_top10']")
          [["model","cohort","n","mae","rmse","bias","ead_weighted_bias"]].to_string(index=False))


if __name__ == "__main__": main()
