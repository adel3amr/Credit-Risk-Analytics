# Reproduce post-R1 hardening

Read `DECISION.md` first: the calibration was rejected, R1 retained, and no new
final holdout was opened. Existing numerical results remain historical evidence.

From the repository root, install the pinned environment as described in
`REPRODUCIBILITY.md`, then:

```bash
python -m pytest -q
python -c "from s2_remediation.evaluate import verify, verify_lock; verify(); verify_lock()"
python -m lgd_hardening.decision
```

To independently reproduce diagnostics in a separate checkout, archive its
`lgd_hardening/results` directory, recreate that empty directory, and run:

```bash
python -m lgd_hardening.audit
python -m lgd_hardening.calibration
python -m lgd_hardening.engineering
python -m lgd_hardening.decision
python -m pytest -q
```

The calibration command rejects overwriting its candidate. It fits only the
frozen matured calibration file; current and retired promotion data are known
engineering evaluations. These commands do not make them independent again.

`ECONOMIC_DOMAIN_CONTRACT.json` is the common mechanical/support boundary.
`capture.RecoveryEvidence` validates evidence records; it does not derive a model
feature or certify a legal opinion. No validated recovery-feature derivation has
been registered. `runtime.score` requires genuine promotion and support, and
therefore blocks the current candidate. The incumbent platform remains unchanged.

Evidence units: metrics CSV values are fractions unless a column explicitly
ends in `_pp`. `band_diagnosis.csv` separates expected error from realization
noise. `precision_planning.csv` counts independent economic clusters, not
facilities. `quality_sensitivity.csv` is non-deployable development diagnostics.
`facility_traces.json` includes provenance and labelled model sensitivities.
