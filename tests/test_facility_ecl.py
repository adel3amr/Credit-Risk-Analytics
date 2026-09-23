import numpy as np
import pandas as pd

from src.facility_ecl import calculate_facility_ecl, aggregate_facility_ecl


def test_stage2_uses_facility_remaining_maturity():
    borrowers=pd.DataFrame({
        "customer_id":["A"],
        "stage":["Stage 2"],
        "forward_looking_pd_12m":[0.10],
    })
    facilities=pd.DataFrame({
        "customer_id":["A","A"],
        "facility_id":["A1","A2"],
        "ead_at_default":[100.0,100.0],
        "predicted_lgd":[0.50,0.50],
        "remaining_months":[12,24],
    })
    out=calculate_facility_ecl(borrowers,facilities)
    assert out.loc[1,"facility_lifetime_pd"] > out.loc[0,"facility_lifetime_pd"]
    assert out.loc[1,"facility_ecl"] > out.loc[0,"facility_ecl"]


def test_stage3_facility_ecl_is_lgd_times_ead():
    borrowers=pd.DataFrame({
        "customer_id":["A"],
        "stage":["Stage 3"],
        "forward_looking_pd_12m":[0.08],
    })
    facilities=pd.DataFrame({
        "customer_id":["A"],
        "facility_id":["A1"],
        "ead_at_default":[200.0],
        "predicted_lgd":[0.60],
        "remaining_months":[18],
    })
    out=calculate_facility_ecl(borrowers,facilities)
    assert np.isclose(out.loc[0,"facility_ecl"],120.0)


def test_facility_ecl_aggregation_reconciles():
    facilities=pd.DataFrame({
        "customer_id":["A","A"],
        "facility_id":["A1","A2"],
        "ead_at_default":[100.0,300.0],
        "facility_ecl_12m":[5.0,12.0],
        "facility_ecl":[8.0,20.0],
        "facility_lifetime_pd":[0.10,0.20],
    })
    out=aggregate_facility_ecl(facilities).set_index("customer_id")
    assert np.isclose(out.loc["A","facility_ead"],400.0)
    assert np.isclose(out.loc["A","ecl_facility"],28.0)
    assert np.isclose(out.loc["A","facility_weighted_lifetime_pd"],0.175)
