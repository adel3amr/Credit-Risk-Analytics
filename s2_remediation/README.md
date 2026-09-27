# Focused S2-R1 remediation

This directory preserves one constrained successor, its frozen data and its
promotion assessment. It does not replace V5 or the original S2 in place.
Read `PROTOCOL.md` for the predeclared tolerances, economic assumptions and split
design. Read `DECISION.md` for the final disposition. Machine-readable evidence
is in `results/decision.json`, with individual acceptance checks in
`results/gate_checks.json` and registered artifact/data hashes in
`results/registry.json`.

## Run and verify

From the repository root, in the Python environment installed using
`requirements-platform-lock.txt`:

```bash
python -c "from s2_remediation.evaluate import verify, verify_lock; verify(); verify_lock()"
python -m pytest -q
python -m s2_remediation.review
```

`review` independently recalculates aggregate metrics from saved predictions and
applies the frozen numerical gates. It does not fit, calibrate or reopen the
promotion sample. It will not presume engineering success without the recorded
full-suite signoff. Historical S2 evidence remains in `economic_lgd/results`.

The existing authenticated `/api/v1/lgd-economic-validation` view and model-risk
Copilot retrieve the newest completed decision, including unresolved findings.
The historical incumbent continues to drive existing reference calculation runs
unless an explicit governed release passes all gates. No bank-use approval is
implied by a synthetic-reference promotion.

## Reproduce the new data without overwriting evidence

```bash
python -m s2_remediation.generate --destination /tmp/s2-r1-reproduction
```

The destination must not exist. Compare the nine generated `.csv.gz` file hashes
with `data/manifest.json`. A manifest generated later can contain additional
source-file provenance; compare data hashes individually rather than assuming
identical manifest inventories. No held-out outcomes enter fitting.

To independently rebuild the entire experiment, use a separate copy/check-out,
move its `s2_remediation/data` and `s2_remediation/results` to archival locations,
then run, in order:

```bash
python -m s2_remediation.generate
python -m s2_remediation.evaluate develop
# Inspect and preserve LOCK.json before the next command.
python -m s2_remediation.evaluate final
python -m pytest -q
python -m s2_remediation.review
```

Do not remove `FINAL_OPENED.json` and tune against its population. A reviewer’s
reproduction is not a new model-selection exercise. The original committed
engineering signoff is evidence of its own run, not an assertion that a new
environment passed; preserve it outside the reproduction output directory.

## Evidence interpretation

* `*_metrics.csv`: prediction minus realization and prediction minus conditional
  mean are separate columns. Units are fractions; multiply by 100 for pp.
* `*_predictions.csv`: three-model predictions, realized outcomes and independent
  simulator conditional means; identities and scenario are included.
* `*_support.csv`: marginal exceptions, local neighbor counts, economic cluster
  counts and distance to the twentieth nearest development recovery.
* `*_shape.json`: violations on each cohort for each model; no post-score sorting.
* `scenario_ecl.csv`: original governed, scenario-ordered incumbent, original S2
  and remediated S2 results on identical facilities; shadow evidence only unless
  an explicitly qualified release is made.
* `rejected_generation`: a pre-fit cycle-coverage bug and its preserved evidence.

The support object is outcome-free. `Support.require()` rejects unsupported
inputs; `runtime.score()` additionally requires a promoted reference registry.
Raw predictor calls inside evaluation are diagnostic only and do not waive the
operational boundary. No new macro feed or prediction-time security/guarantor
quality was invented. Synthetic history cannot substitute for institutional data.
