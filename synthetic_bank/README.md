# Synthetic bank dataset S1

A versioned, linked dataset for the complete reference platform. It supplements,
and does not overwrite, V5/R2. All records are synthetic. No challenger is active.

## What was rebuilt

Borrowers, financial fields, product exposures and 36-month conduct panels use the
frozen chronological borrower process with new seeds. Facility records share those
borrower IDs. Collateral is allocated from a borrower pool without duplicate pledges.
Third-party guarantee contracts are generated separately from bank-issued trade
products. Security quality, guarantor strength and synthetic sector condition are
recorded before outcomes in every cohort. Defaults lead to facility workouts with
shared borrower cure/recovery shocks, explicit costs and six dated cashflow buckets.
Future targets and recovery records are kept outside scoring inputs.

This is an integrated new dataset, not a claim that every inherited economic
assumption has been redeveloped or validated on institutional data.

| Cohort | Reporting date | Borrowers | Facilities | Workouts |
|---|---|---:|---:|---:|
| Development | 2005-01-01 | 30,000 | 52,098 | 1,933 |
| Selection | 2012-01-01 | 15,000 | 26,130 | 1,055 |
| Final | 2019-01-01 | 15,000 | 26,089 | 1,017 |
| Current | 2026-01-01 | 5,000 | 8,695 | None—future outcomes withheld |

Dates are synthetic illustrations, not historical economic reconstructions.
Seven-year gaps permit 12-month default observation plus 60-month recovery before
the next vintage. Borrowers never cross cohorts. Monthly conduct totals 2,340,000
records. Approximately 80% of all facilities in each cohort have zero guarantee
support. This repairs the source-population discontinuity in S1; it does not fix
the old model's training support or guarantee institutional representativeness.

## Final held-out comparison

All three LGD candidates were fixed before opening final results. Units below are
percentage points. Same final population: 1,017 resolved facilities; 168 above 75% LGD.

| LGD model | MAE | RMSE | Overall bias | Bias for realized LGD >75% |
|---|---:|---:|---:|---:|
| Frozen V5 benchmark | 12.81 | 18.13 | +1.64 | -10.42 |
| Same specification refit on S1 | 14.76 | 19.72 | +5.20 | -14.48 |
| GB with captured quality/context inputs | 12.39 | 17.08 | +1.48 | -15.31 |

**Regeneration improves data consistency; it does not resolve severe-loss bias.**
The enhanced candidate improves aggregate RMSE but worsens retrospective severe
bias. The same-specification refit loses on both. Neither is promoted. Development
contains only 1,933 natural defaulted facilities, fewer than the old 6,000-case
workout training sample. Changes in process, sample size and population mean this
comparison cannot isolate a causal effect of better capture alone. Selection also
showed adverse tail results; no settings were adjusted after seeing them.

PD final population: 14,949 initially non-impaired borrowers, 542 defaults (3.626%).
Frozen logistic AUC .78176, Gini .56352, KS .43350, Brier .031805, log loss .132692;
refitted unchanged logistic AUC .79066, Gini .58133, KS .44139, Brier .031733,
log loss .131508. Mean predictions are 3.939% and 3.468% respectively. No PD promotion.

Full metrics include fixed >60/>75/>90 tails, low loss, predicted bands, product and
collateral segments, EAD-weighted bias and PD calibration. Small segments remain
visible: final >90% loss has only 29 facilities, not 29 independent borrowers.

## Platform verification

**107 tests pass.** The 5,000 current borrowers and 8,695 facilities were ingested
into a fresh migrated SQLite database and scored through the unchanged reference
engine. EAD is 3,594,645,614.15 and ECL is 78,746,507.57 synthetic currency units.
Facility stage counts: 7,802 Stage 1; 859 Stage 2; 34 Stage 3. Independent maximum
EAD error is zero and ECL arithmetic error is 5.82e-11; audit chain verifies.
The final all-population and >75% metrics were independently recalculated from saved
predictions with maximum difference 1.11e-16. Historical V5/R2 hashes still match.
These are reference software checks; PostgreSQL deployment qualification remains
outside this completed dataset release.

