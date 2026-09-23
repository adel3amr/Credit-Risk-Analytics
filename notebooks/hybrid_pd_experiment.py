"""Hybrid SME PD incremental-information experiment.

Run from repository root:
    python notebooks/hybrid_pd_experiment.py

The same unweighted Logistic Regression specification is used for each nested
information set so differences primarily reflect information content rather than
algorithm choice. All portfolio and added V2 features are synthetic.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data_preparation import load_data, prepare_data
from hybrid_features import feature_sets
from validation import validation_summary, calibration_table, ks_statistic
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

raw = load_data(ROOT / "data/raw/sme_credit_portfolio.csv")
# All engineered trajectory variables are generated upstream before the split.
# This experiment does not derive any feature using full-sample statistics.
model_df = prepare_data(raw)

y = model_df["default"]
train_idx, test_idx = train_test_split(
    model_df.index,
    test_size=0.25,
    stratify=y,
    random_state=42,
)

sets = feature_sets(model_df)
order = [
    "Financial only",
    "Financial + Current Behavior",
    "Financial + Current Behavior + Trajectory",
]
results = []
predictions = {}
train_predictions = {}
diagnostics = []
calibration_rows = []
confusion_rows = []

for set_name in order:
    cols = sets[set_name]
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000)),
    ])
    model.fit(model_df.loc[train_idx, cols], y.loc[train_idx])
    p_train = model.predict_proba(model_df.loc[train_idx, cols])[:, 1]
    p_test = model.predict_proba(model_df.loc[test_idx, cols])[:, 1]
    train_predictions[set_name] = p_train
    predictions[set_name] = p_test

    tr = validation_summary(y.loc[train_idx], p_train)
    te = validation_summary(y.loc[test_idx], p_test)
    row = dict(te)
    row["Information_Set"] = set_name
    row["Features"] = len(cols)
    row["Train_AUC"] = tr["ROC_AUC"]
    row["AUC_Train_Test_Gap"] = tr["ROC_AUC"] - te["ROC_AUC"]
    row["Train_KS"] = tr["KS"]
    row["KS_Train_Test_Gap"] = tr["KS"] - te["KS"]
    row["Train_Brier"] = tr["Brier"]
    row["Train_LogLoss"] = tr["LogLoss"]
    row["Train_Mean_PD"] = tr["Mean_PD"]
    row["Train_Observed_DR"] = tr["Observed_DR"]
    row["Train_Calibration_in_the_large"] = tr["Calibration_in_the_large"]
    results.append(row)

    for sample, yy, pp in [
        ("Train", y.loc[train_idx], p_train),
        ("Test", y.loc[test_idx], p_test),
    ]:
        d = validation_summary(yy, pp)
        d.update({"Information_Set": set_name, "Sample": sample})
        diagnostics.append(d)
        tab = calibration_table(yy, pp, bins=10)
        tab["Information_Set"] = set_name
        tab["Sample"] = sample
        calibration_rows.append(tab)

        # Confusion matrices are threshold-dependent. Report two transparent views:
        # 5% PD (business-style risk cutoff) and a prevalence-matched cutoff that
        # flags approximately the observed default share. Neither is model-tuned.
        prevalence = float(np.mean(yy))
        prev_cut = float(np.quantile(pp, 1 - prevalence))
        for label, threshold in [("PD_5pct", .05), ("Prevalence_matched", prev_cut)]:
            pred = (pp >= threshold).astype(int)
            tn, fp, fn, tp = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
            confusion_rows.append({
                "Information_Set": set_name, "Sample": sample,
                "Threshold_Type": label, "Threshold": threshold,
                "TN": tn, "FP": fp, "FN": fn, "TP": tp,
                "Sensitivity": tp / (tp + fn) if tp + fn else np.nan,
                "Specificity": tn / (tn + fp) if tn + fp else np.nan,
                "Precision": tp / (tp + fp) if tp + fp else np.nan,
            })

comparison = pd.DataFrame(results).set_index("Information_Set").loc[order]
comparison["AUC_lift_vs_financial"] = comparison["ROC_AUC"] - comparison.loc["Financial only", "ROC_AUC"]
comparison["Gini_lift_vs_financial"] = comparison["Gini"] - comparison.loc["Financial only", "Gini"]
comparison.to_csv(OUT / "information_set_comparison.csv")
pd.DataFrame(diagnostics).to_csv(OUT / "train_test_validation.csv", index=False)
pd.concat(calibration_rows, ignore_index=True).to_csv(OUT / "train_test_calibration_deciles.csv", index=False)
pd.DataFrame(confusion_rows).to_csv(OUT / "confusion_matrices.csv", index=False)

# Paired bootstrap isolates each incremental information layer on the common holdout.
rng = np.random.default_rng(42)
y_test = y.loc[test_idx].to_numpy()
boot_rows = []
for _ in range(1000):
    idx = rng.integers(0, len(y_test), len(y_test))
    y_b = y_test[idx]
    if len(np.unique(y_b)) < 2:
        continue
    from sklearn.metrics import roc_auc_score
    aucs = {name: roc_auc_score(y_b, predictions[name][idx]) for name in order}
    boot_rows.append({
        "current_behavior_minus_financial": aucs[order[1]] - aucs[order[0]],
        "trajectory_minus_current_behavior": aucs[order[2]] - aucs[order[1]],
    })
boot = pd.DataFrame(boot_rows)
pairs = [
    ("Current Behavior - Financial", "current_behavior_minus_financial"),
    ("Trajectory - Current Behavior", "trajectory_minus_current_behavior"),
]
bootstrap_summary = pd.DataFrame([{
    "Comparison": label,
    "Mean_AUC_Difference": boot[col].mean(),
    "CI_2.5%": boot[col].quantile(.025),
    "CI_97.5%": boot[col].quantile(.975),
} for label, col in pairs])
bootstrap_summary.to_csv(OUT / "auc_difference_bootstrap.csv", index=False)

# Trajectory provenance audit: quantify whether the observed incremental signal is
# expected from the frozen synthetic DGP rather than silently treating it as an
# empirical discovery. The DGP explicitly includes utilization_6m_change and
# months_above_80_utilization in latent default risk; avg utilization and breach
# count are correlated monitoring variables but have no direct target coefficient.
trajectory_provenance = pd.DataFrame([
    {"feature": "utilization_6m_change", "direct_in_frozen_default_dgp": 1,
     "dgp_coefficient": 1.20, "role": "direct latent-PD driver"},
    {"feature": "avg_utilization_6m", "direct_in_frozen_default_dgp": 0,
     "dgp_coefficient": 0.00, "role": "correlated behavioural summary"},
    {"feature": "months_above_80_utilization", "direct_in_frozen_default_dgp": 1,
     "dgp_coefficient": 0.08, "role": "direct latent-PD driver"},
    {"feature": "limit_breach_count", "direct_in_frozen_default_dgp": 0,
     "dgp_coefficient": 0.00, "role": "correlated EWS/conduct indicator"},
])
trajectory_provenance.to_csv(OUT / "trajectory_signal_provenance.csv", index=False)

# Holdout-only descriptive audit. This is diagnostic, not feature selection.
trajectory_audit = []
for col in ["utilization_6m_change", "avg_utilization_6m",
            "months_above_80_utilization", "limit_breach_count"]:
    x = raw.loc[test_idx, col].astype(float)
    trajectory_audit.append({
        "feature": col,
        "mean_nondefault": x[y.loc[test_idx] == 0].mean(),
        "mean_default": x[y.loc[test_idx] == 1].mean(),
        "spearman_with_default": x.corr(y.loc[test_idx].astype(float), method="spearman"),
        "spearman_with_current_utilization": x.corr(
            raw.loc[test_idx, "credit_utilization"].astype(float), method="spearman"
        ),
    })
pd.DataFrame(trajectory_audit).to_csv(OUT / "trajectory_signal_audit.csv", index=False)

print("\nINCREMENTAL INFORMATION TEST\n")
print(comparison.round(4))
print("\nPAIRED BOOTSTRAP AUC DIFFERENCES (95% percentile CI)")
print(bootstrap_summary.round(4))
print("\nTRAIN VS TEST VALIDATION")
print(pd.DataFrame(diagnostics).set_index(["Information_Set", "Sample"]).round(4))
print("\nCONFUSION MATRICES")
print(pd.DataFrame(confusion_rows).round(4))

borrower = raw.loc[test_idx].copy()
for name, prob in predictions.items():
    pd_col = "pd_" + name.lower().replace(" + ", "_").replace(" ", "_")
    borrower[pd_col] = prob
borrower["pd_change_current_to_trajectory"] = (
    borrower["pd_financial_current_behavior_trajectory"]
    - borrower["pd_financial_current_behavior"]
)
borrower.to_csv(OUT / "borrower_pd_comparison.csv", index=False)

ax = comparison["ROC_AUC"].plot(kind="bar", figsize=(10, 5))
ax.set_ylim(max(.50, comparison["ROC_AUC"].min() - .05), min(1, comparison["ROC_AUC"].max() + .05))
ax.set_ylabel("Test ROC-AUC")
ax.set_xlabel("")
ax.set_title("Incremental Information in SME PD Modeling")
plt.xticks(rotation=12, ha="right")
plt.tight_layout()
plt.savefig(OUT / "information_set_auc.png", dpi=180)
plt.close()

plt.figure(figsize=(8, 5))
plt.scatter(borrower["utilization_6m_change"], borrower["pd_change_current_to_trajectory"], alpha=.35, s=18)
plt.axhline(0, linestyle="--", linewidth=1)
plt.xlabel("6M change in credit-line utilization")
plt.ylabel("Trajectory PD - Current-behavior PD")
plt.title("Risk Direction: Incremental PD from Trajectory")
plt.tight_layout()
plt.savefig(OUT / "utilization_trend_pd_uplift.png", dpi=180)
plt.close()

print()
print("Saved:")
print("- outputs/information_set_comparison.csv")
print("- outputs/borrower_pd_comparison.csv")
print("- outputs/auc_difference_bootstrap.csv")
print("- outputs/trajectory_signal_provenance.csv")
print("- outputs/trajectory_signal_audit.csv")
print("- outputs/train_test_validation.csv")
print("- outputs/train_test_calibration_deciles.csv")
print("- outputs/confusion_matrices.csv")
print("- outputs/information_set_auc.png")
print("- outputs/utilization_trend_pd_uplift.png")
