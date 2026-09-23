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
from validation import validation_summary, calibration_table, threshold_diagnostics
from scorecard import add_score, add_risk_rating
from ecl import calculate_ecl

ROOT=Path(__file__).resolve().parents[1]
(ROOT/"outputs").mkdir(parents=True, exist_ok=True)
(ROOT/"data/processed").mkdir(parents=True, exist_ok=True)
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

# Fixed reference thresholds provide operational classification diagnostics without
# optimizing a cutoff on the untouched holdout.
threshold_diag = threshold_diagnostics(yte, primary_pd, thresholds=(0.05, 0.10))
threshold_diag.to_csv(ROOT/"outputs/pd_threshold_diagnostics.csv", index=False)
print("\nREFERENCE THRESHOLD DIAGNOSTICS (not optimized)\n", threshold_diag.round(4))

out=df.loc[Xte.index].copy()
out["predicted_pd"]=primary_pd
out=add_score(out)
out=calculate_ecl(out)
# Make the existing operational monitoring flag available before rating.
# This does not change the existing rating policy because add_risk_rating
# still preserves its original risk_direction fallback/union logic.
out["ews_monitoring_flag"] = (
    (out["risk_direction"] == "Deteriorating") & (out["stage"] == "Stage 1")
).astype(int)
out=add_risk_rating(out)

# Borrower-level audit trace: preserve the full reporting-date chain from raw
# synthetic inputs through governed PD, score/EWS/stage and ECL. This is intended
# for manual review, not as an additional modeling dataset.
audit_trace_cols = [
    "customer_id", "industry", "annual_revenue", "ebitda_margin", "current_ratio",
    "leverage_ratio", "cash_flow", "debt_to_income", "years_in_business",
    "credit_utilization", "utilization_6m_ago", "utilization_6m_change",
    "avg_utilization_6m", "months_above_80_utilization", "limit_breach_count",
    "consecutive_ews_months", "delinquencies_12m", "previous_defaults",
    "days_past_due", "current_credit_impaired", "collateral_value",
    "collateral_coverage", "collateral_type", "collateral_haircut", "recognized_collateral",
    "recognized_collateral_coverage", "unsecured_ead", "unsecured_lgd", "loan_limit", "loan_draw_ratio", "loans", "loan_ead", "ovd", "ovd_ead", "trade",
    "direct_limit", "direct_drawn", "indirect_limit", "total_credit_limit", "total_utilized_amount",
    "trade_type", "trade_ccf", "trade_ead", "ead", "lgd", "loan_term_months",
    "predicted_pd", "pit_pd_12m", "pd_12m_upside", "pd_12m_baseline",
    "pd_12m_downside", "forward_looking_pd_12m", "credit_score", "risk_band", "risk_rating", "rating_status",
    "risk_direction", "ews_signal_count", "ews_sicr_flag", "stage", "sicr_flag",
    "ecl_12m", "lifetime_pd_upside", "lifetime_pd_baseline",
    "lifetime_pd_downside", "lifetime_pd", "ecl", "default",
]
missing_audit_cols = [col for col in audit_trace_cols if col not in out.columns]
if missing_audit_cols:
    raise ValueError(f"Missing required borrower audit-trace columns: {missing_audit_cols}")
audit_trace = out[audit_trace_cols].copy()
audit_trace.to_csv(ROOT/"outputs/borrower_audit_trace.csv", index=False)