## Files and prediction-time contract

- `data/<cohort>/borrowers.csv.gz`: dated financial, qualitative and conduct drivers;
  no future default or LGD target.
- `facilities.csv.gz`: borrower link, exposure, product, collateral allocation,
  guarantee contract and known quality/context fields. IDs unique within release.
- `conduct.csv.gz`: borrower-month observations leading to reporting date.
- `targets.csv.gz`: retrospective PD eligibility/outcome, event date and availability.
- `workouts.csv.gz`: default-facility link, future recoveries/costs, discount rate,
  bounded and unbounded economic loss. Nondefault facilities have no realized LGD.
- `data/current/canonical.json.gz`: accepted by the platform's existing dataset API.
- `data/manifest.json`, `DATA_FREEZE.json`: file/source hashes and independent DQ.
- `results/FINAL_LOCK.json`, `FINAL_OPENED.json`: candidate/data identity and single
  final evaluation marker. Final cohort was not used for model fitting or tuning.
- `results/platform_run.json`: current-cohort execution and independent EAD/ECL checks.

`security_quality` and `guarantor_strength`: fractions 0..1, known synthetic
assessment at `observed_at`, recorded per facility; zero for absent security/support.
They require a real institution's documented valuation/legal and guarantor credit
assessment capture before any deployment. `downturn_at_default` retains the R2
feature name but means **known reporting-date synthetic sector condition** in S1,
held fixed through workout. It is not a forecast of future default conditions.
These extra fields are preserved in the source feature table for research; the
unchanged canonical incumbent engine does not consume them. No fabricated live
institutional capture or automatic challenger propagation is claimed.

## Reproduce

Install `requirements-platform-lock.txt` from repository root, then:

```bash
python -m synthetic_bank.validate
python -m pytest -q
python scripts/run_v5.py
python -m credit_platform.cli build-models
DATABASE_URL=sqlite:///s1-review.db python -m alembic upgrade head
DATABASE_URL=sqlite:///s1-review.db python -m synthetic_bank.run_platform
```

Frozen data and comparison artifacts are included. `python -m synthetic_bank.generate`
creates them only when `synthetic_bank/data` does not exist; it refuses overwrite.
To independently regenerate in a disposable clone, first move the committed data
and results to an evidence directory, then run:

```bash
python -m synthetic_bank.generate
python -m synthetic_bank.validate
python -m synthetic_bank.evaluate selection
python -m synthetic_bank.evaluate final
```

Compare regenerated manifest hashes against preserved originals. Final execution
refuses a second opening in the same results directory. This local control is not
an external sealed evaluation service. Trusted local artifacts only: do not load
untrusted joblib files. The protocol/source are committed before data generation,
and candidates before final evaluation.

## Limitations and release decision

- Synthetic assumptions, no empirical bank calibration or production approval.
- One financial snapshot per disjoint cohort plus monthly conduct; not a complete
  repeated financial-statement/default/cure lifecycle for the same borrowers.
- Financial state and EAD at default are held at reporting-date state. There is no
  independent observed EAD target or validation of future drawdown/CCF accuracy.
- Recovery equations derived from R2; borrower-rate discounting and shared shocks
  are new S1 generator assumptions, not changes to active LGD/ECL methodology.
- Twelve workouts across development/selection have unbounded economic LGD >100%
  due to costs. Both unbounded loss and the bounded model target are retained.
- Borrower-shared outcomes are correlated. Facility counts do not equal independent
  statistical sample sizes; no unsupported significance claim is made.
- Current cohort has no future outcomes: scoring reconciles but does not validate
  current PD/LGD predictive performance.
- Production/bank-use gates remain BLOCKED. S1 models remain research candidates.

The inherited `months_to_resolution` is a recovery timing centre; cashflow buckets
extend through month 60 and `resolved_at` reflects that full observation horizon.
Do not treat the timing centre as the final cash receipt date.
