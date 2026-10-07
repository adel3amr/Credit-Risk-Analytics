# Marginal Interest research (MI-1)

Start with [REPORT.md](REPORT.md), then [PROTOCOL.md](PROTOCOL.md) and [FEATURE_CONTRACTS.md](FEATURE_CONTRACTS.md).

**Conclusion:** no robust incremental value from Marginal Interest demonstrated in this hypothetical experiment. No production promotion. Historical datasets, models and policy remain unchanged.

The repository contains frozen data, dated ledgers, fitted research artifacts, selection lock, final opening record, predictions, grouped uncertainty, support diagnostics, scenario checks and independent ECL arithmetic. All new observations are already impaired; findings cannot be generalized to Stage 1/2 or empirical bank portfolios.

From the repository root, with Python 3.12:

```bash
python -m venv .venv
# Activate .venv using your operating system's command.
python -m pip install -r requirements-platform-lock.txt
python -m pytest -q
python -m marginal_interest.audit
python -m marginal_interest.make_report
```

The full reference suite also needs its established ignored reference artifacts on a clean clone; follow the parent FINAL_RED_TEAM_REPORT.md build commands first. Do not regenerate any frozen research datasets. `generate`, `fit` and `evaluate` deliberately reject overwriting frozen data/models or reopening the final evaluation. Saved predictions permit independent arithmetic without reusing a holdout for tuning.

Only load the committed, verified joblib artifacts from this trusted repository. Binary model loading is not a safe interface for arbitrary uploads.

`pre_outcome_failed_attempt/` preserves failed-generation and damaged-archive evidence. Those files are explicitly not active data. `recovery_verification.json` records the repair proof. No failed attempt is hidden or used for selection.

See RELEASE_TRACK.md for outstanding GitHub/CI/browser items. Research release identity is the final commit containing this README and the completed results; use `git rev-parse HEAD`.
