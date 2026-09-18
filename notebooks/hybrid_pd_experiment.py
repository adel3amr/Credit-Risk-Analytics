"""
Hybrid SME Credit Risk Analytics & PD Modeling
Run from repository root: python notebooks/hybrid_pd_experiment.py

Compares nested information sets using the same interpretable Logistic Regression
model so changes in performance reflect information content rather than algorithm
choice. The data and added qualitative/trajectory fields are synthetic.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from data_preparation import load_data, prepare_data
from pd_model import logistic_model
from validation import validation_summary
from hybrid_features import add_hybrid_features, feature_sets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

raw = load_data(ROOT / "data/raw/sme_credit_portfolio.csv")
hybrid_raw = add_hybrid_features(raw)
model_df = prepare_data(hybrid_raw)

y = model_df["default"]
train_idx, test_idx = train_test_split(
    model_df.index, test_size=.25, stratify=y, random_state=42
)

sets = feature_sets(model_df)
results, predictions = [], {}

for set_name, cols in sets.items():
    # Unweighted logistic regression is intentional here: class weighting can\n    # improve minority-class ranking but distorts raw probabilities, which is\n    # undesirable when the output is interpreted as PD.\n    model = Pipeline([\n        ("imputer", SimpleImputer(strategy="median")),\n        ("scaler", StandardScaler()),\n        ("model", LogisticRegression(max_iter=2000))\n    ])
    model.fit(model_df.loc[train_idx, cols], y.loc[train_idx])
    prob = model.predict_proba(model_df.loc[test_idx, cols])[:, 1]
    predictions[set_name] = prob
    row = validation_summary(y.loc[test_idx], prob)
    row["Information_Set"] = set_name
    row["Features"] = len(cols)
    results.append(row)

comparison = (
    pd.DataFrame(results)
    .set_index("Information_Set")
    .loc[["Financial only", "Financial + Behavioral", "Hybrid"]]
)
comparison["AUC_lift_vs_financial"] = comparison["ROC_AUC"] - comparison.loc["Financial only", "ROC_AUC"]
comparison["Gini_lift_vs_financial"] = comparison["Gini"] - comparison.loc["Financial only", "Gini"]
comparison.to_csv(OUT / "information_set_comparison.csv")\n\nprint(f"
Holdout observed default rate: {y.loc[test_idx].mean():.4f}")\nfor name, prob in predictions.items():\n    print(f"{name} mean predicted PD: {prob.mean():.4f}")

print("\nINCREMENTAL INFORMATION TEST\n")
print(comparison.round(4))

# Borrower-level PD comparison for the same holdout population.
borrower = hybrid_raw.loc[test_idx].copy()
for name, prob in predictions.items():
    borrower["pd_" + name.lower().replace(" + ", "_").replace(" ", "_")] = prob

borrower["pd_change_financial_to_hybrid"] = (
    borrower["pd_hybrid"] - borrower["pd_financial_only"]
)
borrower.sort_values("pd_change_financial_to_hybrid", ascending=False).to_csv(
    OUT / "borrower_pd_comparison.csv", index=False
)

# Publication-ready information-set comparison chart.
ax = comparison["ROC_AUC"].plot(kind="bar", figsize=(8, 5))
ax.set_ylim(max(.50, comparison["ROC_AUC"].min() - .05),
            min(1.0, comparison["ROC_AUC"].max() + .05))
ax.set_ylabel("ROC-AUC")
ax.set_xlabel("")
ax.set_title("Incremental Information in SME PD Modeling")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(OUT / "information_set_auc.png", dpi=180)
plt.close()

# Relationship between utilization direction and hybrid PD uplift.
plt.figure(figsize=(8, 5))
plt.scatter(
    borrower["utilization_6m_change"],
    borrower["pd_change_financial_to_hybrid"],
    alpha=.35, s=18
)
plt.axhline(0, linestyle="--", linewidth=1)
plt.xlabel("6M change in credit-line utilization")
plt.ylabel("Hybrid PD - Financial-only PD")
plt.title("Risk Direction: Utilization Trend vs Incremental PD")
plt.tight_layout()
plt.savefig(OUT / "utilization_trend_pd_uplift.png", dpi=180)
plt.close()

print("\nSaved:")
print("- outputs/information_set_comparison.csv")
print("- outputs/borrower_pd_comparison.csv")
print("- outputs/information_set_auc.png")
print("- outputs/utilization_trend_pd_uplift.png")
