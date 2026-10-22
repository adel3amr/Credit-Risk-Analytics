"""Portfolio stress / sensitivity experiment for the governed credit-risk engine.

This branch is intentionally isolated from main. It applies transparent borrower-level
shocks to the untouched holdout and traces their effects through PD, rating, stage,
LGD and ECL without retraining or retuning the governed model.
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
from scorecard import add_score, add_risk_rating
from ecl import calculate_ecl

SEED = 42

df = load_data(ROOT / "data/raw/sme_credit_portfolio.csv")
model_df = prepare_data(df)
feature_cols = pd_feature_columns(model_df)
X = model_df[feature_cols]
y = model_df["default"]

train_idx, test_idx = train_test_split(
    np.arange(len(df)), test_size=0.25, stratify=y, random_state=SEED
)
model = logistic_model()
model.fit(X.iloc[train_idx], y.iloc[train_idx])
base_raw = df.iloc[test_idx].copy()

def _predict_pd(raw):
    prepared = prepare_data(raw)
    aligned = prepared.reindex(columns=feature_cols, fill_value=0)
    return model.predict_proba(aligned)[:, 1]

def _refresh_collateral(raw):
    out = raw.copy()
    ead = out["ead"].clip(lower=0)
    out["collateral_coverage"] = np.where(
        ead > 0, out["collateral_value"].clip(lower=0) / ead, 0.0
    )
    recognized = np.minimum(
        out["collateral_value"].clip(lower=0) * (1.0 - out["collateral_haircut"].clip(0, 1)),
        ead,
    )
    out["recognized_collateral"] = recognized
    out["recognized_collateral_coverage"] = np.where(ead > 0, recognized / ead, 0.0)
    out["unsecured_ead"] = np.maximum(ead - recognized, 0.0)
    out["lgd"] = np.clip(
        out["unsecured_lgd"].clip(0, 1) * out["unsecured_ead"] / np.maximum(ead, 1),
        0.0, 0.85,
    )
    return out

def _run_engine(raw, scenario):
    out = raw.copy()
    out["predicted_pd"] = _predict_pd(out)
    out = add_score(out)
    out = calculate_ecl(out)
    out = add_risk_rating(out)
    out["scenario"] = scenario
    return out

def _summary(out):
    total_ead = float(out["ead"].sum())
    total_ecl = float(out["ecl"].sum())
    return {
        "borrowers": len(out),
        "mean_pd": float(out["predicted_pd"].mean()),
        "mean_lgd": float(out["lgd"].mean()),
        "total_ead": total_ead,
        "total_ecl": total_ecl,
        "ecl_to_ead": total_ecl / max(total_ead, 1.0),
        "stage1": int((out["stage"] == "Stage 1").sum()),
        "stage2": int((out["stage"] == "Stage 2").sum()),
        "stage3": int((out["stage"] == "Stage 3").sum()),
        "rating_1_6": int(out["risk_rating"].between(1, 6).sum()),
        "rating_7": int((out["risk_rating"] == 7).sum()),
        "rating_8_10": int(out["risk_rating"].between(8, 10).sum()),
    }

scenarios = {}

scenarios["Baseline"] = base_raw.copy()

s = base_raw.copy()
s["leverage_ratio"] = s["leverage_ratio"] + 1.0
scenarios["Leverage +1.0x"] = s

s = base_raw.copy()
s["ebitda_margin"] = s["ebitda_margin"] - 0.05
scenarios["EBITDA margin -5pp"] = s

s = base_raw.copy()
s["current_ratio"] = (s["current_ratio"] * 0.80).clip(lower=0)
scenarios["Current ratio -20%"] = s

s = base_raw.copy()
s["credit_utilization"] = (s["credit_utilization"] + 0.10).clip(upper=1.50)
scenarios["Utilization +10pp"] = s

s = base_raw.copy()
s["delinquencies_12m"] = s["delinquencies_12m"] + 1
scenarios["One additional delinquency"] = s

s = base_raw.copy()
s["collateral_value"] = s["collateral_value"] * 0.80
s = _refresh_collateral(s)
scenarios["Collateral value -20%"] = s

s = base_raw.copy()
s["leverage_ratio"] = s["leverage_ratio"] + 1.0
s["ebitda_margin"] = s["ebitda_margin"] - 0.05
s["current_ratio"] = (s["current_ratio"] * 0.80).clip(lower=0)
s["credit_utilization"] = (s["credit_utilization"] + 0.10).clip(upper=1.50)
s["collateral_value"] = s["collateral_value"] * 0.80
s = _refresh_collateral(s)
scenarios["Combined borrower deterioration"] = s

engine_outputs = {name: _run_engine(raw, name) for name, raw in scenarios.items()}
summary = pd.DataFrame([
    {"scenario": name, **_summary(out)} for name, out in engine_outputs.items()
])

baseline = summary.loc[summary["scenario"] == "Baseline"].iloc[0]
for col in ["mean_pd", "mean_lgd", "total_ecl", "ecl_to_ead"]:
    summary[f"delta_{col}"] = summary[col] - baseline[col]

# Borrower-level sensitivity for the combined scenario.
b = engine_outputs["Baseline"].set_index("customer_id")
c = engine_outputs["Combined borrower deterioration"].set_index("customer_id")
impact = pd.DataFrame({
    "baseline_pd": b["predicted_pd"],
    "stressed_pd": c["predicted_pd"],
    "delta_pd": c["predicted_pd"] - b["predicted_pd"],
    "baseline_rating": b["risk_rating"],
    "stressed_rating": c["risk_rating"],
    "baseline_stage": b["stage"],
    "stressed_stage": c["stage"],
    "baseline_lgd": b["lgd"],
    "stressed_lgd": c["lgd"],
    "baseline_ecl": b["ecl"],
    "stressed_ecl": c["ecl"],
    "delta_ecl": c["ecl"] - b["ecl"],
}).reset_index()
impact = impact.sort_values("delta_ecl", ascending=False)

out_dir = ROOT / "outputs" / "experiments" / "stress_sensitivity"
out_dir.mkdir(parents=True, exist_ok=True)
summary.to_csv(out_dir / "stress_scenario_summary.csv", index=False)
impact.to_csv(out_dir / "combined_scenario_borrower_impact.csv", index=False)

print("\nSTRESS / SENSITIVITY TESTING")
print("Governed LR is held fixed. No model retraining or threshold tuning occurs.")
print("\nSCENARIO SUMMARY\n", summary.round(4).to_string(index=False))
print("\nTOP 15 BORROWERS BY ECL INCREASE UNDER COMBINED DETERIORATION\n")
print(impact.head(15).round(4).to_string(index=False))
print("\nThese are transparent synthetic sensitivity shocks, not regulatory stress scenarios or forecasts.")
