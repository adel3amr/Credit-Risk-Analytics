# Credit Risk Analytics: whole-project review

**24 September 2026 · review branch `review/independent-system-validation` · reference V5 `0dfe4c8`**

## Executive decision

The repository is a functioning, reproducible **synthetic demonstration** of a borrower-to-facility credit workflow. It is **blocked for live bank provisioning**. The decisive evidence is absent institution-specific default and recovery data, no independent bank model approval, and material forecast error among loans selected *after* severe loss is realized. The new machine-readable gate (`python scripts/assess_bank_readiness.py --purpose bank`) exits with code 2. The demo remains runnable. Neither a clean CI run nor a near-zero portfolio LGD bias authorizes bank deployment.

This review found and addressed a genuine **input-support defect**: 79.20% of the live facilities have guarantee coverage zero, whereas only 0.0125% of the original resolved-workout sample do. A distinct synthetic development vintage now supplies exactly the same approved guarantee inputs as the reporting-date facility mapper. An entirely different seed was reserved for a separate validation vintage. The *same governed Gradient Boosting model specification* was refit for a diagnostic comparison, without promoting this refit to production. On that separate 8,000-case synthetic vintage, whole-vintage bias moved from +1.24 to −0.15 percentage points, but bias on the 1,618 **realized LGDs above 75%** went from −13.13 to −14.66 points. Consequently the input problem can be fixed in synthetic data; the severe-outcome problem **cannot honestly be declared solved**. Further changes to model structure, forecasts, overlays or ECL would require explicit methodological approval under the frozen mandate.

## Entire repository: version lineage and what actually changed

The available Git history contains 299 commits and 26 remote branches. Fifteen selected source snapshots were reconstructed in isolated checkouts, including separate experiment branches; every listed snapshot executed successfully under the present environment. They do not constitute replay of every commit, original historical Python runtime or historical hosted CI. The machine-readable chronology is in `evidence/commit_history.csv`, `evidence/phases.csv`, `evidence/historical_reproduction.csv`, `evidence/historical_data_profiles.csv`, and `PROJECT_TIMELINE.md`.

| Period / reference | Delivery and verified sample | Remaining issue |
|---|---|---|
| Initial `4d91d1e` | Borrower PD/ECL prototype; 12k records, 10.54% generated defaults, holdout AUC .71341 | PD cutoff staging, scaled lifetime loss, incompatible population versus later releases. |
| V2 `29ede62` | Seeded 12k SME portfolio, 36-month EWS, fixed logistic PD, macro scenarios, internal 9-month rule; AUC .76729; ECL 37.00m | Simplified borrower LGD and immature source checks in intermediate commits. |
| V3 `a78bfe9` and main `b93a459` | Streamlit workbench, collateral, ratings, facility limits and trade CCF; main AUC .75991; ECL 38.15m | Role picker is a demonstration; borrower-based recovery persists. |
| Research branches, PRs 18–21 | PCA, WOE, bootstrap and stress studies reproduced independently | No challenger is the governed V5 model. |
| Unmerged PR 22 `cfce69a` | Broader remediation branch replays | Its ECL 30.58m is not an adopted release. |
| Code-only PR 23 `a90db85` | Actual V4 base | Maintains approved pre-facility rules. |
| Early V4 `c85cdab` | 8k separate resolved workouts, facility LGD and ECL; holdout LGD MAE 12.12 pp | Severe-loss underprediction 15.46 pp in 308 realized >75% cases. |
| Final V4 `4f87d21` | Improved cash-workout generator; LGD MAE 11.40 pp, RMSE 16.58 pp | Severe-loss underprediction still 15.59 pp in 327 realized >75% cases. Different targets prevent direct tail attribution. |
| Frozen V5 `0dfe4c8` | Common-cohort validation, code guards, dashboard and release checks; EAD 2.09191bn, ECL 45.26597m | Numerical PD/LGD/ECL equal final V4 in clean reproduction; no empirical bank validation. |
| Current review | Independent arithmetic, policy boundary tests, new future-seed guarantee-support experiment and operating gate | Severe-outcome error remains; no methodological or ECL change approved. |

## Component audit and end-to-end interpretation

