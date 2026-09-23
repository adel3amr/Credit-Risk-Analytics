# V5 change control

Release: **Credit Risk Analytics & IFRS 9 Decisioning System — V5**.
Reviewed baselines: V4 `4f87d21`; remote V5 `33c60ee`. Prior local work from `90b0aef`/`2abc84a` is included. V4 additions after the V5 fork were benchmark execution comments; no V4 feature was removed.

| Classification | Change | Reason / evidence |
| --- | --- | --- |
| BUG FIX | Reject invalid stages, duplicate/orphan facilities and non-finite/out-of-range ECL inputs | Prevent silent Stage 1 fallback, double counting and NaN totals. Missing maturity retains the 12-month default. Valid results unchanged. |
| BUG FIX | Literal borrower search | Input such as `[` previously raised a regex error. |
| BUG FIX | Normalize display-only mixed-value tables to text | Prevent Streamlit Arrow serialization fallback when numeric signals and risk labels share a column. |
| CODE ENHANCEMENT | One-command build and tested direct dependency pins | Fail-fast execution order and consistent paths. pandas minimum 2.2 matches existing `include_groups` use. |
| UI/UX ENHANCEMENT | V5 identity, facility ECL trace, LGD bias/tail/support/legacy tables and release checks | Exposes calculations and limitations; permissions unchanged. |
| VALIDATION ENHANCEMENT | Common-cohort challengers and realized-loss thresholds | Same facilities for paired comparison; all 60/75/90/97% cuts reported. |
| VALIDATION ENHANCEMENT | Recovery, split, feature, staging, EAD and ECL checks | Independent arithmetic with explicit rounding tolerances. |
| VALIDATION ENHANCEMENT | Reapplied legacy proxy diagnostic | Exact old formula, fixed synthetic residual seed 20260923; no fitting or promotion. |
| VALIDATION ENHANCEMENT | Regression and dashboard tests | Invalid input, leakage, 9-month boundary, five roles and filter paths. |
| VALIDATION ENHANCEMENT | V5 workflow triggers and retained artifacts | Previous configuration did not directly trigger V5. |
| DOCUMENTATION | README, report, decision record and limitations | Removes stale no-macro and lifetime-multiplier descriptions. |
| DATA ENHANCEMENT | No training/holdout distribution changes | Severe-loss support measured; small synthetic fixtures exercise edge cases only. |
| METHODOLOGICAL CHANGE | **None implemented** | PD/LGD structures, predictors, seeds, staging, 9-month policy, EAD, ECL and champion unchanged. |

The build produces 30 release checks, 27 unit/regression tests and the dashboard suite. Workflows use Python 3.12 and the tested direct dependency set. Production identity/storage, genuine bank-data validation and statistical limitations remain outside this synthetic release.
