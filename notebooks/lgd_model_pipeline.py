"""Train, validate and deploy the synthetic facility-level workout LGD model."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/"src"))

import pandas as pd
from sklearn.model_selection import train_test_split

from lgd_model import (
    TARGET, NUMERIC_FEATURES, CATEGORICAL_FEATURES,
    gradient_boosting_lgd_model, ridge_lgd_challenger,
    predict_lgd, lgd_validation_summary, calibration_table, save_model,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs"
MODEL_DIR=ROOT/"models"
OUT.mkdir(parents=True,exist_ok=True)
MODEL_DIR.mkdir(parents=True,exist_ok=True)

df=pd.read_csv(ROOT/"data/raw/lgd_workout_history.csv")
required=set(NUMERIC_FEATURES+CATEGORICAL_FEATURES+[TARGET,"facility_id","ead_at_default"])
missing=required.difference(df.columns)
if missing:
    raise ValueError(f"Missing LGD workout fields: {sorted(missing)}")

train_idx,test_idx=train_test_split(
    df.index,test_size=.25,random_state=42
)

models={
    "Gradient Boosting":gradient_boosting_lgd_model(),
    "Ridge":ridge_lgd_challenger(),
}
rows=[]
preds={}
for name,m in models.items():
    m.fit(df.loc[train_idx],df.loc[train_idx,TARGET])
    p=predict_lgd(m,df.loc[test_idx])
    preds[name]=p
    s=lgd_validation_summary(
        df.loc[test_idx,TARGET],p,df.loc[test_idx,"ead_at_default"]
    )
    s["Model"]=name
    rows.append(s)

validation=pd.DataFrame(rows).set_index("Model")
validation.to_csv(OUT/"lgd_model_validation.csv")
print("\nLGD MODEL VALIDATION\n",validation.round(4).to_string())

# Governance decision is fixed ex ante: gradient boosting is the production-style
# champion for non-linear recovery interactions; Ridge remains an interpretable challenger.
champion_name="Gradient Boosting"
champion=models[champion_name]
champion_pred=preds[champion_name]
cal=calibration_table(df.loc[test_idx,TARGET],champion_pred,bins=10)
cal.to_csv(OUT/"lgd_calibration_deciles.csv",index=False)

holdout=df.loc[test_idx,[
    "facility_id","product_type","industry","ead_at_default","collateral_type",
    "collateral_coverage","lien_rank","guarantee_coverage","economic_lgd"
]].copy()
holdout["predicted_lgd"]=champion_pred
holdout.to_csv(OUT/"lgd_holdout_predictions.csv",index=False)

# Refit governed model on the full resolved-workout history after the independent
# holdout validation has been produced. This deployed model is then applied to the
# current synthetic portfolio; holdout metrics above remain the validation evidence.
deployed=gradient_boosting_lgd_model()
deployed.fit(df,df[TARGET])
save_model(deployed,MODEL_DIR/"lgd_workout_model.joblib")

print("\nLGD CALIBRATION DECILES\n",cal.round(4).to_string(index=False))
print(f"Saved deployed LGD model to {MODEL_DIR/'lgd_workout_model.joblib'}")
