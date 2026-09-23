# Credit Risk Analytics & IFRS 9 Decisioning System — V5
## Forensic reconstruction and independent implementation validation

**Review date:** 23 September 2026. **Frozen reference:** `0dfe4c883a8314704394c49fa096dfb45525096c`. **Review branch:** `review/independent-system-validation`. **Disposition:** Implementation validated on synthetic data; high-loss conditional LGD limitation remains open. No approved methodology changed.

### Abstract

We reconstructed 299 commits, inspected 26 remote branches and pull requests, executed 15 representative historical snapshots from clean archives and rebuilt frozen V5. Separate code recalculated holdout PD, workout LGD, EWS and stage assignments, scenario PDs, workout recovery targets, and facility/borrower ECL. Frozen V5 passed 27 tests, 30 release checks and a dashboard smoke test across five role views. On 2,000 resolved-workout holdouts, governed facility LGD MAE is 0.113965, RMSE 0.165798 and mean prediction-minus-realization error −0.003052. For 327 **realized** LGDs >75%, bias is −0.155928; for the top 200 **predicted** LGDs it is −0.025344. Selection on the realized outcome magnifies negative errors even for a conditional-mean forecast. Cure uncertainty and stochastic recovery indicate a material data/information-set limitation; no observed accounting or mapping defect warrants an unapproved model change. This is a synthetic decisioning demonstration, not evidence of live-bank performance or certification of accounting compliance.

## 1. Scope and independence

Repository history and executable source, rather than earlier narrative claims, are primary evidence. We compared V4, V5, main, abandoned remediation and separate experiments. `git archive` extracted each checkpoint into an isolated directory to avoid stale generated outputs. `tools/independent_recalculation.py` imports no production validation/model function: it uses direct arrays, ranked AUC, raw cash flows and independently transcribed approved policy identities. This is **computational** independence, not an institutionally independent audit. Historical source and the frozen production commit remain untouched. Synthetic samples do not constitute real-world validation.

Evidence inventory: `evidence/commit_history.csv` (all 299 commits), `branches.csv`, `pull_requests.json`, `phases.csv`, `capability_matrix.csv`, `test_inventory.csv`, `historical_reproduction.csv`, `frozen_source_hashes.csv`, independent calculations and the charts. Historical execution covers selected representative checkpoints, whereas commit/branch inventory covers available repository history. Unmerged branches are not approved V5 features. Metrics across changed generators, populations and rules are not like-for-like improvements.

## 2. Historical reconstruction

| Phase and source | Implementation shift | Assessment |
|---|---|---|
| Initial `4d91d1e` | Supplied portfolio, balanced classifiers, best holdout-AUC model selection, PD-cutoff stages, 2.5×/4× ECL multipliers | Reproduced; initial default share 10.54%. Staging semantics and target mix differ from V5. |
| V2 `29ede62` | Seeded borrower generator, fixed logistic PD, current-state staging, macro scenarios, 36-month EWS and internal nine-month persistence | Reproduced. Earlier `4833e84`/`03c1db0` had removed substantive CI invariants; tests were subsequently restored. |
| V3 `a78bfe9` through main `b93a459` | Streamlit governance workbench, operational ratings, collateral recognition, product limits and CCF | Reproduced representative snapshots. Main predates V4/V5; demo identities do not constitute authentication. |
| PRs 18–21 | PCA, 2,000 paired bootstrap resamples, five-bin training-only WOE scorecard with 0.5 smoothing, stress sensitivity | Separate branches; executable experiments reproduced; none is a governed V5 component. |
| PR 22 `cfce69a` | Broader generator/feature/ECL remediation | Closed unmerged; its numbers cannot be ascribed to V5. |
| PR 23 `a90db85` | Code-only remediation from main | Actual V4 base, rather than PR 22. |
| Early V4 `c85cdab` to V4 `4f87d21` | Independent synthetic qualitative inputs; 8,000 resolved workouts, facility LGD/ECL, recovery diagnostics/challengers | Early holdout LGD MAE 0.12123, final V4 0.11396; not proof of generalization. |
| V5 `33c60ee` to `0dfe4c8` | Train/holdout stability, common-cohort tail checks, realized-tail and legacy-proxy diagnostics, release and interface checks | Governed PD/LGD metrics and EAD/ECL totals equal final V4 in clean reruns. V5 primarily improves observability and release integrity. |

