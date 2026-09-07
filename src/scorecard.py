import numpy as np
import pandas as pd

def pd_to_score(pd_value, base_score=600, base_odds=20, pdo=50):
    pd_value=np.clip(pd_value,1e-6,1-1e-6)
    odds=(1-pd_value)/pd_value
    return base_score + pdo*np.log2(odds/base_odds)

def risk_band(pd_value):
    if pd_value < .03: return "Low"
    if pd_value < .08: return "Moderate"
    if pd_value < .15: return "High"
    return "Very High"

def add_score(df,pd_col="predicted_pd"):
    out=df.copy()
    out["credit_score"]=pd_to_score(out[pd_col])
    out["risk_band"]=out[pd_col].apply(risk_band)
    return out
