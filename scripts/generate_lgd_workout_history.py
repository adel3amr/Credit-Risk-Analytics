"""Generate a reproducible synthetic historical default/workout dataset.

The dataset represents resolved defaulted facilities and is used to demonstrate a
facility-level workout-LGD model. Recovery outcomes, workout timing and costs are
post-default outcomes and are never used as model inputs.
"""
from pathlib import Path
import numpy as np
import pandas as pd

N = 8_000
SEED = 20260923
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "lgd_workout_history.csv"


def main():
    rng = np.random.default_rng(SEED)
    n = N

    product_type = rng.choice(
        ["Term Loan", "OVD", "Import LC", "Performance Guarantee", "Financial Guarantee"],
        n, p=[.42, .25, .12, .13, .08]
    )
    industry = rng.choice(
        ["Manufacturing","Retail","Services","Construction","Transport","Hospitality","Technology"],
        n, p=[.18,.20,.24,.12,.10,.08,.08]
    )
    ead_at_default = np.exp(rng.normal(np.log(350_000), .95, n))
    ead_at_default = np.clip(ead_at_default, 20_000, 8_000_000)

    collateral_type = rng.choice(
        ["Unsecured","Cash","Mortgage","Other"], n, p=[.36,.10,.34,.20]
    )
    coverage = np.zeros(n)
    coverage[collateral_type=="Cash"] = np.clip(
        rng.lognormal(np.log(.90), .22, (collateral_type=="Cash").sum()), .25, 1.40
    )
    coverage[collateral_type=="Mortgage"] = np.clip(
        rng.lognormal(np.log(1.05), .38, (collateral_type=="Mortgage").sum()), .20, 2.00
    )
    coverage[collateral_type=="Other"] = np.clip(
        rng.lognormal(np.log(.65), .42, (collateral_type=="Other").sum()), .10, 1.50
    )
    collateral_value = ead_at_default * coverage

    lien_rank = np.where(
        collateral_type=="Unsecured", "Unsecured",
        rng.choice(["First","Second"], n, p=[.78,.22])
    )
    guarantee_coverage = np.where(
        np.isin(product_type, ["Import LC","Performance Guarantee","Financial Guarantee"]),
        np.clip(rng.beta(2.2, 3.2, n), 0, 1),
        np.clip(rng.beta(1.0, 12.0, n), 0, .35),
    )

    leverage_at_default = np.clip(rng.lognormal(np.log(2.8), .48, n), .3, 9.0)
    current_ratio_at_default = np.clip(rng.lognormal(np.log(1.05), .40, n), .25, 3.5)
    management_quality = np.digitize(rng.normal(0, 1, n), [-1,-.3,.3,1]) + 1

    # Resolution outcomes are generated from economically plausible recovery drivers.
    # These equations are synthetic assumptions, not empirical bank estimates.
    secured_quality = np.select(
        [collateral_type=="Cash", collateral_type=="Mortgage", collateral_type=="Other"],
        [.995, .70, .45], default=0.0
    )
    lien_factor = np.select([lien_rank=="First", lien_rank=="Second"], [1.0,.72], default=0.0)
    # Cash collateral is operationally distinct from physical collateral: where the\n    # bank has enforceable control, value volatility and liquidation friction should\n    # be much lower. Keep a small residual haircut rather than hard-coding zero LGD.\n    realization_multiplier = np.where(\n        collateral_type=="Cash",\n        np.clip(rng.normal(1.0, .01, n), .97, 1.01),\n        np.clip(rng.normal(1.0, .14, n), .55, 1.25),\n    )\n    collateral_recovery = np.minimum(\n        collateral_value * secured_quality * lien_factor * realization_multiplier,\n        ead_at_default\n    )

    guarantee_recovery = np.minimum(
        ead_at_default * guarantee_coverage
        * np.clip(rng.normal(.72, .16, n), .20, 1.0),
        np.maximum(ead_at_default - collateral_recovery, 0)
    )

    base_unsecured = np.select(
        [
            product_type=="Term Loan", product_type=="OVD", product_type=="Import LC",
            product_type=="Performance Guarantee", product_type=="Financial Guarantee"
        ],
        [.24,.18,.34,.28,.38], default=.22
    )
    unsecured_pool = np.maximum(ead_at_default - collateral_recovery - guarantee_recovery, 0)
    unsecured_rate = np.clip(
        base_unsecured
        - .035 * (leverage_at_default - 2.8)
        + .045 * (current_ratio_at_default - 1.05)
        + .025 * (management_quality - 3)
        + rng.normal(0,.10,n),
        0, .75
    )
    unsecured_recovery = unsecured_pool * unsecured_rate

    cure_logit = (
        -1.6 + .55*(current_ratio_at_default-1.0) - .20*(leverage_at_default-2.5)
        + .18*(management_quality-3) + .35*(collateral_type=="Cash")
    )
    cure_prob = 1/(1+np.exp(-cure_logit))
    cure_flag = rng.binomial(1, cure_prob)
    cure_recovery = np.where(
        cure_flag==1,
        np.maximum(
            ead_at_default * np.clip(rng.normal(.94,.04,n), .78, 1.0)
            - collateral_recovery - guarantee_recovery,
            0
        ),
        0
    )

    gross_recovery = np.minimum(
        collateral_recovery + guarantee_recovery + unsecured_recovery + cure_recovery,
        ead_at_default
    )

    standard_resolution = np.clip(\n        np.rint(\n            9 + 18*(collateral_type=="Mortgage") + 8*(lien_rank=="Second")\n            + 7*(1-cure_flag) + rng.gamma(2.0,5.0,n)\n        ),\n        3, 60\n    ).astype(int)\n    cash_resolution = rng.integers(1, 4, n)\n    months_to_resolution = np.where(collateral_type=="Cash", cash_resolution, standard_resolution)\n    standard_cost_rate = np.clip(\n        .035 + .015*(collateral_type=="Mortgage") + .012*(lien_rank=="Second")\n        + rng.normal(0,.012,n), .01, .12\n    )\n    cash_cost_rate = np.clip(rng.normal(.005, .002, n), .001, .012)\n    workout_cost_rate = np.where(collateral_type=="Cash", cash_cost_rate, standard_cost_rate)
    workout_cost = ead_at_default * workout_cost_rate

    # Allocate recoveries across standard workout time buckets according to resolution speed.
    buckets = np.array([1,6,12,24,36,60])
    weights = np.empty((n, len(buckets)))
    for i, b in enumerate(buckets):
        weights[:, i] = np.exp(-np.abs(b - months_to_resolution) / 10.0)
    weights = weights / weights.sum(axis=1, keepdims=True)
    recovery_cfs = gross_recovery[:,None] * weights

    # Workout costs are treated as negative recovery cash flows. Cash costs are\n    # incurred near-immediately; other workout costs are placed at 12 months.\n    net_cfs = recovery_cfs.copy()\n    cash_mask = collateral_type=="Cash"\n    net_cfs[cash_mask,0] = net_cfs[cash_mask,0] - workout_cost[cash_mask]\n    net_cfs[~cash_mask,2] = net_cfs[~cash_mask,2] - workout_cost[~cash_mask]

    discount_rate = np.clip(rng.normal(.07,.012,n), .035, .12)
    pv_net_recovery = np.zeros(n)
    for i,b in enumerate(buckets):
        pv_net_recovery += net_cfs[:,i] / np.power(1+discount_rate, b/12)

    economic_lgd = np.clip(1 - pv_net_recovery / ead_at_default, 0, 1)
    write_off_flag = (economic_lgd >= .97).astype(int)

    df = pd.DataFrame({
        "facility_id": [f"DFLT{i:06d}" for i in range(1,n+1)],
        "product_type": product_type,
        "industry": industry,
        "ead_at_default": ead_at_default.round(2),
        "collateral_type": collateral_type,
        "collateral_value_at_default": collateral_value.round(2),
        "collateral_coverage": coverage.round(4),
        "lien_rank": lien_rank,
        "guarantee_coverage": guarantee_coverage.round(4),
        "leverage_at_default": leverage_at_default.round(4),
        "current_ratio_at_default": current_ratio_at_default.round(4),
        "management_quality": management_quality.astype(int),
        "cure_flag": cure_flag.astype(int),
        "months_to_resolution": months_to_resolution,
        "workout_cost": workout_cost.round(2),
        "discount_rate": discount_rate.round(5),
        "recovery_cf_1m": net_cfs[:,0].round(2),\n        "recovery_cf_6m": net_cfs[:,1].round(2),\n        "recovery_cf_12m": net_cfs[:,2].round(2),\n        "recovery_cf_24m": net_cfs[:,3].round(2),\n        "recovery_cf_36m": net_cfs[:,4].round(2),\n        "recovery_cf_60m": net_cfs[:,5].round(2),
        "pv_net_recovery": pv_net_recovery.round(2),
        "economic_lgd": economic_lgd.round(6),
        "write_off_flag": write_off_flag,
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT,index=False)
    print(f"Saved {len(df):,} resolved default facilities to {OUT}")
    print(f"Mean economic LGD: {df.economic_lgd.mean():.2%}")
    print(f"Write-off share: {df.write_off_flag.mean():.2%}")


if __name__ == "__main__":
    main()