![Historical diagnostic snapshots](figures/history.png)

Selected historical runs appear in `evidence/historical_reproduction.csv`. V2 AUC 0.76729, main AUC 0.75991 and V5 AUC 0.75946 reflect changed data and rules, not a controlled decline. The initial prototype's AUC 0.71341 applies to a different default mix. Final V4 and V5 share the same seeded 3,000-borrower holdout, 102 future defaults, EAD 2,091,914,076.05 and ECL 45,265,972.05 synthetic currency units.

## 3. Frozen methodology and information flow

The generator creates 12,000 borrowers and 36 monthly behavior observations for each; a distinct 8,000-facility resolved-default history supplies discounted workout LGD targets. PD development/holdout splitting is stratified 75%/25% with seed 42. LGD uses 75%/25% facility-ID-disjoint split, seed 42. After holdout evaluation, the fixed LGD specification is refit on all workouts for current-portfolio scoring. The current portfolio has **no realized workout outcomes**: its LGD forecasts cannot be assigned MAE.

Governed borrower logistic PD is a reporting-date, PIT-oriented 12-month forecast; fixed synthetic macro scenario shifts act on odds, then weighted scenario PDs form forward PD. Facility lifetime PD equals `1 − (1 − forward PD12)^(remaining months/12)`. Loan EAD equals drawn loan, OVD EAD equals approved limit and trade EAD applies the instrument CCF. The governed LGD is fixed gradient boosting on pre-workout borrower/facility features; borrower LGD display is facility EAD-weighted. Stage 1 ECL is forward PD12 × LGD × EAD, Stage 2 replaces PD12 with facility lifetime PD, and Stage 3 uses 1 × LGD × EAD. Borrower ECL is a facility sum. Historical borrower-term ECL and a direct-collateral Stage 3 shortfall remain diagnostics, not governed outputs.

Monitoring watchlist/direction, accounting proxy stages, default outcomes, risk bands and ratings are different concepts. EWS deterioration enters Stage 2 only after **nine consecutive deteriorating months** under the established internal policy. Stage 3 is current impairment or DPD ≥90. Other Stage 2 triggers are DPD ≥30, two or more delinquencies, utilization ≥85% with positive DPD, or prior default and current PD ≥5%. The nine-month rule is not presented as an external regulatory rule.

## 4. LGD integrity, calibration and high-loss tail

Raw economic LGD is clipped `1 − PV(net recovery cash flows)/EAD`; six dated buckets use the recorded discount rate. Independent reconstruction max difference is 0.00001554 in LGD fraction, attributable to stored rounding. Cash, mortgage, other and unsecured collateral; guarantee, lien, cost, recovery timing, cure and write-off cases occur. The training and holdout samples have 980 and 327 LGDs >75%, 102 and 25 ≥97%, and 1,059 and 322 cures respectively. Severe cases are **not absent**, although only 25 extreme holdout cases constrain precision. Feature names exclude observed outcomes, cash flows and resolution fields. Facility IDs are split-disjoint. Only one raw forecast of 2,000 is outside [0,1] pre-clipping, so clipping cannot explain the widespread tail bias.

| Independent cohort | n | Actual mean | Forecast mean | Bias forecast − actual | MAE | RMSE |
|---|---:|---:|---:|---:|---:|---:|
| All holdout | 2,000 | 45.43% | 45.13% | −0.31 pp | 11.40 pp | 16.58 pp |
| Realized ≤10% | 158 | 5.72% | 18.60% | +12.88 pp | 14.00 pp | 23.87 pp |
| Realized >60% | 652 | 76.28% | 64.02% | −12.27 pp | 12.70 pp | 14.70 pp |
| Realized >75% | 327 | 85.07% | 69.48% | −15.59 pp | 15.62 pp | 17.17 pp |
| Realized ≥90% | 89 | 94.77% | 74.34% | −20.43 pp | 20.43 pp | 21.32 pp |
| Top 10% *predicted* | 200 | 77.77% | 75.24% | −2.53 pp | 17.51 pp | 24.34 pp |

