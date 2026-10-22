"""Traditional Weight of Evidence (WOE) credit-scorecard experiment.

The experiment is isolated from the governed model. Bins and WOE values are fitted
on training data only, then applied unchanged to the untouched holdout.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from data_preparation import (
    load_data, prepare_data, pd_feature_columns, PD_BASE_FEATURES
)
from pd_model import logistic_model
from validation import validation_summary

SEED = 42
N_BINS = 5
SMOOTHING = 0.5

def _fit_buckets(train_s):
    s = train_s.copy()
    non_null = s.dropna()
    if pd.api.types.is_numeric_dtype(s) and non_null.nunique() > 10:
        _, edges = pd.qcut(non_null, q=min(N_BINS, non_null.nunique()),
                           retbins=True, duplicates="drop")
        edges = np.unique(edges.astype(float))
        edges[0], edges[-1] = -np.inf, np.inf
        return {"kind": "numeric", "edges": edges}
    cats = sorted(non_null.astype(str).unique().tolist())
    return {"kind": "categorical", "categories": cats}

def _bucketize(s, spec):
    if spec["kind"] == "numeric":
        b = pd.cut(pd.to_numeric(s, errors="coerce"),
                   bins=spec["edges"], include_lowest=True)
        return b.astype(str).where(s.notna(), "__MISSING__")
    return s.astype(str).where(s.notna(), "__MISSING__")

def _fit_woe(train_df, y, variables):
    specs, maps, table_rows = {}, {}, []
    total_good = int((y == 0).sum())
    total_bad = int((y == 1).sum())
    for var in variables:
        spec = _fit_buckets(train_df[var])
        specs[var] = spec
        bucket = _bucketize(train_df[var], spec)
        tmp = pd.DataFrame({"bucket": bucket, "bad": np.asarray(y, dtype=int)})
        grouped = tmp.groupby("bucket", dropna=False)["bad"].agg(["count", "sum"]).reset_index()
        grouped["good"] = grouped["count"] - grouped["sum"]
        k = len(grouped)
        grouped["dist_good"] = (grouped["good"] + SMOOTHING) / (total_good + SMOOTHING * k)
        grouped["dist_bad"] = (grouped["sum"] + SMOOTHING) / (total_bad + SMOOTHING * k)
        grouped["woe"] = np.log(grouped["dist_good"] / grouped["dist_bad"])
        grouped["iv_component"] = (grouped["dist_good"] - grouped["dist_bad"]) * grouped["woe"]
        grouped["event_rate"] = grouped["sum"] / grouped["count"].clip(lower=1)
        maps[var] = dict(zip(grouped["bucket"].astype(str), grouped["woe"]))
        for _, r in grouped.iterrows():
            table_rows.append({
                "variable": var,
                "bucket": str(r["bucket"]),
                "count": int(r["count"]),
                "goods": int(r["good"]),
                "defaults": int(r["sum"]),
                "event_rate": float(r["event_rate"]),
                "dist_good": float(r["dist_good"]),
                "dist_bad": float(r["dist_bad"]),
                "woe": float(r["woe"]),
                "iv_component": float(r["iv_component"]),
            })
    return specs, maps, pd.DataFrame(table_rows)

def _transform_woe(frame, variables, specs, maps):
    out = pd.DataFrame(index=frame.index)
    for var in variables:
        bucket = _bucketize(frame[var], specs[var]).astype(str)
        out[var] = bucket.map(maps[var]).fillna(0.0).astype(float)
    return out

df = load_data(ROOT / "data/raw/sme_credit_portfolio.csv")
idx = np.arange(len(df))
train_idx, test_idx = train_test_split(
    idx, test_size=0.25, stratify=df["default"], random_state=SEED
)
train_raw = df.iloc[train_idx].copy()
test_raw = df.iloc[test_idx].copy()
ytr = train_raw["default"].astype(int)
yte = test_raw["default"].astype(int)

# Traditional WOE scorecard uses economically governed borrower variables plus
# industry as a categorical characteristic. No holdout-driven bin tuning is used.
variables = list(PD_BASE_FEATURES) + ["industry"]
specs, woe_maps, bin_table = _fit_woe(train_raw, ytr, variables)
Xtr_woe = _transform_woe(train_raw, variables, specs, woe_maps)
Xte_woe = _transform_woe(test_raw, variables, specs, woe_maps)

woe_lr = LogisticRegression(max_iter=2000)
woe_lr.fit(Xtr_woe, ytr)
woe_pd = woe_lr.predict_proba(Xte_woe)[:, 1]
woe_metrics = validation_summary(yte, woe_pd)

# Same holdout comparator: current governed LR.
model_df = prepare_data(df)
X_all = model_df[pd_feature_columns(model_df)]
baseline = logistic_model()
baseline.fit(X_all.iloc[train_idx], ytr)
baseline_pd = baseline.predict_proba(X_all.iloc[test_idx])[:, 1]
baseline_metrics = validation_summary(yte, baseline_pd)

comparison = pd.DataFrame([
    {"model": "Governed Logistic Regression", **baseline_metrics},
    {"model": "WOE Logistic Scorecard", **woe_metrics},
])

# Convert the WOE model into conventional scorecard points.
# Convention: 600 points at 50:1 good:bad odds; +20 points doubles good:bad odds.
BASE_SCORE = 600
BASE_ODDS = 50
PDO = 20
factor = PDO / np.log(2)
offset = BASE_SCORE - factor * np.log(BASE_ODDS)
intercept = float(woe_lr.intercept_[0])
base_points = offset - factor * intercept

coef = dict(zip(variables, woe_lr.coef_[0]))
points = bin_table.copy()
points["coefficient"] = points["variable"].map(coef)
points["bin_points"] = -factor * points["coefficient"] * points["woe"]
points["base_points_once_per_score"] = base_points
points["information_value_total"] = points.groupby("variable")["iv_component"].transform("sum")

logit = woe_lr.decision_function(Xte_woe)
scores = offset - factor * logit
holdout_scores = pd.DataFrame({
    "customer_id": test_raw["customer_id"].values,
    "default": yte.values,
    "predicted_pd": woe_pd,
    "score": scores,
})

out_dir = ROOT / "outputs" / "experiments" / "woe_credit_scorecard"
out_dir.mkdir(parents=True, exist_ok=True)
comparison.to_csv(out_dir / "woe_vs_governed_validation.csv", index=False)
points.to_csv(out_dir / "woe_scorecard_points.csv", index=False)
holdout_scores.to_csv(out_dir / "woe_holdout_scores.csv", index=False)

iv = points[["variable", "information_value_total"]].drop_duplicates().sort_values(
    "information_value_total", ascending=False
)

print("\nWOE CREDIT SCORECARD EXPERIMENT")
print("WOE definition: ln(distribution of non-defaults / distribution of defaults).")
print("Positive WOE therefore indicates a relatively safer bin under this convention.")
print("\nVALIDATION COMPARISON\n", comparison.round(4).to_string(index=False))
print("\nINFORMATION VALUE BY CHARACTERISTIC\n", iv.round(4).to_string(index=False))
print(f"\nScore scaling: {BASE_SCORE} points at {BASE_ODDS}:1 good:bad odds; PDO={PDO}.")
print("All bin edges and WOE values were learned on training data only.")
print("This experiment does not alter the governed PD model or downstream risk engine.")
