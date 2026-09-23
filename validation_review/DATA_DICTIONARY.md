# Data dictionary and policy lineage

Detailed generated borrower fields are also documented by frozen `outputs/borrower_audit_trace_dictionary.csv`. This dictionary explains report terms; neither source contains live customer data.

| Term | Level and provenance | Interpretation / caution |
|---|---|---|
| `customer_id` / `facility_id` | Borrower / facility synthetic IDs | One borrower can carry multiple facilities; facility ID is unique for each scored obligation. |
| `default` | Borrower outcome | Synthetic future 12-month default label; never current impairment or predictor for stage. |
| `predicted_pd` | Borrower model output | Governed logistic PIT-oriented 12-month PD; validated only on held-out borrowers. |
| `forward_looking_pd_12m` | Borrower overlay | Probability-weighted scenario PD, with fixed source-defined macro odds shifts. |
| `pd_12m_upside/baseline/downside` | Borrower scenarios | Transparent synthetic assumptions, not official economic forecasts. |
| `risk_direction` / `ews_sicr_flag` | Borrower monitoring | Stable, Watch or Deteriorating; separate from rating and stage. |
| `consecutive_ews_months` | Behavioral history | Consecutive deteriorating periods ending at current reporting month; ≥9 can trigger Stage 2 under internal policy. |
| `risk_band` / `risk_rating` | Borrower categorization | PD band and operational 1–10 rating; rating 7/watchlist differs from accounting stage. |
| `stage` / `sicr_flag` | Borrower accounting proxy | Stage 1/2/3 follows reporting-date source policy; Stage 3 requires impairment or DPD ≥90. |
| `loan_ead`, `ovd_ead`, `trade_ead` | Borrower exposure products | Drawn term loan, approved OVD limit, instrument amount × trade CCF; EAD sum. |
| `ead_at_default` | Facility | Facility exposure allocated from borrower products; one-to-many borrower link. |
| `collateral_coverage`, `collateral_type`, `guarantee_coverage`, `lien_rank` | Pre-workout LGD drivers | Frozen facility model risk drivers; synthetic guarantee mapping differs by instrument. |
| `economic_lgd` | Resolved default facility outcome | `clip(1 − discounted net cash recoveries / historical EAD, 0, 1)`; not observable at scoring. |
| `cure_flag`, `write_off_flag`, `recovery_cf_*`, `pv_net_recovery` | Resolved workout outcomes | Diagnostic and target reconstruction only; do not leak to prediction input. |
| `predicted_lgd` | Facility governed model | Gradient-boosting output clipped [0,1]; 2,000-facility disjoint holdout has actual workout comparator. |
| `modelled_lgd` | Borrower presentation | EAD-weighted facility predicted LGD; not a separate fitted borrower LGD. |
| `lgd_legacy_proxy` | Borrower diagnostic | Earlier collateral formula output; no actual current-portfolio workout available. |
| `facility_lifetime_pd` | Facility derived | Constant annual hazard over remaining contractual months. |
| `facility_ecl` | Facility governed | Stage 1: 12m PD×LGD×EAD; Stage 2: lifetime PD×LGD×EAD; Stage 3: LGD×EAD. |
| `ecl` | Borrower aggregate | Sum of its governed facility ECLs, in synthetic currency units. |

**Bias sign convention:** mean(predicted LGD − realized LGD); negative is underprediction. **AUC population:** governed logistic model's borrower holdout, not all generated borrowers. **LGD population:** resolved-default facility holdout, not active facilities. **Currency:** synthetic unnamed monetary units, never an actual financial statement.