![LGD tail bias](figures/lgd_tail_bias.png)

The outcome-conditioned bias does not alone establish a misspecified conditional expectation. The 322 cures have realized mean 16.14%, predicted 43.59% (bias +27.45 pp); 1,678 non-cures have realized 51.05%, predicted 45.42% (−5.63 pp). Cure/no-cure and final recovery are unknown pre-workout and cannot be inserted as training features without leakage. A forecast based on available pre-workout information averages across these outcomes, so selecting severe realized outcomes selects negative residuals. That is an **information-set and stochastic recovery limitation**, not a demonstrated weighting, join or discount-code bug; it leaves a genuine high-loss use-case concern. Unsecured n=716 MAE 16.86 pp, RMSE 22.64 pp, bias −1.25 pp; cash n=192 MAE 3.71 pp, bias +0.77 pp; OVD n=509 bias −1.90 pp.

![LGD decile calibration](figures/lgd_calibration.png)

The highest predicted decile averages 75.24% versus 77.77% actual. The residual distribution shows material two-sided errors obscured by small aggregate bias.

![Holdout residuals](figures/lgd_residuals.png)

The old/simple collateral proxy is **reapplied** to the same resolved-workout holdout using its frozen generator formula and an independent fixed-seed synthetic residual. `outputs/v5_lgd_legacy_holdout_comparison.csv` is thus a diagnostic transfer, **not** historical predictions by an earlier trained version. Its whole-holdout MAE/RMSE/bias are 21.14/25.33/−11.32 pp, compared with the facility model's 11.40/16.58/−0.31 pp; in realized >75% workouts, its bias is −24.91 pp versus −15.59 pp. The facility model captures more of the observed synthetic recovery economics on this paired diagnostic population, but this transfer is not an external comparison. On the current portfolio the proxy has no realized outcome, so it has no honest current-portfolio MAE. Huber, RF, histogram boosting and ridge are fixed-holdout diagnostic challengers, not authorized replacements. Huber MAE 10.42 pp is lower than the champion's 11.40 pp, but RMSE 16.73 pp versus 16.58 pp and mean bias +2.14 pp versus −0.31 pp. A single favorable metric does not change governance.

## 5. Independent PD, EWS, staging, EAD and ECL assessment

Rank-based AUC on 3,000 held-out borrowers is 0.759455; Gini 0.518911; KS 0.408497; Brier 0.0300025; log loss 0.128562. Observed future default is 3.4000% (102 cases) versus mean predicted PD 3.4388%, a +0.0388 percentage point forecast-minus-outcome gap. Values match the saved logistic row to floating-point precision. A finite single-seed synthetic holdout cannot establish real-bank calibration. The logistic champion is fixed by governance and is not chosen by holdout AUC.

Independent reconstruction of three EWS flags from trajectory inputs produces **zero risk-direction mismatches**; independently transcribed stage triggers give **zero stage mismatches** across 3,000 borrowers. Stage counts are 2,769/221/10; operational rating-7/watchlist count is 287, illustrating distinct semantics. Nine-month persistence remains intact. Scenario-weighted forward PD maximum difference is 1.7×10⁻¹⁶. Facility borrower links are unique and complete. Maximum differences: facility lifetime PD 5.5×10⁻¹⁶, facility ECL 3.5×10⁻¹⁰, borrower ECL aggregate 1.2×10⁻¹⁰ and borrower EAD 0.01 synthetic units (source rounding; tolerance 0.02). Portfolio EAD totals 2,091,914,076.05; ECL 45,265,972.05. `evidence/independent_facility_traces.csv` has one complete trace per stage, with IDs, PD, maturity-adjusted PD, LGD, EAD and recomputed ECL.

