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

best_name=res.index[0]; best=models[best_name]; best_pd=preds[best_name]
out=df.iloc[Xte.index].copy()
out["predicted_pd"]=best_pd
out=add_score(out)
out=calculate_ecl(out)

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
print("\nBEST MODEL:",best_name)

# ROC curve
fpr,tpr,_=roc_curve(yte,best_pd)
plt.figure(figsize=(7,5)); plt.plot(fpr,tpr,label=f"{best_name} (AUC={roc_auc_score(yte,best_pd):.3f})")
plt.plot([0,1],[0,1],"--"); plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
plt.title("PD Model ROC Curve"); plt.legend(); plt.tight_layout()
(ROOT/"outputs/roc_curve.png").parent.mkdir(exist_ok=True)
plt.savefig(ROOT/"outputs/roc_curve.png",dpi=160); plt.close()

# Save scored portfolio
out.to_csv(ROOT/"data/processed/scored_portfolio.csv",index=False)
res.to_csv(ROOT/"outputs/model_validation.csv")
cal = calibration_table(yte, best_pd, bins=10)
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
