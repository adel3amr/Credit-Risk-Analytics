# Synthetic bank S1 — frozen generation and evaluation protocol

Version S1. New DATA / DATA ARCHITECTURE; no incumbent risk methodology change.
Historical V5/R2 sources, data and predictions remain untouched. This protocol is
written before S1 generation, training or examination of model metrics.

## Observed problem and hypothesis

Original workouts and current facilities use different guarantee support and lack
shared borrower lineage. Security/guarantor quality exists only in research.
Hypothesis: one facility/security contract and one recovery process across cohorts
will remove the artificial support discontinuity, without guaranteeing accuracy.

## Design fixed before results

Four disjoint borrower cohorts: development 30,000 (2005-01-01, seed 31001),
selection 15,000 (2012-01-01, seed 31002), final 15,000 (2019-01-01, seed 31003),
current 5,000 (2026-01-01, seed 31004). Dates are illustrative synthetic vintages,
NOT reconstructions of actual economic history. Default observation window is
12 months; workout cash flows extend 60 months after default. Seven-year vintage
spacing keeps earlier outcomes available before later-cohort observation dates.
Borrowers and facilities never cross splits. Final results may be evaluated once
only after data freeze and development/selection comparison. No reseeding, sample
expansion, parameter tuning or postfinal recalibration based on performance.

Reuse the frozen borrower/financial/36-month conduct/default process in an isolated
temporary directory with new seeds. Its 3.5% target rate and all coefficients are
inherited assumptions, not institutional estimates. Exclude currently impaired
borrowers from the prospective PD target; record their existing default separately.
Drop legacy generated LGD/proxy outputs from S1: workouts are produced only for
actual synthetic default events, linked to the same facilities used for scoring.
Exposure and financial state at default is held at reporting-date state: explicit
simplification, no invented actual CCF validation. Nondefault facilities have no
realized LGD. Current cohort carries no future targets or recoveries.

Borrower collateral value is allocated in proportion to facility EAD (no duplicate
pledge). Guarantee support is an independently captured third-party protection
contract, not inferred from a bank-issued trade product: probability .20 for all
products, coverage drawn from [.15,.35,.55,.8,1]. Thus approximately 80% zero support
is generated consistently across cohorts, not forced to an exact observed share.
Quality fields use inherited R2 Beta(4,2) security and Beta(3,2) guarantor processes;
all cohorts contain dated records. The downturn variable is a synthetic current
borrower-sector condition, not a known future default environment. No forecast of
future macro conditions is claimed. It is fixed through workout in this version.

Ordinary R2 recovery equations retained as S1 assumptions: collateral, guarantee,
residual collection, cure, timing, costs and discounting. Borrower-level cure and
future recovery shocks are shared across that borrower's facilities; security/lien
and EAD remain facility-specific. Shared risk causes correlated facility outcomes.
Borrower interest rate is the discount rate, recorded before outcome; cash flows
and cost dates are explicit. No forced severe/cure frequencies or target LGDs.
Unbounded economic loss is retained alongside bounded model target; values >100%
are disclosed, not silently discarded. Support at zero/full guarantee comes from
the declared source process. Separate edge tests cover zero exposure.

## Validation and experiments

Before fitting: canonical schema validation, unique/FK IDs, dates, borrower split
separation, security allocation, guarantee range, target availability, cash-flow
PV independent recalculation, recovery exposure caps, deterministic reproduction,
and freeze of file/source hashes. Report loss coverage without targeting quotas.

Models: frozen incumbent GB; unchanged GB specification refit on S1 default cases;
existing R2 enhanced GB specification refit with three captured quality/context
fields. No hyperparameter search or two-stage re-tuning. PD: frozen logistic and
same specification refit on development at-risk borrowers only. Report selection
first; lock candidate artifacts before opening final metrics. Keep every candidate
regardless of rank. MAE/RMSE/bias, fixed tail thresholds .60/.75/.90, predicted bands,
collateral/product segments, PD AUC/Gini/KS/Brier/logloss/calibration; all denominators.
Current canonical data runs through the unchanged reference platform, reconciles
facility ECL independently, and discloses support/feature limitations.

## Evidence and limits

EBA/GL/2017/16 (20 November 2017), primary IRB guidance:
https://www.eba.europa.eu/sites/default/files/documents/10180/2033363/6b062012-45d6-4655-af04-801d26493ed0/Guidelines%20on%20PD%20and%20LGD%20estimation%20%28EBA-GL-2017-16%29.pdf
Referenced for data representativeness and explicit economic recovery/cost records,
not as IFRS9 policy or a source of synthetic coefficients. Existing project methods
remain unchanged. Synthetic capture is not proof of institutional feature availability.
A new dataset cannot confer bank-use approval. All candidates remain RESEARCH.
