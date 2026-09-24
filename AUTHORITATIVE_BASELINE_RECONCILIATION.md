# Authoritative baseline reconciliation

Established 24 September 2026 before platform implementation. Baseline is committed `ae9942a`, not the damaged research working tree. No historical dataset or model was modified. Full changed-file list and inventory: `platform_evidence/`.

| Item | Historical claim | Newest evidence | Independently verified | Authoritative value | Source |
|---|---|---|---|---|---|
| Research branch/commit | research/lgd-tail-programme / ae9942a | Same committed head | git log, show, branches | ae9942a | Git history |
| Development line | None | New isolated worktree | git worktree | platform/production-foundation from ae9942a | Git history |
| Frozen V5 | 0dfe4c8, PR25 | PR open, unmerged | GitHub metadata and local ref | 0dfe4c883a8314704394c49fa096dfb45525096c | PR25 |
| Tests | 54 | 54 | pytest rerun: 54 passed | 54 baseline tests | test suite |
| Reconciliation | 30 checks | Full V5 rebuild succeeds | run_v5.py, independent recalculation | 30 release checks; no EWS/stage mismatch | outputs/v5_release_checks.csv |
| Hosted CI | Passing | V5 both successful | GitHub workflow API | runs 35879967200 / 35879966965 success; no research runs returned | platform_evidence/hosted_ci.json |
| Portfolio | 12,000 borrowers | Rebuilt | hash and held-out recalculation | 12,000 generated, 3,000 holdout, 5,172 scored facilities | baseline_hashes.json |
| R2 datasets | 9k/3k/3k/3k | All committed hashes match | SHA-256 | development/selection/final/stress frozen | lgd_research/results/dataset_hashes.csv |
| Working R2 development | Previously clean | Truncated exact prefix | byte comparison with Git blob | 3,933,184 vs 4,211,819 bytes; working hash 80b6eb6f2ff68ae3ad7916f9a04395e12b4fd49320a4b5d5e2732fd2abbff0fa | Original worktree preserved |
| PD | AUC .759455 | Reproduced | rank-based independent metrics | AUC .759455473, Gini .518910946, KS .408496732, Brier .030002535, logloss .128562115 | independent_reconciliation.json |
| V5 LGD | RMSE 16.58 pp | Reproduced | direct residual arithmetic | MAE 11.39645 pp, RMSE 16.57985 pp, bias −.30517 pp | independent_lgd_segments.csv |
| V5 severe tail | −15.59 pp | Reproduced | 327 realized >75% | −15.59278 pp | same |
| EAD | 2,091,914,076.05 | Reproduced | borrower/facility reconciliation | Same; borrower rounding max .01 | independent_reconciliation.json |
| ECL | 45,265,972.05 | Reproduced | independent facility arithmetic | 45,265,972.05000534 | same |
| Stage / watchlist | 2769/221/10; 287 | Reproduced | independent policy comparison | Same; 287 Rating7, distinct from Stage2 | same |
| EWS | No mismatches | Reproduced | source-independent conditions | 0 mismatches | same |
| R1 support experiment | 1618 severe, −14.66 pp | Archived findings | Not refit again at baseline | Historical experiment, not newest R2 cohort | validation_review/PROJECT_WIDE_DECISION.md |
| R2 final | 3,000 holdout | Recalculated common predictions | direct arithmetic | 536 severe; V5 RMSE .176503254, two-stage .156922972 | research_recalculated.json |
| R2 severe bias | −12.74 / −12.05 pp | Recalculated | direct arithmetic | −12.74213 / −12.04825 pp | same |
| Stress | Actual +25.42 pp | Archived paired table | File inspected; not regenerated at baseline | two-stage +12.5441 pp response; future-only shocks unavailable | stress_responses.csv |
| Figures/artifacts | 18 plots | 18 plots and three research artifacts | inventory/hash inspection | Research only; no promotion | lgd_research/ |
| Production gate | BLOCKED | Still justified | absent live research features and institutional evidence | BLOCKED | research_gate.py, findings F1–F9 |

## Evidence interpretation

The original and R2 metrics refer to different synthetic populations. R2 is not empirical bank evidence. Outcome-selected tail bias is retrospective and must be accompanied by forecast-selected cohort diagnostics. The final selection lock is archived, but this is not externally timestamped preregistration. A source commit and passing tests cannot certify a model. Local working-file truncation is a new integrity finding, not evidence for changing any generator. The intact committed snapshot is the reproducible baseline.
