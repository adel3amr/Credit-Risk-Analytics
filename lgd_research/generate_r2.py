"""Standalone economic recovery simulation for research; never used by V5.

At default, only feature columns listed in DEPLOYABLE exist. Every recovery,
cost, cure, resolution and shock column is future information and oracle-only.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PRODUCTS = ["Term Loan", "OVD", "Import LC", "Performance Guarantee", "Financial Guarantee"]
INDUSTRIES = ["Manufacturing", "Retail", "Services", "Construction", "Transport", "Hospitality", "Technology"]
DEPLOYABLE = ["ead_at_default", "collateral_coverage", "guarantee_coverage", "leverage_at_default",
              "current_ratio_at_default", "management_quality", "product_type", "industry",
              "collateral_type", "lien_rank", "security_quality", "guarantor_strength", "downturn_at_default"]
BUCKETS = np.array([1, 6, 12, 24, 36, 60])


def generate(n, seed, vintage, stress="ordinary"):
    rng = np.random.default_rng(seed)
    product = rng.choice(PRODUCTS, n, p=[.42, .25, .12, .13, .08])
    industry = rng.choice(INDUSTRIES, n, p=[.18, .20, .24, .12, .10, .08, .08])
    collateral = rng.choice(["Unsecured", "Cash", "Mortgage", "Other"], n, p=[.36, .10, .34, .20])
    ead = np.clip(rng.lognormal(np.log(350_000), .95, n), 20_000, 8_000_000)
    leverage = np.clip(rng.lognormal(np.log(2.8), .48, n), .3, 9)
    liquidity = np.clip(rng.lognormal(np.log(1.05), .4, n), .25, 3.5)
    management = np.digitize(rng.normal(0, 1, n), [-1, -.3, .3, 1]) + 1
    downturn = rng.binomial(1, .22, n)
    if stress == "combined":
        downturn[:] = 1
    coverage = np.zeros(n)
    for category, median, sigma, low, high in [("Cash", .9, .22, .25, 1.4),
                                                ("Mortgage", 1.05, .38, .2, 2),
                                                ("Other", .65, .42, .1, 1.5)]:
        mask = collateral == category
        coverage[mask] = np.clip(rng.lognormal(np.log(median), sigma, mask.sum()), low, high)
    lien = np.where(collateral == "Unsecured", "Unsecured", rng.choice(["First", "Second"], n, p=[.78, .22]))
    # Legal/valuation quality known at default, but imperfectly measured.
    security_quality = np.where(collateral == "Unsecured", 0.,
                                np.clip(rng.beta(4, 2, n) - .10 * downturn, .05, 1))
    trade = np.isin(product, PRODUCTS[2:])
    guarantee = np.where(trade, rng.choice([0., .2, .35, .55, .8], n, p=[.2, .2, .3, .25, .05]),
                         rng.choice([0., .15, .35], n, p=[.8, .15, .05]))
    strength = np.where(guarantee > 0, np.clip(rng.beta(3, 2, n) - .12 * downturn, .02, 1), 0.)

    # Future realization shocks are deliberately *not* part of DEPLOYABLE.
    market_shock = rng.normal(0, .16, n)
    bank_shock = rng.normal(0, .16, n)
    collection_shock = rng.normal(0, .10, n)
    cure_probability = 1 / (1 + np.exp(-(-1.5 + .6*(liquidity-1) - .22*(leverage-2.5)
                                           + .20*(management-3) - .55*downturn)))
    cure = rng.binomial(1, cure_probability)
    liquidation = np.select([collateral == "Cash", collateral == "Mortgage", collateral == "Other"],
                            [.97, .68, .44], default=0.)
    lien_factor = np.where(lien == "Second", .72, 1.)
    security_stress = .78 if stress in ("collateral", "combined") else 1.
    guarantee_stress = .65 if stress in ("guarantee", "combined") else 1.
    recovery_stress = .75 if stress in ("recovery", "combined") else 1.
    collateral_cash = np.minimum(ead, ead*coverage*liquidation*lien_factor*
                                 (.55+.6*security_quality)*np.clip(1+market_shock-.20*downturn, .15, 1.5)*security_stress)
    guarantee_cash = np.minimum(np.maximum(ead-collateral_cash, 0), ead*guarantee*
                                (.25+.65*strength)*np.clip(1+bank_shock-.2*downturn, 0, 1.3)*guarantee_stress)
    residual = np.maximum(ead-collateral_cash-guarantee_cash, 0)
    unsecured_rate = np.clip(.30-.027*(leverage-2.8)+.045*(liquidity-1)+.02*(management-3)
                             -.10*downturn+collection_shock, 0, .75)*recovery_stress
    unsecured_cash = residual * unsecured_rate
    cure_cash = np.where(cure == 1, np.maximum(ead*(.90+.04*rng.normal(size=n))
                                                 -collateral_cash-guarantee_cash-unsecured_cash, 0), 0)
    cure_cash = np.minimum(cure_cash, np.maximum(ead-collateral_cash-guarantee_cash-unsecured_cash, 0))
    gross = collateral_cash + guarantee_cash + unsecured_cash + cure_cash
    delay_stress = 14 if stress in ("timing", "combined") else 0
    months = np.clip(np.rint(8+17*(collateral == "Mortgage")+8*(lien == "Second")
                             +9*(1-cure)+13*downturn+delay_stress+rng.gamma(2, 5, n)), 1, 60)
    months = np.where(collateral == "Cash", rng.integers(1, 5, n)+4*downturn, months)
    extra_cost = .04 if stress in ("cost", "combined") else 0
    costs = ead*np.clip(.012+.014*(collateral == "Mortgage")+.012*(lien == "Second")
                        +.025*downturn+extra_cost+rng.normal(0, .009, n), .003, .16)
    weights = np.exp(-np.abs(BUCKETS[None, :]-months[:, None])/9)
    weights /= weights.sum(axis=1, keepdims=True)
    # Components are already subject to the remaining exposure cap; timing and
    # costs are explicit before PV discounting, with no direct LGD assignment.
    net = gross[:, None]*weights
    net[:, 0] -= costs*(collateral == "Cash")
    net[:, 2] -= costs*(collateral != "Cash")
    rate = np.clip(rng.normal(.07, .012, n), .035, .12)
    pv = np.sum(net/(1+rate[:, None])**(BUCKETS[None, :]/12), axis=1)
    out = pd.DataFrame(dict(vintage=vintage, facility_id=[f"{vintage}-{i:06d}" for i in range(n)],
                            product_type=product, industry=industry, ead_at_default=ead,
                            collateral_type=collateral, collateral_coverage=coverage, lien_rank=lien,
                            guarantee_coverage=guarantee, leverage_at_default=leverage,
                            current_ratio_at_default=liquidity, management_quality=management,
                            security_quality=security_quality, guarantor_strength=strength,
                            downturn_at_default=downturn, cure_flag=cure,
                            collateral_recovery=collateral_cash, guarantee_recovery=guarantee_cash,
                            unsecured_recovery=unsecured_cash, cure_recovery=cure_cash,
                            months_to_resolution=months, workout_cost=costs, discount_rate=rate,
                            pv_net_recovery=pv, economic_lgd=np.clip(1-pv/ead, 0, 1),
                            market_realization_shock=market_shock, guarantee_realization_shock=bank_shock,
                            collection_realization_shock=collection_shock, stress_scenario=stress))
    for i, bucket in enumerate(BUCKETS):
        out[f"recovery_cf_{bucket}m"] = net[:, i]
    assert out.economic_lgd.between(0, 1).all()
    assert (out[["collateral_recovery", "guarantee_recovery", "unsecured_recovery", "cure_recovery"]]
            .sum(axis=1) <= out.ead_at_default + 1e-6).all()
    assert not set(DEPLOYABLE) & set(["cure_flag", "pv_net_recovery", "economic_lgd",
                                      "months_to_resolution", "workout_cost"])
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--vintage", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stress", choices=["ordinary", "collateral", "guarantee", "recovery", "timing", "cost", "combined"], default="ordinary")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.n, args.seed, args.vintage, args.stress)
    df.to_csv(args.output, index=False)
    print(args.output, len(df), df.economic_lgd.mean(), (df.economic_lgd > .75).sum())