**Data and provenance.** Reporting portfolio: 12,000 generated SMEs, 432,000 behavioral months, 3,000 holdout borrowers and 102 holdout defaults. Separate default/workout data: 8,000 resolved facilities split 6,000 development and 2,000 held out. The later support experiment has 12,000 additional development cases and 8,000 additional validation cases with a different seed. Both are synthetic draws from declared rules, **not time-based vintages of observed bank customers**. Generator IDs repeat across draws and must always be scoped by dataset; no row from the separate validation draw enters either fit. The original generated history is preserved by default when running its generator without flags.

**PD.** The approved logistic model uses reporting-date borrower features, then fixed synthetic macro odds shifts generate scenario and forward PD. Independent validation gives AUC .759455, Gini .518911, KS .408497, Brier .030003, log loss .128562, predicted mean .034388 and realized default rate .034000. The record does not validate actual live-borrower calibration, origination-to-current migration or empirically forecast scenarios. PCA/WOE/hybrid experiments are diagnostics, not promoted alternatives.

**SICR, watchlist and rating.** Distinct concepts were traced from 36-month conduct to EWS signal count, current deterioration and consecutive months; the internal nine-month persistence is a source-defined Stage 2 trigger. Stage 3 is impairment or DPD ≥90; other Stage 2 triggers are DPD ≥30, multiple delinquencies, high utilization with positive DPD or prior default with the policy PD condition. Nine months is an *internal policy*, not a claimed external requirement. Independent reruns found zero mismatches to the source-defined stage and EWS policy on the 3,000-borrower validation population. Role views do not implement authentication.

**LGD.** The frozen model predicts discounted net recovery shortfall using facility EAD, collateral coverage/type, guarantee coverage, lien, product, industry, leverage, liquidity and management quality. Cure, future recovery amounts/costs and resolution timing form targets, never forecast features. Original 2,000-facility holdout: mean realized LGD .454306, predicted .451254, MAE .113965, RMSE .165798, mean error −.003052. The 327 outcomes >75% have −.155928 mean error; 89 >90% have −.204291. Top 200 by **forecast** have −.025344 mean error, a prospective risk group. Cure outcomes have +.274488 mean error, and non-cure −.056310. The two opposite errors help cancel in the full population. Extreme post-resolution selection cannot be turned into a live scoring rule without observing the future. Training includes 980 >75% losses and 102 ≥97% losses; sample scarcity alone does not explain everything. Cash-flow recomputation, rounding, split integrity, absence of outcome features, feature propagation and clipping were checked in `RESEARCH_REPORT.md` and evidence files. A pro-rata collateral coverage ratio across facilities does **not** multiply nominal collateral: the facility EAD weights sum to the borrower EAD.

**New support experiment.** The original training history essentially omits zero-guarantee exposures, but 4,096 of 5,172 live facilities have guarantee coverage zero. `scripts/generate_lgd_workout_history.py --guarantee-profile live` creates separately named datasets using the *already existing* 0/.20/.35/.55 live inputs and the unchanged workout-recovery arithmetic. `validation_review/tools/assess_lgd_support.py` compares a model trained on the original 6,000 development cases to the same model specification trained on those 6,000 plus 12,000 support cases. It evaluates both on the original untouched 2,000 and a separately seeded 8,000. On the original holdout, the corrected fit improves severe bias from −15.59 to −15.03 pp, but on the separate draw it worsens severe bias from −13.13 to −14.66 pp. On the latter, overall MAE changes 12.24 to 12.31 pp; RMSE 18.15 to 17.97 pp. These mixed, already-inspected results **do not support a new champion**. File: `outputs/lgd_independent_vintage_assessment.csv`.

**EAD/ECL.** Term EAD equals drawn outstanding; OVD EAD is the approved limit; trade EAD equals face amount times the internally configured CCF. Stage 1 uses forward PD12 × forecast LGD × EAD, Stage 2 uses `1 − (1 − PD12)^(remaining months/12)` × LGD × EAD, and Stage 3 uses LGD × EAD. Individual facilities, borrower sums and portfolio sums reconcile within stored rounding. The 3,000-borrower sample contains 5,172 facilities and EAD 2,091,914,076.05; ECL 45,265,972.05. This shows code fidelity to project rules, not independent assessment of accounting-policy suitability. `evidence/independent_facility_traces.csv` contains manually reproducible facility examples.

