# V2 Recovery Architecture Freeze — 2026-09-22

> **Historical checkpoint — superseded by the reviewed current methodology in README.md and FINAL_PROJECT_RELEASE_2026-09-22.md. Values and implementation details below are retained only as development history and must not be treated as the current release.**

## Purpose

This checkpoint freezes the revised synthetic collateral/LGD architecture after the root-cause review of ECL coverage. It replaces the earlier assumption that collateral is broadly generated as a high multiple of facilities.

## Frozen architecture

1. EAD is determined from product mechanics.
2. Collateral type is generated independently as Unsecured, Cash, Mortgage or Other.
3. Nominal collateral coverage is generated conditional on collateral type.
4. Recognized collateral is capped at EAD.
5. Synthetic recovery haircuts are:
   - Cash: 0% haircut / 100% recognition.
   - Mortgage: 20% haircut / 80% recognition.
   - Other: 35% haircut / 65% recognition.
   - Unsecured: no collateral recognition.
6. Residual EAD is treated as unsecured.
7. Borrower LGD is the unsecured loss severity applied to residual unsecured EAD relative to total EAD.
8. Stage 1 uses forward-looking 12-month PD × LGD × EAD.
9. Stage 2 uses probability-weighted lifetime PD × LGD × EAD.
10. Stage 3 remains a direct workout cash-shortfall calculation.

## Synthetic portfolio assumptions

Collateral-type probabilities are 35% Unsecured, 10% Cash, 35% Mortgage and 20% Other. Type-specific nominal coverage distributions and unsecured-LGD dispersion are synthetic demonstration assumptions.

These assumptions are not IFRS 9 prescribed percentages, regulatory collateral haircuts, official forecasts, or empirically calibrated recovery parameters. Production use would require collateral eligibility rules, legal enforceability, seniority, valuation frequency, realization costs/timing, cure/workout data and empirical LGD calibration.

## Governance

The recovery architecture was changed because the prior collateral DGP structurally over-collateralised the synthetic portfolio. The revised assumptions were defined from credit-risk mechanics rather than selected to hit a target ECL/EAD ratio. After validation, these assumptions are frozen. Further changes require a documented methodology reason or empirical recovery evidence; Stage 2 ECL coverage itself is not a tuning target.

## Validation snapshot

On the 3,000-borrower holdout produced by the revised DGP:
- portfolio mean LGD: approximately 33.58%;
- Stage 1 ECL/EAD: approximately 1.04%;
- Stage 2 ECL/EAD: approximately 9.29%;
- Stage 3 ECL/EAD: approximately 58.82%;
- total staged ECL: approximately EUR 45.81m.

Collateral-type mean LGDs are approximately 10.0% Cash, 11.7% Mortgage, 34.6% Other and 62.5% Unsecured. These are model outputs from the synthetic assumptions, not externally validated benchmarks.