# A compact data dictionary makes the manual trace review explicit.
audit_dictionary = pd.DataFrame([
    ("customer_id", "Raw", "Synthetic borrower identifier"),
    ("financial/current-behaviour fields", "Raw / governed PD inputs", "Reporting-date borrower information"),
    ("utilization_6m_* / limit_breach_count", "EWS inputs", "Derived from chronological 36-month history"),
    ("consecutive_ews_months", "EWS", "Consecutive deteriorating months ending at M0"),
    ("predicted_pd / pit_pd_12m", "PD", "Governed Logistic Regression reporting-date 12-month PIT-oriented PD"),
    ("pd_12m_upside / baseline / downside", "Forward-looking PD", "Fixed scenario shifts to PIT default odds; synthetic assumptions"),
    ("forward_looking_pd_12m", "Forward-looking PD", "Probability-weighted 12-month scenario PD used in ECL"),
    ("credit_score / risk_band", "Risk segmentation", "Transformations of predicted PD; not accounting stages"),
    ("risk_rating / rating_status", "Operational rating", "1-6 performing PD grades; 7 watchlist; 8-10 Stage 3 severity. Full cash coverage sets non-Stage-3 borrowers to Rating 1."),
    ("risk_direction / ews_signal_count", "EWS", "Monitoring status; separate from PD grade"),
    ("stage", "Accounting proxy", "Simplified Stage 1/2/3 assignment using reporting-date triggers"),
    ("loan_ead", "EAD", "100% of synthetic current term-loan outstanding"),
    ("ovd_ead", "EAD", "100% of synthetic approved OVD limit"),
    ("trade_ead", "EAD", "Trade amount multiplied by synthetic instrument CCF"),
    ("ead", "EAD", "Sum of loan, OVD and trade EAD"),
    ("collateral_coverage / lgd", "LGD", "Aggregate borrower-level synthetic recovery proxy"),
    ("ecl_12m", "ECL", "forward_looking_pd_12m x lgd x ead"),
    ("lifetime_pd", "ECL", "Probability-weighted scenario lifetime PD using a simplified constant-hazard term structure"),
    ("ecl", "ECL", "Stage-dependent simplified ECL"),
    ("default", "Validation outcome", "Future 12-month synthetic outcome; not a reporting-date input"),
], columns=["field_or_group", "layer", "interpretation"])
audit_dictionary.to_csv(ROOT/"outputs/borrower_audit_trace_dictionary.csv", index=False)

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
    (out["ews_sicr_flag"] == 1) & (out["consecutive_ews_months"].fillna(0) >= 9)
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
# Stage 1. The flag is created before rating and reused here for reporting.
ews_monitoring = out[out["ews_monitoring_flag"] == 1].copy()
# Refresh Stage 2 subset after the monitoring flag is added to the master output.
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
        mean_consecutive_ews_months=("consecutive_ews_months", "mean"),
    )
    .reset_index()
)
ews_9m_validation["portfolio_share"] = ews_9m_validation["customers"] / len(out)
ews_9m_validation.to_csv(ROOT/"outputs/ews_9m_policy_validation.csv", index=False)
print("\nFIXED 9-MONTH EWS POLICY VALIDATION")
print(ews_9m_validation.round(4).to_string(index=False))

audit.to_csv(ROOT/"outputs/stage2_trigger_audit.csv", index=False)