**Interface and software.** The five demo role views and underlying generated-file paths were exercised with the existing AppTest harness. The validator now shows the independent support comparison and an explicit bank-use blocker. Batch outputs are CSV and the joblib fit; no production data service, immutable model registry, real identity provider or operational approval workflow exists. The CI trigger has been extended to all pushed branches and pull requests; the new audit runs in CI and asserts that bank purpose stays blocked while demonstration execution succeeds.

## Root cause, acceptable use and action

The strongest demonstrated defect is *training/live guarantee-feature support mismatch*. The corrected synthetic development data makes the live input combinations observable in development and tests without altering LGD factors or recovery math. A separate validation draw shows this correction is **insufficient** to remove the severe realized-outcome error. Large errors conditional on an eventual outcome can coexist with reasonable mean forecasts: stochastic cures, recoveries and collateral realization create future uncertainty that is absent from the pre-workout feature set. This does **not** excuse systematic bias in forecast-selected risk cohorts; those cohorts and EAD-weighted aggregates must be monitored on actual future default cohorts. No synthetic experiment establishes that the model is suitably calibrated to any bank.

**Bank-use decision: blocked.** A bank cannot responsibly use these synthetic ECL outputs as booked allowances. The software now makes that status executable and visible. A bank may use the project as a training or analytical prototype while collecting representative recovery cash flows, actual facility-level security/guarantee terms and multi-period outcomes; independent model validation and governance must decide any subsequent deployment. The IFRS Foundation describes ECL as unbiased, probability-weighted and based on reasonable supportable information, while the Basel Committee describes sound credit-risk practices and governance; these external standards are not substitutes for this project's approved internal policy. Primary sources: <https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ifrs9.html>, <https://www.bis.org/publications/201512-guidelines-guidance-credit-risk-and-accounting-expected-credit-losses>.

## Classified changes and controlled recommendations

| Classification | Current change | Effect |
|---|---|---|
| DATA ENHANCEMENT | Additional seeded live-input-support development and validation draws | Exposes the original missing zero-guarantee region; separate populations retained. |
| CODE ENHANCEMENT | Optional generator seed, size and destination; bank-purpose readiness command | Original default generated history and governed model unchanged; bank use fails closed. |
| VALIDATION ENHANCEMENT | Fixed-specification paired test across original and new validation draws; CI execution and boundary tests | Documents mixed results without tuning to a repeatedly viewed holdout. |
| UI/UX ENHANCEMENT | Validator bank-use alert and transparent support table | Error visible beside LGD diagnostics. |
| DOCUMENTATION | Whole-repository disposition, README and limitations | Explains evidence and refusal to claim a tail cure. |
| METHODOLOGICAL CHANGE | **None implemented** | Forecast uplift, new cure classifier, asymmetric loss, portfolio overlay and revised staging/ECL remain unapproved. |

The following **future methodological recommendations are not implemented**: bank-approved recovery-data collection and representative time-split tests; assessing additional pre-workout cure/security-quality inputs; assessing probability-weighted recovery scenarios and asymmetric high-severity risk; governance-defined acceptance thresholds and controlled overlays with ECL impact assessment. Approval must precede any replacement of the frozen model, policy or allowance calculation.

## Reproduction and evidence

From a clean checkout with Python 3.12:

1. Install `requirements-v5.txt` and run `python scripts/run_v5.py`.
2. Run the two live-profile generator commands in `.github/workflows/validate-hybrid-v2.yml`.
3. Run `python validation_review/tools/assess_lgd_support.py`, `python -m pytest -q` and `python scripts/test_dashboard.py`.
4. Run `python scripts/assess_bank_readiness.py --purpose bank` (expected exit 2).

Calculation evidence appears in `outputs/v5_release_checks.csv`, `outputs/lgd_independent_vintage_assessment.csv`, `evidence/independent_reconciliation.json`, the historical CSVs, `FINDINGS_REGISTER.csv` and the longer `RESEARCH_REPORT.md`. CI and test success demonstrate reproducibility and consistency **only on generated data**.
