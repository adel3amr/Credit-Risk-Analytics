# V2 Final Validation — 2026-09-22

## Decision
V2 is frozen for manual review. No further tuning of the synthetic DGP, governed PD specification, EWS threshold, staging rules, or macro sensitivities should be made from holdout results.

The governed borrower PD remains the unweighted Logistic Regression using current financial and current behavioural variables. Trajectory remains a separate EWS / monitoring layer.

## Why trajectory was not promoted into core PD
The holdout information-set experiment shows an AUC increase from 0.7673 for Financial + Current Behavior to 0.7643 after adding trajectory. The paired bootstrap mean difference is -0.0030 with a 95% percentile interval of [-0.0134, 0.0070]. The final audited run therefore provides no evidence of incremental trajectory discrimination beyond current behaviour.

This is not treated as independent evidence for model expansion because the frozen synthetic default DGP explicitly contains utilization_6m_change (coefficient 1.20) and months_above_80_utilization (coefficient 0.08). The observed trajectory uplift is therefore partly expected by construction. avg_utilization_6m and limit_breach_count are correlated monitoring summaries rather than direct DGP default terms.

Accordingly, the result is retained as a transparent methodology finding, not used to optimize the governed PD.

## Governed holdout baseline
- Holdout borrowers: 3,000
- Observed 12M default rate: 3.33%
- Logistic Regression AUC: 0.7673
- Gini: 0.5346
- Mean PIT-oriented PD: 3.33%
- Stage 1: 2,760 borrowers
- Stage 2: 231 borrowers
- Stage 3: 9 borrowers
- Holdout EAD: approximately EUR 2.394bn

## Forward-looking ECL overlay
Illustrative synthetic macro assumptions produce:
- upside mean PD: 2.84%
- baseline mean PD: 3.33%
- downside mean PD: 4.82%
- probability-weighted forward-looking mean PD: 3.53%
- PIT 12M diagnostic ECL: approximately EUR 25.97m
- forward-looking 12M diagnostic ECL: approximately EUR 27.53m
- forward-looking staged ECL: approximately EUR 37.75m

Macro variables and log-odds sensitivities are fixed synthetic assumptions, not official forecasts and not empirically estimated elasticities.

## Auditability
The borrower audit trace is a required 3,000-row holdout output. Independent artifact review confirmed zero scenario-ordering violations, a strictly inverse PD-to-score ranking, no zero-EAD borrowers, and accounting identities within rounding tolerance. Required columns fail closed if absent. CI now checks:
1. EAD = loan EAD + OVD EAD + trade EAD.
2. PIT PD = governed predicted PD.
3. Baseline scenario PD = PIT PD.
4. 12M ECL = forward-looking PD × LGD × EAD.
5. Stage 1 ECL = 12M ECL.
6. Stage 2 ECL = weighted lifetime PD × LGD × EAD.
7. Stage 3 ECL = LGD × EAD.
8. Stage 1 does not contain 30+ DPD.
9. Current credit-impaired borrowers are Stage 3.

## Known limitations
This remains an educational synthetic portfolio, not a production model. It has no true origination/reference PD for a full IFRS 9 SICR test; no calibrated macro satellite model; no discounted cash-shortfall engine; no facility-level lifetime EAD term structure; aggregate borrower-level LGD; synthetic trade CCFs; and one borrower-level contractual term across mixed facilities.

The macro scenario table is illustrative rather than jurisdiction- and forecast-horizon-specific. This is intentional and should remain explicit unless the project is later converted into a separately sourced real-world scenario exercise.

## Manual review gate
Do not merge solely because CI is green. Before merge, manually inspect the generated raw portfolio, behavioural history, borrower audit trace, macro diagnostics, validation tables, and representative borrowers across risk bands and stages. Trace selected rows from raw inputs through PD, score, EWS, EAD/LGD, stage, and ECL.

PR #1 remains the V2 review workspace until that manual review is complete.
