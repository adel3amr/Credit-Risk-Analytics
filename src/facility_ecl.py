"""Facility-level ECL calculation using borrower PD/stage and facility LGD/EAD/maturity."""
import numpy as np
import pandas as pd


def calculate_facility_ecl(borrowers, facilities):
    required_b = {"customer_id","stage","forward_looking_pd_12m"}
    required_f = {"customer_id","facility_id","ead_at_default","predicted_lgd","remaining_months"}
    mb = required_b.difference(borrowers.columns)
    mf = required_f.difference(facilities.columns)
    if mb:
        raise ValueError(f"Missing borrower ECL fields: {sorted(mb)}")
    if mf:
        raise ValueError(f"Missing facility ECL fields: {sorted(mf)}")

    b = borrowers[["customer_id","stage","forward_looking_pd_12m"]].copy()
    f = facilities.merge(b,on="customer_id",how="left",validate="many_to_one")
    if f["stage"].isna().any():
        raise ValueError("Missing borrower stage for one or more facilities")

    pd12=f["forward_looking_pd_12m"].clip(0,1).astype(float)
    lgd=f["predicted_lgd"].clip(0,1).astype(float)
    ead=f["ead_at_default"].clip(lower=0).astype(float)
    years=np.maximum(f["remaining_months"].fillna(12).astype(float)/12.0,0.0)

    f["facility_pd_12m"]=pd12
    f["facility_lifetime_pd"]=(1-np.power(1-pd12,years)).clip(0,1)
    f["facility_ecl_12m"]=pd12*lgd*ead

    s1=f["stage"].eq("Stage 1")
    s2=f["stage"].eq("Stage 2")
    s3=f["stage"].eq("Stage 3")
    f["facility_ecl"]=f["facility_ecl_12m"]
    f.loc[s2,"facility_ecl"]=(f["facility_lifetime_pd"]*lgd*ead)[s2]
    f.loc[s3,"facility_ecl"]=(lgd*ead)[s3]

    return f


def aggregate_facility_ecl(facilities):
    g=facilities.groupby("customer_id",as_index=False).agg(
        facility_ead=("ead_at_default","sum"),
        ecl_12m_facility=("facility_ecl_12m","sum"),
        ecl_facility=("facility_ecl","sum"),
    )
    weighted=facilities.assign(
        _lp=facilities["facility_lifetime_pd"]*facilities["ead_at_default"]
    ).groupby("customer_id",as_index=False).agg(
        _lp_sum=("_lp","sum"),
        _ead=("ead_at_default","sum"),
    )
    weighted["facility_weighted_lifetime_pd"]=weighted["_lp_sum"]/weighted["_ead"].clip(lower=1)
    return g.merge(
        weighted[["customer_id","facility_weighted_lifetime_pd"]],
        on="customer_id",how="left",validate="one_to_one"
    )
