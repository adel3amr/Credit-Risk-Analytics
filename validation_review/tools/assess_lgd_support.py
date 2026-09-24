"""Independent synthetic-vintage experiment for LGD input support.

The original holdout stays untouched. The second validation vintage uses a
different random seed and is never passed to fit. No holdout-selected tuning.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lgd_model import gradient_boosting_lgd_model, predict_lgd  # noqa: E402

ORIGINAL = ROOT / "data/raw/lgd_workout_history.csv"
DEVELOPMENT = ROOT / "data/raw/lgd_live_profile_development.csv"
VALIDATION = ROOT / "data/raw/lgd_live_profile_validation.csv"
OUTPUT = ROOT / "outputs/lgd_independent_vintage_assessment.csv"


def summaries(model, sample, name, vintage):
    y = sample.economic_lgd.to_numpy()
    pred = predict_lgd(model, sample)
    w = sample.ead_at_default.to_numpy()
    rows = []
    for cohort, mask in [
        ("all", np.ones(len(sample), dtype=bool)),
        ("loan_or_ovd_zero_guarantee", sample.product_type.isin(["Term Loan", "OVD"]).to_numpy() & (sample.guarantee_coverage.to_numpy() == 0)),
        ("unsecured", sample.collateral_type.eq("Unsecured").to_numpy()),
        ("realized_above_75pct", y > .75),
        ("realized_above_90pct", y > .90),
        ("predicted_top_10pct", pred >= np.quantile(pred, .90)),
    ]:
        if not mask.any():
            continue
        delta = pred[mask] - y[mask]
        rows.append(dict(model=name, vintage=vintage, cohort=cohort,
                         facilities=int(mask.sum()), actual_mean=float(y[mask].mean()),
                         forecast_mean=float(pred[mask].mean()),
                         bias=float(delta.mean()), mae=float(abs(delta).mean()),
                         rmse=float(np.sqrt(np.mean(delta**2))),
                         ead_weighted_bias=float(np.average(delta, weights=w[mask])),
                         severe_capture=float(np.mean(pred[mask] > .75))))
    return rows


def main():
    historical = pd.read_csv(ORIGINAL)
    dev = pd.read_csv(DEVELOPMENT)
    future = pd.read_csv(VALIDATION)
    if dev.head(len(future)).drop(columns="facility_id").reset_index(drop=True).equals(
        future.drop(columns="facility_id").reset_index(drop=True)
    ):
        raise ValueError("Development and validation vintages unexpectedly identical")
    # Generator IDs restart for each seed; vintage IDs must therefore be scoped
    # by their source, and no row of the future vintage is used in fitting.
    original_train, original_holdout = train_test_split(historical, test_size=.25, random_state=42)
    train = pd.concat([original_train, dev], ignore_index=True)
    candidate = gradient_boosting_lgd_model().fit(train, train.economic_lgd)
    baseline = gradient_boosting_lgd_model().fit(original_train, original_train.economic_lgd)
    rows = []
    for name, model in [("original_training", baseline), ("support_corrected", candidate)]:
        rows.extend(summaries(model, original_holdout, name, "original_holdout"))
        rows.extend(summaries(model, future, name, "separate_live_profile_seed"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT, index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print(json.dumps(dict(original_holdout=len(original_holdout),
                          corrected_development=len(dev), independent_validation=len(future),
                          heldout_rows_used_in_fit=0), indent=2))


if __name__ == "__main__":
    main()
