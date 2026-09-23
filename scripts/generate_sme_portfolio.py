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
    # Independent deterministic RNG streams prevent unrelated component edits from
    # silently changing every downstream synthetic variable.
    seed_sequence = np.random.SeedSequence(SEED)
    (
        rng_borrower, rng_facility, rng_behavior, rng_credit,
        rng_recovery, rng_default, rng_qualitative, rng_maturity,
    ) = [np.random.default_rng(s) for s in seed_sequence.spawn(8)]
    rng = rng_borrower
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

    # Independent qualitative underwriting information. These fields are not
    # reconstructed from the financial ratios or account behaviour below; they
    # represent genuinely additional synthetic information that a credit officer
    # could obtain through management meetings, KYC, governance review and market
    # due diligence.
    q = rng_qualitative
    latent_management = q.normal(0, 1, n)
    latent_governance = 0.35 * latent_management + q.normal(0, .94, n)
    latent_reporting = 0.25 * latent_governance + q.normal(0, .97, n)
    latent_market = q.normal(0, 1, n)
    latent_support = q.normal(0, 1, n)

    def ordinal_1_5(x):
        return np.digitize(x, [-1.0, -0.3, 0.3, 1.0]) + 1

    management_quality = ordinal_1_5(latent_management).astype(int)
    governance_quality = ordinal_1_5(latent_governance).astype(int)
    financial_reporting_quality = ordinal_1_5(latent_reporting).astype(int)
    market_position = ordinal_1_5(latent_market).astype(int)
    sponsor_support = ordinal_1_5(latent_support).astype(int)
    customer_concentration = np.clip(q.beta(2.0, 4.5, n), .03, .90)
    supplier_concentration = np.clip(q.beta(1.8, 5.0, n), .02, .85)
    key_person_dependency = q.binomial(1, .22, n).astype(int)
    audit_quality = q.choice([1, 2, 3], n, p=[.30, .50, .20]).astype(int)

    rng = rng_facility
    # Three product buckets per borrower: term loans, overdraft (OVD), and trade.
    # Values below are facility amounts/limits. A borrower can use more than one product.
    has_loan = rng.random(n) < .72
    has_ovd = rng.random(n) < .58
    has_trade = rng.random(n) < .36
    # Ensure every borrower has at least one credit product.
    none = ~(has_loan | has_ovd | has_trade)
    has_loan[none] = True

    # Term-loan approved limit and current outstanding are separated so portfolio
    # utilization has a genuine denominator. The draw ratio is a broad synthetic
    # facility assumption and is not fitted to default, ECL or staging outcomes.
    loan_limit = np.where(
        has_loan, np.clip(annual_revenue * rng.uniform(.04, .28, n), 25_000, 4_000_000), 0.0
    )
    loan_draw_ratio = np.where(has_loan, rng.uniform(.55, 1.00, n), 0.0)
    loans = loan_limit * loan_draw_ratio
    ovd = np.where(
        has_ovd, np.clip(annual_revenue * rng.uniform(.02, .16, n), 15_000, 2_000_000), 0.0
    )
    trade = np.where(
        has_trade, np.clip(annual_revenue * rng.uniform(.02, .22, n), 20_000, 3_000_000), 0.0
    )
    loan_amount = loans + ovd + trade
    direct_limit = loan_limit + ovd
    indirect_limit = trade
    total_credit_limit = direct_limit + indirect_limit
    loan_term_months = rng.choice([12, 24, 36, 48, 60], n, p=[.15, .23, .30, .17, .15])
    # Reporting-date remaining maturity is generated independently of credit risk.
    loan_age_months = np.floor(
        rng_maturity.random(n) * np.maximum(loan_term_months, 1)
    ).astype(int)
    loan_remaining_months = np.maximum(loan_term_months - loan_age_months, 1)
    loan_age_months = np.where(has_loan, loan_age_months, 0)
    loan_remaining_months = np.where(has_loan, loan_remaining_months, 0)
    ovd_remaining_months = np.where(has_ovd, 12, 0)
    debt_to_income = np.clip(
        .12 + .075 * leverage_ratio + rng.normal(.08, .10, n), .03, .90
    )
    rng = rng_behavior
    # 36-month behavioural history generated strictly forward from M-35 to M0.
    # Reporting-date utilization is therefore an OUTPUT of the history process,
    # rather than an anchor used to reconstruct the past. This avoids conditioning
    # historical EWS trajectories on a value that was not yet observed.
    history_months = 36
    month_labels = np.arange(-(history_months - 1), 1)

    # Borrower-specific long-run utilization level reflects leverage/liquidity.
    # Parameters are transparent synthetic assumptions, not fitted to target
    # Stage-2 shares, AUC, or ECL.
    long_run_util = np.clip(
        rng.beta(3.0, 2.7, n) + .035 * (leverage_ratio - 2.0)
        - .020 * (current_ratio - 1.45), .03, .97
    )
    borrower_drift = rng.normal(
        .0015 * (leverage_ratio - 2.0) - .0015 * (current_ratio - 1.25),
        .0045, n
    )
    util_hist = np.empty((n, history_months))
    util_hist[:, 0] = np.clip(long_run_util + rng.normal(0, .10, n), .02, .99)
    for m in range(1, history_months):
        common_shock = rng.normal(0, .012)
        idio = rng.normal(0, .035, n)
        mean_reversion = .10 * (long_run_util - util_hist[:, m - 1])
        util_hist[:, m] = np.clip(
            util_hist[:, m - 1] + borrower_drift + mean_reversion + common_shock + idio,
            .02, .99
        )

    # Current utilization is the final observed month of the chronological panel.
    credit_utilization = util_hist[:, -1].copy()

    # Drawn/utilized facility amounts are reporting-date measures and therefore must
    # be derived only after current utilization has been observed at M0.
    direct_drawn = loans + ovd * credit_utilization
    total_utilized_amount = direct_drawn + trade

    # Monthly limit-breach process: high utilization raises breach likelihood, but
    # breaches remain stochastic rather than deterministic.
    breach_lambda = np.clip((util_hist - .78) / .18, 0, 1) * 1.10
    breach_hist = np.clip(rng.poisson(breach_lambda), 0, 5).astype(int)

    # Current EWS features are derived only from observations available through M0.
    utilization_6m_ago = util_hist[:, -7]
    utilization_6m_change = credit_utilization - utilization_6m_ago
    avg_utilization_6m = util_hist[:, -6:].mean(axis=1)
    months_above_80_utilization = (util_hist[:, -6:] >= .80).sum(axis=1).astype(int)
    limit_breach_count = breach_hist[:, -6:].sum(axis=1).astype(int)

    # Reconstruct EWS status at each month with six months of lookback, then measure
    # the consecutive deteriorating spell ending at the reporting date.
    ews_hist = np.zeros((n, history_months), dtype=bool)
    for m in range(6, history_months):
        change_6m = util_hist[:, m] - util_hist[:, m - 6]
        window_start = m - 5
        avg_6m = util_hist[:, window_start:m + 1].mean(axis=1)
        months_high_6m = (util_hist[:, window_start:m + 1] >= .80).sum(axis=1)
        breaches_6m = breach_hist[:, window_start:m + 1].sum(axis=1)
        signals = (
            (change_6m >= .10).astype(int)
            + ((avg_6m >= .80) | (months_high_6m >= 3)).astype(int)
            + (breaches_6m >= 1).astype(int)
        )
        ews_hist[:, m] = signals >= 2

    consecutive_ews_months = np.zeros(n, dtype=int)
    for i in range(n):
        if ews_hist[i, -1]:
            run = 0
            for m in range(history_months - 1, 5, -1):
                if ews_hist[i, m]:
                    run += 1
                else:
                    break
            consecutive_ews_months[i] = run

    # Long-format behavioural panel for auditability and later SQL/time-series work.
    history_df = pd.DataFrame({
        "customer_id": np.repeat([f"SME{i:05d}" for i in range(1, n + 1)], history_months),
        "month_from_reporting": np.tile(month_labels, n),
        "credit_utilization": util_hist.reshape(-1).round(4),
        "limit_breach_count_month": breach_hist.reshape(-1),
        "ews_deteriorating": ews_hist.reshape(-1).astype(int),
    })
    rng = rng_credit
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

    rng = rng_recovery
    # Collateral is generated after EAD because security should be expressed against
    # the exposure it protects, not assumed as a multiple of total committed facilities.
    number_of_accounts = np.clip(rng.poisson(2.2, n) + 1, 1, 10)
    interest_rate = np.clip(
        .045 + .025 * credit_utilization + .008 * leverage_ratio
        + .006 * delinquencies_12m + rng_credit.normal(0, .008, n),
        .035, .18,
    )

    # Product-level EAD mechanics.
    # Internal project policy:
    # - Term-loan EAD = 100% of the current withdrawn/outstanding amount.
    # - OVD EAD = 100% of the total approved limit.
    # In this synthetic schema, 'loans' represents the current term-loan
    # outstanding amount and 'ovd' represents the total OVD limit.
    # Trade CCFs remain transparent synthetic assumptions for methodology
    # demonstration, not regulatory prescriptions.
    loan_ead = loans.copy()
    ovd_drawn = ovd * credit_utilization
    ovd_ead = ovd.copy()

    trade_types = np.array(["Import LC", "Performance Guarantee", "Financial Guarantee"])
    trade_type = rng_facility.choice(trade_types, n, p=[.45, .35, .20])
    trade_ccf_map = {"Import LC": .20, "Performance Guarantee": .50, "Financial Guarantee": 1.00}
    trade_ccf = np.array([trade_ccf_map[x] for x in trade_type])
    trade_ccf = np.where(has_trade, trade_ccf, 0.0)
    trade_type = np.where(has_trade, trade_type, "None")
    trade_ead = trade * trade_ccf
    trade_remaining_months = np.array([
        {"Import LC":6, "Performance Guarantee":18, "Financial Guarantee":24, "None":0}[x]
        for x in trade_type
    ], dtype=int)

    ead = loan_ead + ovd_ead + trade_ead
    # Collateral DGP: generate security type first, then nominal coverage conditional
    # on that type. This creates genuinely unsecured borrowers and avoids assuming that
    # nearly every SME is over-collateralised. Probabilities and coverage ranges are
    # transparent synthetic portfolio assumptions, not empirical or regulatory rates.
    collateral_types = np.array(["Unsecured", "Cash", "Mortgage", "Other"])
    collateral_type = rng_recovery.choice(collateral_types, n, p=[.35, .10, .35, .20])

    collateral_coverage = np.zeros(n)
    cash_mask = collateral_type == "Cash"
    mortgage_mask = collateral_type == "Mortgage"
    other_mask = collateral_type == "Other"

    collateral_coverage[cash_mask] = np.clip(
        rng_recovery.lognormal(np.log(.85), .20, cash_mask.sum()), .40, 1.25
    )
    collateral_coverage[mortgage_mask] = np.clip(
        rng_recovery.lognormal(np.log(1.05), .35, mortgage_mask.sum()), .35, 1.80
    )
    collateral_coverage[other_mask] = np.clip(
        rng_recovery.lognormal(np.log(.65), .40, other_mask.sum()), .15, 1.30
    )
    collateral_value = ead * collateral_coverage

    # Synthetic internal recognition policy (not IFRS 9 prescribed haircuts):
    # cash is recognized at 100%; mortgage receives a 20% haircut; other collateral
    # receives a more conservative 35% haircut; unsecured borrowers have no collateral.
    collateral_haircut = np.select(
        [cash_mask, mortgage_mask, other_mask],
        [0.00, 0.20, 0.35],
        default=1.00,
    )
    recognized_collateral = np.minimum(
        collateral_value * (1.0 - collateral_haircut), ead
    )
    recognized_collateral_coverage = recognized_collateral / np.maximum(ead, 1)
    unsecured_ead = np.maximum(ead - recognized_collateral, 0.0)

    # LGD is driven by loss severity on residual unsecured exposure. Collateral does
    # not reduce PD or create a provision floor; it changes expected recovery.
    unsecured_lgd = np.clip(
        .62 + .06 * (industry == "Hospitality") + rng_recovery.normal(0, .07, n),
        .35, .85,
    )
    lgd = np.clip(
        unsecured_lgd * unsecured_ead / np.maximum(ead, 1),
        0.0,
        .85,
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
        # Qualitative underwriting information is deliberately independent of
        # the quantitative features. Coefficients are fixed synthetic assumptions,
        # not tuned to the holdout or to a target AUC.
        - .12 * (management_quality - 3)
        - .10 * (governance_quality - 3)
        - .08 * (financial_reporting_quality - 3)
        - .08 * (market_position - 3)
        - .08 * (sponsor_support - 3)
        + .35 * (customer_concentration - .30)
        + .20 * (supplier_concentration - .25)
        + .18 * key_person_dependency
        - .07 * (audit_quality - 2)
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
        (days_past_due >= 90) | (rng_credit.random(n) < severe_distress_prob)
    ).astype(int)

    # Write-off is a distinct reporting-date resolution status, not merely a
    # high-DPD bucket. This allows internal Rating 10 to represent write-off cases.
    write_off_probability = np.where(days_past_due >= 120, .35, .06)
    write_off_flag = (
        (current_credit_impaired == 1)
        & (rng_credit.random(n) < write_off_probability)
    ).astype(int)

    default = rng_default.binomial(1, pd_true)

    df = pd.DataFrame({
        "customer_id": [f"SME{i:05d}" for i in range(1, n + 1)],
        "industry": industry,
        "management_quality": management_quality,
        "governance_quality": governance_quality,
        "financial_reporting_quality": financial_reporting_quality,
        "market_position": market_position,
        "sponsor_support": sponsor_support,
        "customer_concentration": customer_concentration.round(4),
        "supplier_concentration": supplier_concentration.round(4),
        "key_person_dependency": key_person_dependency,
        "audit_quality": audit_quality,
        "annual_revenue": annual_revenue.round(2),
        "ebitda_margin": ebitda_margin.round(4),
        "current_ratio": current_ratio.round(4),
        "leverage_ratio": leverage_ratio.round(4),
        "cash_flow": cash_flow.round(2),
        "loan_amount": loan_amount.round(2),
        "loan_limit": loan_limit.round(2),
        "loan_draw_ratio": loan_draw_ratio.round(4),
        "loans": loans.round(2),
        "ovd": ovd.round(2),
        "trade": trade.round(2),
        "direct_limit": direct_limit.round(2),
        "direct_drawn": direct_drawn.round(2),
        "indirect_limit": indirect_limit.round(2),
        "total_credit_limit": total_credit_limit.round(2),
        "total_utilized_amount": total_utilized_amount.round(2),
        "loan_ead": loan_ead.round(2),
        "ovd_ead": ovd_ead.round(2),
        "trade_type": trade_type,
        "trade_ccf": trade_ccf.round(2),
        "trade_ead": trade_ead.round(2),
        "trade_remaining_months": trade_remaining_months,
        "loan_term_months": loan_term_months,
        "loan_age_months": loan_age_months,
        "loan_remaining_months": loan_remaining_months,
        "ovd_remaining_months": ovd_remaining_months,
        "interest_rate": interest_rate.round(4),
        "debt_to_income": debt_to_income.round(4),
        "credit_utilization": credit_utilization.round(4),
        "utilization_6m_ago": utilization_6m_ago.round(4),
        "utilization_6m_change": utilization_6m_change.round(4),
        "avg_utilization_6m": avg_utilization_6m.round(4),
        "months_above_80_utilization": months_above_80_utilization,
        "limit_breach_count": limit_breach_count,
        "consecutive_ews_months": consecutive_ews_months,
        "number_of_accounts": number_of_accounts,
        "delinquencies_12m": delinquencies_12m,
        "previous_defaults": previous_defaults,
        "collateral_value": collateral_value.round(2),
        "collateral_coverage": collateral_coverage.round(4),
        "collateral_type": collateral_type,
        "collateral_haircut": collateral_haircut,
        "recognized_collateral": recognized_collateral.round(2),
        "recognized_collateral_coverage": recognized_collateral_coverage.round(4),
        "unsecured_ead": unsecured_ead.round(2),
        "unsecured_lgd": unsecured_lgd.round(4),
        "days_past_due": days_past_due,
        "years_in_business": years_in_business,
        "ead": ead.round(2),
        "lgd": lgd.round(4),
        "current_credit_impaired": current_credit_impaired,
        "write_off_flag": write_off_flag,
        "default": default,
        "pd_true": pd_true.round(6),
    })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    history_out = ROOT / "data" / "raw" / "sme_behavioral_history_36m.csv"
    history_df.to_csv(history_out, index=False)
    print(f"Saved {len(df):,} borrowers to {OUT}")
    print(f"Saved {len(history_df):,} monthly observations to {history_out}")
    print(f"Observed default rate: {df.default.mean():.4%}")
    print(f"Mean latent PD: {df.pd_true.mean():.4%}")
    print(f"Mean LGD: {df.lgd.mean():.4%}")
    print(f"Total EAD: {df.ead.sum():,.0f}")


if __name__ == "__main__":
    main()