monitor_cols = [
    "customer_id", "industry", "predicted_pd", "pit_pd_12m", "forward_looking_pd_12m",
    "pd_12m_upside", "pd_12m_baseline", "pd_12m_downside",
    "risk_band", "risk_rating", "rating_status", "credit_score", "stage",
    "risk_direction", "ews_signal_count", "consecutive_ews_months", "ews_monitoring_flag", "days_past_due", "delinquencies_12m",
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
ews_monitoring[monitor_cols].sort_values("predicted_pd", ascending=False).to_csv(
    ROOT/"outputs/ews_monitoring_review.csv", index=False
)
print("\nSTAGE 2 TRIGGER AUDIT (overlapping triggers)\n", audit.round(4))
print("\nEWS MONITORING POPULATION (Stage 1 deteriorating borrowers):", len(ews_monitoring))

print("\nRISK BANDS\n",out.groupby("risk_band").agg(
    customers=("customer_id","count"), observed_default=("default","mean"),
    exposure=("ead","sum"), ecl_12m=("ecl_12m","sum")).round(3))
print("\nIFRS 9-STYLE STAGING\n",out.groupby("stage").agg(
    customers=("customer_id","count"), observed_default=("default","mean"),
    exposure=("ead","sum"), ecl=("ecl","sum")).round(3))
print("\nPORTFOLIO MEAN PIT-ORIENTED PD:",round(out.pit_pd_12m.mean(),4))
print("PORTFOLIO MEAN FORWARD-LOOKING PD:",round(out.forward_looking_pd_12m.mean(),4))
print("HOLDOUT OBSERVED DEFAULT RATE:",round(out.default.mean(),4))
print("TOTAL 12M ECL (diagnostic):",round(out.ecl_12m.sum(),2))
print("TOTAL STAGED ECL:",round(out.ecl.sum(),2))

# ECL coverage diagnostics: expose why provision coverage differs by stage.
# These are diagnostics only; they do not impose arbitrary IFRS 9 loss floors.
ecl_coverage = (
    out.groupby("stage", observed=False)
    .agg(
        borrowers=("customer_id", "count"),
        exposure=("ead", "sum"),
        ecl=("ecl", "sum"),
        mean_pd_12m=("forward_looking_pd_12m", "mean"),
        mean_lifetime_pd=("lifetime_pd", "mean"),
        mean_lgd=("lgd", "mean"),
        mean_collateral_coverage=("collateral_coverage", "mean"),
        mean_recognized_collateral_coverage=("recognized_collateral_coverage", "mean"),
        median_recognized_collateral_coverage=("recognized_collateral_coverage", "median"),
        mean_term_months=("loan_term_months", "mean"),
    )
    .reset_index()
)
ecl_coverage["ecl_to_ead"] = ecl_coverage["ecl"] / ecl_coverage["exposure"].clip(lower=1)
ecl_coverage.to_csv(ROOT/"outputs/ecl_coverage_diagnostics.csv", index=False)

collateral_diag = (
    out.groupby("collateral_type", observed=False)
    .agg(
        borrowers=("customer_id", "count"),
        exposure=("ead", "sum"),
        mean_nominal_coverage=("collateral_coverage", "mean"),
        mean_recognized_coverage=("recognized_collateral_coverage", "mean"),
        mean_lgd=("lgd", "mean"),
        ecl=("ecl", "sum"),
    )
    .reset_index()
)
collateral_diag["portfolio_share"] = collateral_diag["borrowers"] / len(out)
collateral_diag["ecl_to_ead"] = collateral_diag["ecl"] / collateral_diag["exposure"].clip(lower=1)
collateral_diag.to_csv(ROOT/"outputs/collateral_lgd_diagnostics.csv", index=False)
print("\nCOLLATERAL / LGD DIAGNOSTICS\n", collateral_diag.round(4).to_string(index=False))

stage2_diag = out.loc[out["stage"] == "Stage 2", [
    "customer_id", "ead", "ecl", "forward_looking_pd_12m", "lifetime_pd",
    "lgd", "collateral_value", "collateral_coverage", "recognized_collateral",
    "recognized_collateral_coverage", "loan_term_months",
    "risk_direction", "consecutive_ews_months", "days_past_due",
]].copy()
stage2_diag["ecl_to_ead"] = stage2_diag["ecl"] / stage2_diag["ead"].clip(lower=1)
stage2_diag.to_csv(ROOT/"outputs/stage2_ecl_diagnostics.csv", index=False)
print("\nECL COVERAGE DIAGNOSTICS\n", ecl_coverage.round(4).to_string(index=False))

# Forward-looking macro overlay diagnostics. This separates model validation
# (performed on the PIT-oriented PD) from the scenario adjustment used for ECL.
macro_diag = pd.DataFrame({
    "metric": [
        "mean_pit_pd_12m", "mean_upside_pd_12m", "mean_baseline_pd_12m",
        "mean_downside_pd_12m", "mean_forward_looking_pd_12m",
        "pit_12m_ecl", "forward_looking_12m_ecl", "forward_looking_staged_ecl",
    ],
    "value": [
        out["pit_pd_12m"].mean(), out["pd_12m_upside"].mean(),
        out["pd_12m_baseline"].mean(), out["pd_12m_downside"].mean(),
        out["forward_looking_pd_12m"].mean(),
        (out["pit_pd_12m"] * out["lgd"] * out["ead"]).sum(),
        out["ecl_12m"].sum(), out["ecl"].sum(),
    ],
})
macro_diag.to_csv(ROOT/"outputs/macro_scenario_diagnostics.csv", index=False)
print("\nFORWARD-LOOKING MACRO DIAGNOSTICS\n", macro_diag.round(6).to_string(index=False))
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
