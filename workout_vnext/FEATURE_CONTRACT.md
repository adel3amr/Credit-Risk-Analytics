# WN-1 feature contract

All features are available in the synthetic ledger at observation time; institutional availability has NOT been validated. Future cure, ultimate LGD, future cashflows, latent capacity and resolution duration are prohibited predictors. Development/validation/final coverage is in `results/feature_population.csv`; domains are enforced by `contracts.check`. No silent imputation.

| Feature | Definition | Unit | Source | Range/categories |
|---|---|---|---|---|
| predefault_pd | Last dated predefault PD proxy; current default PD is separately one | numeric ratio / indicator | credit_snapshot | (0, 1) |
| predefault_rating | Dated predefault internal rating proxy | rank | credit_snapshot | (1, 7) |
| rating_migration | Dated reported change in rating; not future migration | numeric ratio / indicator | credit_snapshot | (None, None) |
| financial_strength | Observed standardized synthetic financial-strength proxy | standardized value | credit_snapshot | (None, None) |
| previous_defaults | Known prior-default indicator | numeric ratio / indicator | credit_snapshot | (0, None) |
| utilization | Last dated credit utilization | numeric ratio / indicator | credit_snapshot | (0, 1) |
| delinquency | Last dated days past due | days | credit_snapshot | (0, None) |
| age | Months elapsed since default | months | default_event | (0, None) |
| months_since_last_recovery | Age minus latest observed recovery month; age if none | months | recovery_transaction | (0, None) |
| recovered_ratio | Observed cumulative cash recovery / default exposure | numeric ratio / indicator | recovery_transaction | (0, 1) |
| collateral_ratio | Last recorded appraised value / remaining EAD; not depleted security availability | numeric ratio / indicator | collateral_valuation | (0, None) |
| haircut | Last known valuation haircut fraction | numeric ratio / indicator | collateral_valuation | (0, 1) |
| lien | Known lien rank | rank | collateral_valuation | (1, 2) |
| enforcement | Observed enforcement initiation indicator | numeric ratio / indicator | collateral_enforcement | (0, 1) |
| guarantee_ratio | Minimum of one and eligible nominal guarantee / remaining EAD; not payout-depleted | numeric ratio / indicator | guarantee | (0, 1) |
| guarantor_quality | Known synthetic quality fraction | numeric ratio / indicator | guarantee | (0, 1) |
| enforceability | Known enforceability indicator | numeric ratio / indicator | guarantee | (0, 1) |
| claim | Observed claim submission indicator | numeric ratio / indicator | guarantee_claim | (0, 1) |
| restructured | Observed restructuring agreement indicator | numeric ratio / indicator | restructure_event | (0, 1) |
| cost_ratio | Observed accumulated costs / default exposure | numeric ratio / indicator | workout_cost | (0, None) |
| growth | Contemporaneous annual output-growth assumption | percent | macro_snapshot | (None, None) |
| unemployment | Contemporaneous unemployment assumption | percent | macro_snapshot | (0, None) |
| price_change | Contemporaneous collateral-price change fraction | numeric ratio / indicator | macro_snapshot | (None, None) |
| rate | Fixed annual facility discount/accrual rate | numeric ratio / indicator | facility | (0, None) |
| mi_ratio | Cumulative postdefault suspended memorandum interest / remaining EAD | numeric ratio / indicator | interest_accrual | (0, None) |
| ead | Principal plus predefault interest minus cash recoveries already received; excludes suspended interest and writeoffs | EUR | facility | (0, None) |
| industry | Known industry | category | borrower/facility/collateral | ['Manufacturing', 'Retail', 'Services', 'Construction'] |
| product | Known product | category | borrower/facility/collateral | ['Term Loan', 'OVD'] |
| collateral_type | Known collateral_type | category | borrower/facility/collateral | ['none', 'cash', 'property', 'other'] |

Machine-readable `feature_contract.json` also records model usage, availability, observation time, lineage and sensitivity. Zero is a real no-event/no-support value, not missingness. Ratios over one are allowed for collateral and costs where denominator economics imply them. Unknown categories and nonfinite values reject. `None` bounds mean no finite bound, not permission for NaN.
