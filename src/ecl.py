import pandas as pd

def calculate_ecl(df, pd_col="predicted_pd", lgd_col="lgd", ead_col="ead"):
    out=df.copy()
    out["ecl_12m"]=out[pd_col]*out[lgd_col]*out[ead_col]
    out["stage"] = pd.cut(
        out[pd_col], bins=[-1,.03,.15,1], labels=["Stage 1","Stage 2","Stage 3"]
    )
    out["lifetime_ecl"]=out["ecl_12m"] * out["stage"].map(
        {"Stage 1":1.0,"Stage 2":2.5,"Stage 3":4.0}
    ).astype(float)
    return out
