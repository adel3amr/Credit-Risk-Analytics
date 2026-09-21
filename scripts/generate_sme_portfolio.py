"""Generate a reproducible synthetic SME lending portfolio.

The generator is deliberately transparent: borrower characteristics create a latent
12-month through-the-cycle risk signal, which is calibrated to a portfolio default
rate suitable for a mixed performing SME book. It is educational synthetic data,
not an estimate of any real bank's portfolio.
"""
from pathlib import Path
import numpy as np
import pandas as pd

N = 12_000
SEED = 42
TARGET_DEFAULT_RATE = 0.035

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "sme_credit_portfolio.csv"


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def calibrate_intercept(linear_predictor, target_rate):
    lo, hi = -15.0, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if sigmoid(linear_predictor + mid).mean() > target_rate:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    rng = np.random.default_rng(SEED)
    n = N

    industries = np.array(["Manufacturing", "Retail", "Services", "Construction",
                           "Transport", "Hospitality", "Technology"])
    industry = rng.choice(industries, n, p=[.18, .20, .24, .12, .10, .08, .08])

    years_in_business = np.clip(np.rint(rng.gamma(2.8, 3.2, n)), 1, 35).astype(int)
    annual_revenue = np.exp(rng.normal(np.log(3_000_000), .85, n))
    ebitda_margin = np.clip(rng.normal(.135, .065, n), -.08, .38)
    leverage_ratio = np.clip(rng.lognormal(np.log(2.0), .42, n), .15, 7.5)
    current_ratio = np.clip(rng.lognormal(np.log(1.45), .35, n), .35, 4.0)
    cash_flow = annual_revenue * np.clip(ebitda_margin + rng.normal(.015, .04, n), -.12, .32)

    loan_amount = np.clip(annual_revenue * rng.uniform(.06, .38, n), 25_000, 5_000_000)
    loan_term_months = rng.choice([12, 24, 36, 48, 60], n, p=[.15, .23, .30, .17, .15])
    debt_to_income = np.clip(
        .12 + .075 * leverage_ratio + rng.normal(.08, .10, n), .03, .90
    )
    credit_utilization = np.clip(
        rng.beta(3.0, 2.7, n) + .035 * (leverage_ratio - 2.0), .03, .99
    )

    # Actual synthetic 6M behavioural history. A borrower-specific deterioration
    # shock moves current utilization away from its six-month-ago level; the
    # shock is generated before, and independently of, the future default draw.
    deterioration_shock = rng.normal(
        .015 * (leverage_ratio - 2.0) - .020 * (current_ratio - 1.25),
        .09, n
    )
    utilization_6m_ago = np.clip(credit_utilization - deterioration_shock, .02, .99)
    utilization_6m_change = credit_utilization - utilization_6m_ago
    avg_utilization_6m = np.clip(
        (credit_utilization + utilization_6m_ago) / 2 + rng.normal(0, .025, n),
        .02, .99
    )
    months_above_80_utilization = np.clip(
        np.rint(6 * np.clip((avg_utilization_6m - .60) / .30, 0, 1)
                + rng.normal(0, .65, n)), 0, 6
    ).astype(int)
    limit_breach_count = np.clip(
        rng.poisson(np.clip((credit_utilization - .80) / .15, 0, 1) * 1.4),
        0, 5
    ).astype(int)

    # Arrears are uncommon in a predominantly performing portfolio.
    arrears_propensity = sigmoid(
        -4.0 + 2.0 * credit_utilization + .30 * (leverage_ratio - 2)
        - 1.0 * (current_ratio - 1.2)
    )
    delinquencies_12m = np.clip(
        rng.poisson(.08 + 1.15 * arrears_propensity), 0, 5
    ).astype(int)
    previous_defaults = rng.binomial(
        1, np.clip(.006 + .035 * arrears_propensity + .010 * (delinquencies_12m > 1), 0, .12)
    )
    has_dpd = rng.random(n) < np.clip(.035 + .32 * arrears_propensity, .02, .35)
    days_past_due = np.where(
        has_dpd,
        np.clip(np.rint(rng.gamma(1.5, 13, n)), 1, 120),
        0,
    ).astype(int)

    collateral_ratio = np.clip(rng.lognormal(np.log(1.25), .42, n), .25, 3.0)
    collateral_value = loan_amount * collateral_ratio
    number_of_accounts = np.clip(rng.poisson(2.2, n) + 1, 1, 10)
    interest_rate = np.clip(
        .045 + .025 * credit_utilization + .008 * leverage_ratio
        + .006 * delinquencies_12m + rng.normal(0, .008, n),
        .035, .18,
    )

    # EAD is current funded exposure; LGD falls as collateral coverage improves.
    ead = loan_amount * rng.uniform(.72, 1.00, n)
    collateral_coverage = collateral_value / np.maximum(ead, 1)
    lgd = np.clip(
        .62 - .22 * np.minimum(collateral_coverage, 2.0)
        + .06 * (industry == "Hospitality") + rng.normal(0, .07, n),
        .12, .75,
    )

    # Latent 12M default risk. Coefficients encode plausible directions only.
    lp = (
        .55 * (leverage_ratio - 2.0)
        - 2.2 * (ebitda_margin - .12)
        - .70 * (current_ratio - 1.25)
        + 1.55 * (credit_utilization - .55)
        + 1.20 * utilization_6m_change
        + .08 * months_above_80_utilization
        + .55 * delinquencies_12m
        + 1.00 * previous_defaults
        + .018 * days_past_due
        + .55 * (debt_to_income - .30)
        - .018 * np.minimum(years_in_business, 15)
        - .30 * np.minimum(collateral_coverage - 1.0, 1.0)
        + .20 * (industry == "Construction")
        + .18 * (industry == "Hospitality")
    )
    intercept = calibrate_intercept(lp, TARGET_DEFAULT_RATE)
    pd_true = np.clip(sigmoid(lp + intercept), .001, .65)
    # Reporting-date credit impairment is distinct from the future 12M outcome.
    # 90+ DPD is the primary observable backstop; a small additional severe-distress
    # component represents other current credit-impaired events in the synthetic book.
    severe_distress_prob = np.clip(
        .002 + .020 * previous_defaults + .012 * (delinquencies_12m >= 2)
        + .010 * (credit_utilization >= .90), 0, .10
    )
    current_credit_impaired = (
        (days_past_due >= 90) | (rng.random(n) < severe_distress_prob)
    ).astype(int)

    default = rng.binomial(1, pd_true)

    df = pd.DataFrame({
        "customer_id": [f"SME{i:05d}" for i in range(1, n + 1)],
        "industry": industry,
        "annual_revenue": annual_revenue.round(2),
        "ebitda_margin": ebitda_margin.round(4),
        "current_ratio": current_ratio.round(4),
        "leverage_ratio": leverage_ratio.round(4),
        "cash_flow": cash_flow.round(2),
        "loan_amount": loan_amount.round(2),
        "loan_term_months": loan_term_months,
        "interest_rate": interest_rate.round(4),
        "debt_to_income": debt_to_income.round(4),
        "credit_utilization": credit_utilization.round(4),
        "utilization_6m_ago": utilization_6m_ago.round(4),
        "utilization_6m_change": utilization_6m_change.round(4),
        "avg_utilization_6m": avg_utilization_6m.round(4),
        "months_above_80_utilization": months_above_80_utilization,
        "limit_breach_count": limit_breach_count,
        "number_of_accounts": number_of_accounts,
        "delinquencies_12m": delinquencies_12m,
        "previous_defaults": previous_defaults,
        "collateral_value": collateral_value.round(2),
        "days_past_due": days_past_due,
        "years_in_business": years_in_business,
        "ead": ead.round(2),
        "lgd": lgd.round(4),
        "current_credit_impaired": current_credit_impaired,
        "default": default,
        "pd_true": pd_true.round(6),
    })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df):,} borrowers to {OUT}")
    print(f"Observed default rate: {df.default.mean():.4%}")
    print(f"Mean latent PD: {df.pd_true.mean():.4%}")
    print(f"Mean LGD: {df.lgd.mean():.4%}")
    print(f"Total EAD: {df.ead.sum():,.0f}")


if __name__ == "__main__":
    main()
