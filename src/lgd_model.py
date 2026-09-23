"""Facility-level workout LGD modelling and portfolio application."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
    "ead_at_default", "collateral_coverage", "guarantee_coverage",
    "leverage_at_default", "current_ratio_at_default", "management_quality",
]
CATEGORICAL_FEATURES = ["product_type","industry","collateral_type","lien_rank"]
TARGET = "economic_lgd"


def _preprocessor():
    return ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), NUMERIC_FEATURES),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL_FEATURES),
    ], remainder="drop", sparse_threshold=0)


def gradient_boosting_lgd_model():
    return Pipeline([
        ("prep", _preprocessor()),
        ("model", GradientBoostingRegressor(
            n_estimators=220, max_depth=3, learning_rate=.035,
            min_samples_leaf=25, random_state=42,
        )),
    ])


def ridge_lgd_challenger():
    return Pipeline([
        ("prep", _preprocessor()),
        ("model", Ridge(alpha=8.0)),
    ])


def predict_lgd(model, df):
    p = np.asarray(model.predict(df), dtype=float)
    return np.clip(p, 0.0, 1.0)


def lgd_validation_summary(y_true, y_pred, ead=None):
    y = np.asarray(y_true,dtype=float)
    p = np.asarray(y_pred,dtype=float)
    out = {
        "MAE": mean_absolute_error(y,p),
        "RMSE": mean_squared_error(y,p) ** .5,
        "R2": r2_score(y,p),
        "Mean_Actual_LGD": float(y.mean()),
        "Mean_Predicted_LGD": float(p.mean()),
        # Bias convention: prediction minus realization. Positive = overprediction / conservative bias.
        "Mean_Error_Bias": float(np.mean(p-y)),
        "Calibration_in_the_large": float(y.mean()-p.mean()),
    }
    if ead is not None:
        w=np.asarray(ead,dtype=float)
        out["EAD_Weighted_MAE"] = float(np.average(np.abs(y-p),weights=np.maximum(w,1)))
        out["EAD_Weighted_RMSE"] = float(np.sqrt(np.average((y-p)**2,weights=np.maximum(w,1))))
        out["EAD_Weighted_Mean_Error_Bias"] = float(np.average(p-y,weights=np.maximum(w,1)))
        out["EAD_Weighted_Actual_LGD"] = float(np.average(y,weights=np.maximum(w,1)))
        out["EAD_Weighted_Predicted_LGD"] = float(np.average(p,weights=np.maximum(w,1)))
    return out


def calibration_table(y_true, y_pred, bins=10):
    x=pd.DataFrame({"actual":np.asarray(y_true),"pred":np.asarray(y_pred)})
    x["bucket"]=pd.qcut(x["pred"].rank(method="first"),q=bins,labels=False)+1
    return x.groupby("bucket",as_index=False).agg(
        facilities=("actual","size"),
        mean_predicted_lgd=("pred","mean"),
        mean_actual_lgd=("actual","mean"),
    )


def portfolio_to_facilities(borrowers):
    """Expand borrower rows into facility rows using reporting-date product EAD."""
    rows=[]
    for _,x in borrowers.iterrows():
        base={
            "customer_id":str(x["customer_id"]),
            "industry":str(x["industry"]),
            "collateral_type":str(x["collateral_type"]),
            "collateral_coverage":float(x["collateral_coverage"]),
            "leverage_at_default":float(x["leverage_ratio"]),
            "current_ratio_at_default":float(x["current_ratio"]),
            "management_quality":float(x.get("management_quality",3)),
        }
        products=[
            ("Term Loan",float(x.get("loan_ead",0)),0.0,int(x.get("loan_remaining_months",x.get("loan_term_months",12)))),
            ("OVD",float(x.get("ovd_ead",0)),0.0,int(x.get("ovd_remaining_months",12))),
        ]
        trade_type=str(x.get("trade_type","None"))
        if trade_type!="None":
            guarantee_map={"Import LC":.20,"Performance Guarantee":.35,"Financial Guarantee":.55}
            products.append((
                trade_type,float(x.get("trade_ead",0)),guarantee_map.get(trade_type,0.0),
                int(x.get("trade_remaining_months",12))
            ))
        for product,ead,guarantee,remaining_months in products:
            if ead <= 0:
                continue
            lien = "Unsecured" if base["collateral_type"]=="Unsecured" else (
                "First" if product=="Term Loan" or base["collateral_type"]=="Cash" else "Second"
            )
            rows.append({
                **base,
                "facility_id":f'{base["customer_id"]}-{len(rows)+1:06d}',
                "product_type":product,
                "ead_at_default":ead,
                "guarantee_coverage":guarantee,
                "lien_rank":lien,
                "remaining_months":remaining_months,
            })
    return pd.DataFrame(rows)


def aggregate_borrower_lgd(facilities):
    g=facilities.copy()
    g["loss_amount"]=g["predicted_lgd"]*g["ead_at_default"]
    out=g.groupby("customer_id",as_index=False).agg(
        facility_ead=("ead_at_default","sum"),
        modelled_loss=("loss_amount","sum"),
        facilities=("facility_id","count"),
    )
    out["modelled_lgd"]=out["modelled_loss"]/out["facility_ead"].clip(lower=1)
    return out


def save_model(model,path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,path)


def load_model(path):
    return joblib.load(path)
