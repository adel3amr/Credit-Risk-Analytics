"""Bootstrap confidence intervals for the governed Logistic Regression.

This experiment is isolated from the governed pipeline. It fits the existing primary
PD model once on the original training split, then bootstraps the untouched holdout
pairs to quantify uncertainty around out-of-sample validation metrics.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from data_preparation import load_data, prepare_data, pd_feature_columns
from pd_model import logistic_model
from validation import validation_summary

N_BOOTSTRAPS = 2000
SEED = 20260922
ALPHA = 0.05

df = load_data(ROOT / "data/raw/sme_credit_portfolio.csv")
model_df = prepare_data(df)
X = model_df[pd_feature_columns(model_df)]
y = model_df["default"]

Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

model = logistic_model()
model.fit(Xtr, ytr)
pred = model.predict_proba(Xte)[:, 1]
point = validation_summary(yte, pred)

rng = np.random.default_rng(SEED)
rows = []
y_arr = np.asarray(yte)
p_arr = np.asarray(pred)
n = len(y_arr)

for _ in range(N_BOOTSTRAPS):
    idx = rng.integers(0, n, size=n)
    y_b = y_arr[idx]
    p_b = p_arr[idx]
    if np.unique(y_b).size < 2:
        continue
    rows.append(validation_summary(y_b, p_b))

boot = pd.DataFrame(rows)
metrics = [
    "ROC_AUC", "Gini", "KS", "Brier", "LogLoss",
    "Mean_PD", "Observed_DR", "Calibration_in_the_large",
]
summary_rows = []
for metric in metrics:
    vals = boot[metric].dropna()
    summary_rows.append({
        "metric": metric,
        "point_estimate": point[metric],
        "bootstrap_mean": vals.mean(),
        "bootstrap_std": vals.std(ddof=1),
        "ci_2_5pct": vals.quantile(ALPHA / 2),
        "ci_97_5pct": vals.quantile(1 - ALPHA / 2),
        "successful_bootstraps": len(vals),
    })

out_dir = ROOT / "outputs" / "experiments" / "bootstrap_confidence_intervals"
out_dir.mkdir(parents=True, exist_ok=True)
summary = pd.DataFrame(summary_rows)
summary.to_csv(out_dir / "bootstrap_confidence_intervals.csv", index=False)
boot.to_csv(out_dir / "bootstrap_metric_distribution.csv", index=False)

print("\nBOOTSTRAP STABILITY / CONFIDENCE INTERVALS")
print(f"Holdout borrowers: {len(yte):,}")
print(f"Holdout defaults: {int(yte.sum()):,}")
print(f"Requested bootstrap samples: {N_BOOTSTRAPS:,}")
print(f"Successful samples: {len(boot):,}")
print("\n", summary.round(6).to_string(index=False))
print("\nInterpretation: intervals quantify sampling uncertainty on the fixed untouched holdout.")
print("They are not used to retune the model, thresholds, DGP, or primary-model choice.")
