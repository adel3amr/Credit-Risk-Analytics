"""Train, validate and deploy the synthetic facility-level workout LGD model."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/"src"))

import pandas as pd
from sklearn.model_selection import train_test_split

from lgd_model import (
    TARGET, NUMERIC_FEATURES, CATEGORICAL_FEATURES,
    gradient_boosting_lgd_model, ridge_lgd_challenger,
    huber_gradient_boosting_lgd_challenger, random_forest_lgd_challenger,
    hist_gradient_lgd_challenger,
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
    "Huber Gradient Boosting":huber_gradient_boosting_lgd_challenger(),
    "Random Forest":random_forest_lgd_challenger(),
    "Histogram Gradient Boosting":hist_gradient_lgd_challenger(),
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

# Challenger tail comparison. This is diagnostic only: the governed champion is
# not replaced merely because a challenger looks better on an already-observed holdout.
tail_compare=[]
y_hold=df.loc[test_idx,TARGET]
w_hold=df.loc[test_idx,"ead_at_default"].clip(lower=1)
for name,p in preds.items():
    tmp=pd.DataFrame({"actual":y_hold.to_numpy(),"pred":p,"ead":w_hold.to_numpy()})
    tmp["error"]=tmp["pred"]-tmp["actual"]
    for q in [.90,.95]:
        cutoff=float(tmp["pred"].quantile(q))
        g=tmp.loc[tmp["pred"]>=cutoff]
        tail_compare.append({
            "Model":name,"tail_percentile":q,"facilities":len(g),"cutoff":cutoff,
            "actual_lgd":g["actual"].mean(),"predicted_lgd":g["pred"].mean(),
            "bias":g["error"].mean(),
            "ead_weighted_bias":float((g["error"]*g["ead"]).sum()/g["ead"].sum()),
            "rmse":float((g["error"].pow(2).mean())**.5),
        })
tail_challenger=pd.DataFrame(tail_compare)
tail_challenger.to_csv(OUT/"lgd_challenger_tail_comparison.csv",index=False)
print("\nLGD CHALLENGER TAIL COMPARISON\n",tail_challenger.round(4).to_string(index=False))

# Governance decision remains fixed ex ante: the original Gradient Boosting model is the governed champion.
# Additional models are diagnostic challengers only; the untouched holdout is not used to tune or silently replace the champion.
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

# Segment-level validation: detect pockets of bias hidden by near-zero portfolio bias.
segment_rows=[]
holdout_validation=df.loc[test_idx].copy()
holdout_validation["predicted_lgd"]=champion_pred
holdout_validation["error"]=holdout_validation["predicted_lgd"]-holdout_validation[TARGET]
for dimension in ["collateral_type","lien_rank","product_type"]:
    for segment,g in holdout_validation.groupby(dimension,dropna=False):
        w=g["ead_at_default"].clip(lower=1)
        segment_rows.append({
            "dimension":dimension,
            "segment":str(segment),
            "facilities":len(g),
            "ead":g["ead_at_default"].sum(),
            "actual_lgd":g[TARGET].mean(),
            "predicted_lgd":g["predicted_lgd"].mean(),
            "mean_error_bias":g["error"].mean(),
            "mae":g["error"].abs().mean(),
            "rmse":float((g["error"].pow(2).mean())**.5),
            "ead_weighted_actual_lgd":float((g[TARGET]*w).sum()/w.sum()),
            "ead_weighted_predicted_lgd":float((g["predicted_lgd"]*w).sum()/w.sum()),
            "ead_weighted_bias":float((g["error"]*w).sum()/w.sum()),
            "ead_weighted_mae":float((g["error"].abs()*w).sum()/w.sum()),
            "ead_weighted_rmse":float(((g["error"].pow(2)*w).sum()/w.sum())**.5),
        })
segment_validation=pd.DataFrame(segment_rows)
segment_validation.to_csv(OUT/"lgd_segment_validation.csv",index=False)

# Tail validation: the highest predicted-LGD facilities are particularly important
# because aggregate near-zero bias can conceal underprediction in severe workouts.
tail_rows=[]
for q in [.75,.90,.95]:
    cutoff=float(holdout_validation["predicted_lgd"].quantile(q))
    g=holdout_validation.loc[holdout_validation["predicted_lgd"]>=cutoff]
    w=g["ead_at_default"].clip(lower=1)
    tail_rows.append({
        "predicted_lgd_percentile":q,
        "cutoff":cutoff,
        "facilities":len(g),
        "actual_lgd":g[TARGET].mean(),
        "predicted_lgd":g["predicted_lgd"].mean(),
        "mean_error_bias":g["error"].mean(),
        "rmse":float((g["error"].pow(2).mean())**.5),
        "ead_weighted_bias":float((g["error"]*w).sum()/w.sum()),
    })
tail_validation=pd.DataFrame(tail_rows)
tail_validation.to_csv(OUT/"lgd_tail_validation.csv",index=False)
print("\nLGD SEGMENT VALIDATION\n",segment_validation.round(4).to_string(index=False))
print("\nLGD HIGH-LOSS TAIL VALIDATION\n",tail_validation.round(4).to_string(index=False))

# Refit governed model on the full resolved-workout history after the independent
# holdout validation has been produced. This deployed model is then applied to the
# current synthetic portfolio; holdout metrics above remain the validation evidence.
deployed=gradient_boosting_lgd_model()
deployed.fit(df,df[TARGET])
save_model(deployed,MODEL_DIR/"lgd_workout_model.joblib")

print("\nLGD CALIBRATION DECILES\n",cal.round(4).to_string(index=False))
print(f"Saved deployed LGD model to {MODEL_DIR/'lgd_workout_model.joblib'}")