## 6. Software, reproducibility and evidence quality

`scripts/run_v5.py` sequentially generates raw data, trains LGD, builds PD/ECL and diagnostics and runs release checks. Python 3.12 with declared `requirements-v5.txt` pins was used. Streamlit was initially absent in this workspace, preventing its metadata check; installing the declared dependencies resolved the release run. This was an environmental prerequisite, not an LGD/ECL error. **27/27 pytest tests, 30/30 release checks and five-role/three-filter AppTest dashboard smoke passed**, including literal special-character search and a borrower drill-down. We did not visually inspect every live page in a browser or observe a fresh remote GitHub Actions run; equivalent workflow commands and sources were examined locally.

CI generates data, trains models, runs regression and accounting checks and uses Streamlit AppTest. Its pull-request trigger includes main, code-only and V4 targets but does not explicitly list a PR targeting V5; push does include V5. Production `scripts/validate_v5.py` imports production `validation_summary` and `lgd_validation_summary` despite its independent-check description. Its accounting identities are useful; its metrics are not independent from those shared functions. This review supplies separate formulas. Demo role names and session state are not real authentication or governed approvals. Live data contracts, external drift, multi-vintage stability, operational security and accessibility remain outside demonstrated coverage.

## 7. Findings, change control and limitations

| ID | Classification | Evidence and disposition |
|---|---|---|
| F1 | VALIDATION ENHANCEMENT | Separate PD/LGD/ECL/trigger calculations, charts and fingerprints added on review branch. Frozen model unchanged. |
| F2 | DOCUMENTATION | V4-final and V5-frozen governed metrics/totals coincide. Describe V5 validation hardening accurately. |
| F3 | DATA / VALIDATION LIMITATION | 25 near-total-loss holdouts, one synthetic vintage; no test data contaminated to manufacture metrics. |
| F4 | METHODOLOGICAL CHANGE — NOT IMPLEMENTED | Different cure/recovery distributions or new model structures might address tails; require future separate approval. |
| F5 | CODE ENHANCEMENT — recommendation | Remove duplicate challenger imports and clarify the release script's independence claim. No observed numerical defect. |
| F6 | VALIDATION ENHANCEMENT — recommendation | Add independent oracle and PR-to-V5 CI trigger in future code-only release. |
| F7 | GOVERNANCE LIMITATION | AppTest role selection is demonstration UI, not enforceable access control. |

High-loss underprediction is **quantified and explained but not closed as a performance result**. No approved risk methodology was modified for better scores. Institution-specific data, authorized accounting policy, external validation and production controls are prerequisites for live provisioning. See `KNOWN_LIMITATIONS.md` for risk register and future methodological suggestions that were **not implemented**.

## 8. Reproducibility and references

On a clean Python 3.12 checkout of the frozen hash: `python -m pip install -r requirements-v5.txt`, `python scripts/run_v5.py`, `python -m pytest -q`, `python scripts/test_dashboard.py`. On the separate review branch run `python validation_review/tools/independent_recalculation.py /absolute/path/to/frozen/v5` and `python validation_review/tools/make_figures.py /absolute/path/to/frozen/v5`. The latter read outputs only, never train/tune. `forensic_inventory.py` and `reproduce_history.py` recreate the source inventory and historical sample. See `CONTENT_INSIGHTS.md`, `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, `evidence/` and `figures/` for the complete review package; the root README covers the original application's operation.

External background, not imported into the approved internal rules: IFRS Foundation, [IFRS 9 Financial Instruments](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/) and [IFRS 9 project summary](https://www.ifrs.org/content/dam/ifrs/project/fi-impairment/ifrs-standard/published-documents/project-summary-july-2014.pdf); Basel Committee, [Guidance on credit risk and accounting for expected credit losses](https://www.bis.org/bcbs/publ/d350.htm). The internal nine-month watchlist threshold is not attributed to these sources.
