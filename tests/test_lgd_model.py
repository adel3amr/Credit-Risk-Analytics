import numpy as np
import pandas as pd

from src.lgd_model import aggregate_borrower_lgd, lgd_validation_summary


def test_borrower_lgd_is_ead_weighted():
    f = pd.DataFrame({
        "customer_id":["A","A","B"],
        "facility_id":["A1","A2","B1"],
        "ead_at_default":[100.0,300.0,200.0],
        "predicted_lgd":[0.20,0.60,0.40],
    })
    out=aggregate_borrower_lgd(f).set_index("customer_id")
    assert np.isclose(out.loc["A","modelled_lgd"],0.50)
    assert np.isclose(out.loc["B","modelled_lgd"],0.40)


def test_lgd_validation_reports_calibration():
    y=np.array([0.2,0.4,0.6])
    p=np.array([0.25,0.35,0.55])
    s=lgd_validation_summary(y,p,np.array([1,2,3]))
    assert {"MAE","RMSE","Mean_Error_Bias","EAD_Weighted_MAE","EAD_Weighted_RMSE","EAD_Weighted_Mean_Error_Bias"}.issubset(s)
    assert np.isclose(s["Mean_Error_Bias"], np.mean(p-y))
    assert np.isclose(s["Calibration_in_the_large"], y.mean()-p.mean())
    assert np.isclose(s["Calibration_in_the_large"], -s["Mean_Error_Bias"])
