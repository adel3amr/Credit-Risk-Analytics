"""
Credit Risk Analytics & PD Modeling
Run from repository root: python notebooks/credit_risk_pipeline.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/"src"))

import pandas as pd, numpy as np, matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, roc_curve
from data_preparation import load_data, prepare_data, pd_feature_columns
from pd_model import logistic_model, random_forest_model, gradient_boosting_model
from validation import validation_summary, calibration_table
from scorecard import add_score
from ecl import calculate_ecl

ROOT=Path(__file__).resolve().parents[1]
df=load_data(ROOT/"data/raw/sme_credit_portfolio.csv")
model_df=prepare_data(df)
X=model_df[pd_feature_columns(model_df)]
y=model_df["default"]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,stratify=y,random_state=42)

models={"Logistic Regression":logistic_model(),
        "Random Forest":random_forest_model(),
        "Gradient Boosting":gradient_boosting_model()}
results=[]
preds={}
for name,m in models.items():
    m.fit(Xtr,ytr); pr=m.predict_proba(Xte)[:,1]; preds[name]=pr
    s=validation_summary(yte,pr); s["Model"]=name; results.append(s)

res=pd.DataFrame(results).set_index("Model").sort_values("ROC_AUC",ascending=False)
print("\nMODEL VALIDATION\n",res.round(4))

# Governance decision: Logistic Regression is the primary PD model because
# interpretability and calibration are core requirements. RF/GB remain challengers;
# the primary model is not selected dynamically on holdout AUC.
primary_name="Logistic Regression"
primary=models[primary_name]
primary_pd=preds[primary_name]
out=df.iloc[Xte.index].copy()
out["predicted_pd"]=primary_pd
out=add_score(out)
out=calculate_ecl(out)

# Transparent Stage 2 trigger audit. Flags may overlap by design.
dpd = out["days_past_due"].fillna(0)
delinq = out["delinquencies_12m"].fillna(0)
util = out["credit_utilization"].fillna(0)
prev = out["previous_defaults"].fillna(0)
out["trigger_dpd_30_89"] = ((dpd >= 30) & (dpd < 90)).astype(int)
out["trigger_delinquency"] = (delinq >= 2).astype(int)
out["trigger_utilization_conduct"] = ((util >= .85) & (dpd > 0)).astype(int)
out["trigger_previous_default_pd"] = ((prev >= 1) & (out["predicted_pd"] >= .05)).astype(int)
out["trigger_ews_deterioration"] = out["ews_sicr_flag"].astype(int)
out["trigger_ews_9m_persistence"] = (
    (out["ews_sicr_flag"] == 1) & (out["months_on_ews_watchlist"].fillna(0) >= 9)
).astype(int)
trigger_cols = [
    "trigger_dpd_30_89", "trigger_delinquency", "trigger_utilization_conduct",
    "trigger_previous_default_pd", "trigger_ews_deterioration",
    "trigger_ews_9m_persistence",
]
# EWS is reported alongside accounting-stage triggers but does not itself cause Stage 2.
accounting_trigger_cols = [
    "trigger_dpd_30_89", "trigger_delinquency", "trigger_utilization_conduct",
    "trigger_previous_default_pd", "trigger_ews_9m_persistence",
]
out["stage2_trigger_count"] = out[accounting_trigger_cols].sum(axis=1)

stage2 = out[out["stage"] == "Stage 2"].copy()
audit = pd.DataFrame({
    "trigger": trigger_cols,
    "stage2_customers": [int(stage2[col].sum()) for col in trigger_cols],
})
audit["share_of_stage2"] = audit["stage2_customers"] / max(len(stage2), 1)

# Separate monitoring population: deterioration can exist while an exposure remains
# Stage 1. This makes risk direction visible without mechanically forcing SICR.
out["watchlist_flag"] = (
    (out["risk_direction"] == "Deteriorating") & (out["stage"] == "Stage 1")
).astype(int)
watchlist = out[out["watchlist_flag"] == 1].copy()
# Refresh Stage 2 subset after watchlist_flag is added to the master output.
stage2 = out[out["stage"] == "Stage 2"].copy()
# Validate the fixed 9-month persistence rule without tuning the threshold.
other_s2_trigger_cols = [
    "trigger_dpd_30_89", "trigger_delinquency",
    "trigger_utilization_conduct", "trigger_previous_default_pd",
]
other_s2 = out[other_s2_trigger_cols].max(axis=1).astype(int)
persistent9 = out["trigger_ews_9m_persistence"].astype(int)
current_deteriorating = out["trigger_ews_deterioration"].astype(int)
stage3_mask = out["stage"] == "Stage 3"
out["ews_9m_validation_group"] = np.select(
    [
        stage3_mask,
        (persistent9 == 1) & (other_s2 == 0),
        (persistent9 == 1) & (other_s2 == 1),
        (current_deteriorating == 1) & (persistent9 == 0) & (other_s2 == 0),
        (other_s2 == 1) & (persistent9 == 0),
    ],
    [
        "Stage 3",
        "9m EWS persistence only",
        "9m EWS + other Stage 2 trigger",
        "EWS deteriorating <9m only",
        "Other Stage 2 trigger only",
    ],
    default="Stage 1 - no current deterioration",
)
ews_9m_validation = (
    out.groupby("ews_9m_validation_group")
    .agg(
        customers=("customer_id", "count"),
        defaults=("default", "sum"),
        observed_default_rate=("default", "mean"),
        mean_predicted_pd=("predicted_pd", "mean"),
        exposure=("ead", "sum"),
        ecl=("ecl", "sum"),
        mean_watchlist_months=("months_on_ews_watchlist", "mean"),
    )
    .reset_index()
)
ews_9m_validation["portfolio_share"] = ews_9m_validation["customers"] / len(out)
ews_9m_validation.to_csv(ROOT/"outputs/ews_9m_policy_validation.csv", index=False)
print("\nFIXED 9-MONTH EWS POLICY VALIDATION")
print(ews_9m_validation.round(4).to_string(index=False))

audit.to_csv(ROOT/"outputs/stage2_trigger_audit.csv", index=False)

monitor_cols = [
    "customer_id", "industry", "predicted_pd", "risk_band", "credit_score", "stage",
    "risk_direction", "ews_signal_count", "months_on_ews_watchlist", "watchlist_flag", "days_past_due", "delinquencies_12m",
    "previous_defaults", "credit_utilization", "utilization_6m_change",
    "avg_utilization_6m", "months_above_80_utilization", "limit_breach_count",
    "loans", "ovd", "trade", "trade_type", "ead", "lgd", "ecl_12m",
    "lifetime_pd", "ecl", *trigger_cols, "stage2_trigger_count", "default",
]
monitor_cols = [col for col in monitor_cols if col in out.columns]
out[monitor_cols].sort_values(["stage", "predicted_pd"], ascending=[False, False]).to_csv(
    ROOT/"outputs/portfolio_monitoring.csv", index=False
)
stage2[monitor_cols].sort_values("predicted_pd", ascending=False).to_csv(
    ROOT/"outputs/stage2_customer_review.csv", index=False
)
watchlist[monitor_cols].sort_values("predicted_pd", ascending=False).to_csv(
    ROOT/"outputs/ews_watchlist_review.csv", index=False
)
print("\nSTAGE 2 TRIGGER AUDIT (overlapping triggers)\n", audit.round(4))
print("\nEWS WATCHLIST (Stage 1 deteriorating borrowers):", len(watchlist))

print("\nRISK BANDS\n",out.groupby("risk_band").agg(
    customers=("customer_id","count"), observed_default=("default","mean"),
    exposure=("ead","sum"), ecl_12m=("ecl_12m","sum")).round(3))
print("\nIFRS 9-STYLE STAGING\n",out.groupby("stage").agg(
    customers=("customer_id","count"), observed_default=("default","mean"),
    exposure=("ead","sum"), ecl=("ecl","sum")).round(3))
print("\nPORTFOLIO MEAN PREDICTED PD:",round(out.predicted_pd.mean(),4))
print("HOLDOUT OBSERVED DEFAULT RATE:",round(out.default.mean(),4))
print("TOTAL 12M ECL (diagnostic):",round(out.ecl_12m.sum(),2))
print("TOTAL STAGED ECL:",round(out.ecl.sum(),2))
print("\nPRIMARY GOVERNED PD MODEL:",primary_name)

# ROC curve
fpr,tpr,_=roc_curve(yte,primary_pd)
plt.figure(figsize=(7,5)); plt.plot(fpr,tpr,label=f"{primary_name} (AUC={roc_auc_score(yte,primary_pd):.3f})")
plt.plot([0,1],[0,1],"--"); plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
plt.title("PD Model ROC Curve"); plt.legend(); plt.tight_layout()
(ROOT/"outputs/roc_curve.png").parent.mkdir(exist_ok=True)
plt.savefig(ROOT/"outputs/roc_curve.png",dpi=160); plt.close()

# Save scored portfolio
out.to_csv(ROOT/"data/processed/scored_portfolio.csv",index=False)
res.to_csv(ROOT/"outputs/model_validation.csv")
cal = calibration_table(yte, primary_pd, bins=10)
cal.to_csv(ROOT/"outputs/calibration_deciles.csv", index=False)
print("\nCALIBRATION DECILES\n", cal.round(4))

plt.figure(figsize=(7,5))
plt.plot(cal["mean_predicted_pd"], cal["observed_default_rate"], marker="o", label="Holdout deciles")
lim = max(cal["mean_predicted_pd"].max(), cal["observed_default_rate"].max()) * 1.05
plt.plot([0, lim], [0, lim], "--", label="Perfect calibration")
plt.xlabel("Mean predicted PD")
plt.ylabel("Observed default rate")
plt.title("PD Calibration by Holdout Decile")
plt.legend()
plt.tight_layout()
plt.savefig(ROOT/"outputs/calibration_plot.png", dpi=160)
plt.close()
