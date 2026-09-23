# V2 Methodology Checkpoint — 2026-09-21

> **Historical checkpoint — superseded by the reviewed current methodology in README.md and FINAL_PROJECT_RELEASE_2026-09-22.md. Values and implementation details below are retained only as development history and must not be treated as the current release.**

This checkpoint freezes the methodology before the final governance/data audit. It is not a production IFRS 9 implementation.

## Frozen architecture
- 12,000 synthetic SME borrowers.
- 36 months of monthly behavioural history (432,000 borrower-month observations).
- Core PD: financial fundamentals + current observed behaviour.
- Logistic Regression is the intended primary/interpretable PD model; RF and GB are challengers.
- Behavioural trajectory is an EWS/monitoring layer, not forced into core PD.
- Qualitative variables are supplementary review inputs.
- Loans / OVD / trade drive exposure architecture and EAD.
- Aggregate collateral/recovery assumptions drive LGD.
- Stage 3: current credit-impaired flag or DPD >= 90.
- Stage 2: simplified SICR proxy using DPD/conduct/history triggers plus the fixed internal 9-month EWS persistence rule.
- The 9-month threshold is an internal synthetic policy assumption, not an IFRS 9 requirement and will not be tuned on the holdout.

## Locked validation result
Workflow 35612855093 passed at checkpoint.

Holdout (3,000):
- Stage 1: 2,772; observed future default 3.0%.
- Stage 2: 220; observed future default 12.7%.
- Stage 3: 8; observed future default 0.0% (too few observations for inference).
- Mean predicted PD: 3.64%; observed holdout DR: 3.67%.
- Staged ECL: EUR 30.354m.

Fixed 9-month EWS validation:
- Ordinary Stage 1: 2,640; DR 2.54%.
- EWS deteriorating <9m only: 132; DR 11.36%.
- 9m EWS persistence only: 136; DR 13.97%.
- 9m EWS + other Stage 2 trigger: 14; DR 21.43%.
- Other Stage 2 trigger only: 70; DR 8.57%.

PD information-set result:
- Financial only AUC 0.7493.
- Financial + current behaviour AUC 0.7751.
- + trajectory AUC 0.7743.
- Full hybrid AUC 0.7731.
- Paired bootstrap current behaviour - financial: +0.0260, 95% CI [+0.0026,+0.0516].
- Trajectory - current behaviour: -0.0007, CI crosses zero.
- Qualitative - trajectory: -0.0012, CI crosses zero.

## Interpretation frozen at checkpoint
The 9-month persistence rule identifies incremental risk, but <9m EWS cases are already materially risky. We retain 9 months because it was specified ex ante; we do not optimize the threshold on this holdout. Current behaviour belongs in core PD; trajectory is retained as monitoring/EWS because it does not add robust incremental PD discrimination.

## Remaining audit
1. Verify exact governed PD feature set and collateral_coverage availability.
2. Hard-lock Logistic Regression as primary rather than dynamic best-AUC selection.
3. Audit stage/ECL semantics and leakage.
4. Audit product/EAD/LGD assumptions.
5. Update stale README/docs.
6. Build borrower-level raw -> features -> PD -> score -> EWS -> stage -> EAD/LGD -> ECL trace.
7. Manual data review before PR merge.
